#!/usr/bin/env python3
"""Build a local, greppable corpus of papers from the fm4sd reading index.

The upstream repo (borawhocodess/fm4sd) is a README of links, nothing more --
its papers/ directory is gitignored, so there is nothing there to vendor. This
script reconstructs a local corpus from the same index by resolving each link.

For every entry it prefers the arXiv LaTeX source bundle (/src/<id>) over the
PDF, because the .tex files are plain text with section structure intact, which
is what makes the corpus greppable and cheap for a model to read. It falls back
to the PDF only when no source bundle exists.

Entries with no arXiv id are resolved through the route families below -- direct
PDF, publisher PDF, PMLR proceedings, NeurIPS proceedings and web-native HTML --
or stamped with the reason they are absent. No scraping, credentials, JavaScript
or CAPTCHA solving, ever: a route either answers a plain HTTP GET or it does not
go in the corpus. Web routes run at ~1 req/s, well below anything a publisher
could read as load, with the project User-Agent.

Nothing here is committed except references/manifest.json. Raw bundles, .tex and
extracted text all live under papers/, which is gitignored -- several papers in
the index are arXiv non-exclusive-distrib or CC-BY-NC-SA, so redistributing the
payload would be a licensing problem. See PROVENANCE.md.

Usage:
    python3 scripts/fm4sd_fetch.py --index          # parse README -> manifest
    python3 scripts/fm4sd_fetch.py --fetch          # fetch + extract, all missing
    python3 scripts/fm4sd_fetch.py --fetch --only nanotabpfn tabpfnv2 wikidbs
    python3 scripts/fm4sd_fetch.py --status         # what is on disk, and why not
    python3 scripts/fm4sd_fetch.py --check-revisions  # pins that have moved upstream
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import hashlib
import json
import os
import re
import shutil
import socket
import sys
import tarfile
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
PAPERS = REPO / "papers"
REFERENCES = REPO / "references"
MANIFEST = REFERENCES / "manifest.json"

INDEX_URL = "https://raw.githubusercontent.com/borawhocodess/fm4sd/main/README.md"
# Version resolution (#33). `id_list=<unversioned id>` returns the paper's current
# revision in the Atom entry's <id>: `.../abs/2102.10154v3`. The version is read
# off that response, never constructed.
ARXIV_API = "https://export.arxiv.org/api/query?id_list="
# Ids per export-API query. The API accepts a comma-separated `id_list`; batches
# of 50 keep each URL modest and the whole corpus to ~7 calls.
ARXIV_API_BATCH = 50
USER_AGENT = "fm4sd-corpus/1.0 (research; https://github.com/IFoA-ADSWP/fm4sd)"

# Politeness: arXiv asks that automated clients stay light. 3 req/s across a
# small pool is far below anything that would look like abuse.
REQS_PER_SECOND = 3.0
TIMEOUT = 60
DEBUG = bool(os.environ.get("FM4SD_DEBUG"))
KEEP_SRC = bool(os.environ.get("FM4SD_KEEP_SRC"))

# "A paper's worth of text", in bytes. Below this a LaTeX bundle is a wrapper with
# no body and a web page is a landing page rather than the paper, so the fetch
# falls through to the next route. One name for both guards (#38).
MIN_TEXT_BYTES = 4000

# The two statuses that mean the payload is on disk: `ok` (fetched in that run)
# and `cached` (already there and not re-fetched). Every figure about fetched
# entries counts these two.
FETCHED_STATUSES = ("ok", "cached")

# The URL a licence claim was read from, under the two names the manifest carries.
# `licence_url` is written by fm4sd_licences.py for the 253 arXiv rows;
# `licence_source` is written by the route records here for the 18 id-less rows.
# They name one fact and are kept as two keys because renaming either would change
# the committed manifest -- byte-identical output is the reproducibility contract
# (#38). This tuple is the single statement of that mapping; the gate imports it
# and PROVENANCE.md cites it.
LICENCE_URL_FIELDS = ("licence_url", "licence_source")

# Every repo file `--index` reads, relative to the repo root: (path, required).
# README.md is the index itself; references/manifest.json is the prior record it
# carries fetch metadata, licence rows and pinned revisions forward from -- an
# input, not just an output -- and is absent on a fresh clone, which is normal.
# The reproducibility gate copies these into its scratch tree and fails loudly if
# a declared input is missing there (#38).
INDEX_INPUTS: tuple[tuple[str, bool], ...] = (
    ("README.md", True),
    ("references/manifest.json", False),
)


# Entry shape in the README, e.g.
#   - tabpfn — [arxiv](https://arxiv.org/abs/2207.01848) · [iclr](...) — \[hollmann et al. 2023\]
ENTRY_RE = re.compile(r"^\s*-\s+(?P<slug>[^\n—]+?)\s+—\s+(?P<rest>.*)$")
# One id fragment shared by the three arXiv URL patterns, so they cannot drift:
#   modern (post-2007):  2207.01848          \d{4}.\d{4,5}
#   legacy (pre-2007):   cond-mat/0011094    archive[/subclass]/yymmnnn
# The legacy subclass is case-preserving because arXiv ids are case-sensitive on
# the page (`math.GT/0309136`), though the site tolerates any case in URLs.
ARXIV_ID = r"\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Za-z][A-Za-z-]*)?/\d{7}"
ARXIV_RE = re.compile(rf"https?://arxiv\.org/(?:abs|pdf)/(?P<id>{ARXIV_ID})")
ARXIV_PDF_RE = re.compile(rf"https?://arxiv\.org/pdf/(?P<id>{ARXIV_ID})")
ARXIV_ABS_RE = re.compile(rf"https?://arxiv\.org/abs/(?P<id>{ARXIV_ID})")

# ---------------------------------------------------------------------------
# Non-arXiv routes (#29, decision on #9)
#
# Five families, all plain HTTP GETs, no credentials, no JS, no CAPTCHA solving:
#   direct-pdf     the index already carries a `pdf` link
#   publisher-pdf  Nature/PMC/Springer landing -> the same article's PDF
#   pmlr           proceedings.mlr.press landing -> the paper PDF beside it
#   neurips        proceedings.neurips.cc link is already a PDF
#   web-native     a server-rendered HTML paper (blog/site link), no PDF exists
#
# Attribution, not guesswork: the population and every reason below come from the
# audit in research/no-arxiv-payload.md (branch research/no-arxiv-payload, probes
# 2026-10-29) refreshed for the post-merge index in the #29 triage comment
# (2026-10-30). Re-probing the 35 unreachable rows on every run would hammer
# publishers to learn something already recorded; a row whose route comes back to
# life is a one-line move from an absence reason to a link the index already carries.
# ---------------------------------------------------------------------------

# Web routes are slower than arXiv's: one request per second per host.
POLITE_REQS_PER_SECOND = 1.0


ABSENCE_REASONS = frozenset({"not-paper", "captcha", "paywall", "dead", "unknown"})
SHAREABLE_VALUES = frozenset({"yes", "no", "unknown"})


@dataclass(frozen=True)
class RouteSpec:
    """Everything the static audit knows about one id-less entry.

    These facts used to be five slug-keyed tables -- `NON_PAPER`, `UNREACHABLE`,
    `HTML_PAPERS`, `PUBLISHER_PDFS`, `LICENCE_RECORDS` -- so adding a row meant
    patching five literals, and `PUBLISHER_PDFS` existed only because "this PDF
    comes from a publisher" had nowhere else to live. One spec per slug keeps an
    entry's facts together (#38).
    """

    note: str = ""            # what the link is, or which route answered and how
    absence: str = ""         # "" when a route exists; else not-paper|captcha|paywall|dead|unknown
    html_key: str = ""        # link key holding a web-native HTML paper
    publisher: bool = False   # PDF comes from a publisher/mirror, not the author
    licence: str = ""         # what the source declares
    licence_source: str = ""  # URL the licence claim was read from
    shareable: str = ""       # "yes" | "no" | "unknown"; unknown is never permission

    def __post_init__(self) -> None:
        # GLOSSARY.md fixes both vocabularies; a typo would otherwise mint a
        # status or a permission value the docs do not define.
        if self.absence and self.absence not in ABSENCE_REASONS:
            raise ValueError(f"unknown absence reason: {self.absence!r}")
        if self.shareable and self.shareable not in SHAREABLE_VALUES:
            raise ValueError(f"unknown shareable value: {self.shareable!r}")

    @property
    def status(self) -> str:
        """The `fetch_status` of a row with no payload ("" when a route exists)."""
        if not self.absence:
            return ""
        if self.absence == "not-paper":
            return "skipped:not-paper"
        return f"skipped:unreachable:{self.absence}"

    @property
    def licence_record(self) -> dict[str, str]:
        """The manifest keys for this entry's licence, in the manifest's order."""
        if not self.licence:
            return {}
        return {
            "licence": self.licence,
            "licence_source": self.licence_source,
            "shareable": self.shareable,
        }


# One entry per slug: whether a paper exists behind the link, the reason when no
# plain-HTTP route reaches it, whether its payload is a server-rendered page,
# whether its PDF comes from a publisher, and its licence record (#38).
ROUTES: dict[str, RouteSpec] = {
    # --- not a paper: repo, blog, model card or issue -----------------------
    "aplr": RouteSpec("GitHub repo only -- no paper", absence="not-paper"),
    "kumo-tabular": RouteSpec("Hugging Face blog + repo, no paper", absence="not-paper"),
    "timesfm-3": RouteSpec("Google Research blog, no paper", absence="not-paper"),
    "limix2-contamination": RouteSpec("GitHub issue, no paper", absence="not-paper"),
    "tabpfn-rel": RouteSpec("GitHub repo, no paper", absence="not-paper"),
    "tabiclr": RouteSpec("GitHub repo, no paper", absence="not-paper"),
    "turkforecast": RouteSpec("GitHub model card, no paper", absence="not-paper"),

    # --- unreachable: the reason the manifest records, and the route that
    # answered. OpenReview's browser-verification challenge, on forum, PDF and
    # api2 alike.
    "principled-datagen": RouteSpec("openreview forum; challenge", absence="captcha"),
    "zeroshot-coordination-llm-agents": RouteSpec("openreview forum; challenge",
                                                 absence="captcha"),
    "strong-posttraining-pretraining": RouteSpec("openreview forum; challenge",
                                                 absence="captcha"),
    "ensemble-inference": RouteSpec("openreview forum; challenge", absence="captcha"),
    "shapinggeometry": RouteSpec("openreview forum; challenge", absence="captcha"),
    "goggle": RouteSpec("openreview forum; challenge", absence="captcha"),
    "rna-topology-encoding": RouteSpec("openreview pdf; challenge", absence="captcha"),
    "rules-or-exemplars": RouteSpec("openreview forum; challenge", absence="captcha"),
    "tscausalfm": RouteSpec("openreview forum; challenge", absence="captcha"),
    "causalfewshot": RouteSpec("openreview forum; challenge", absence="captcha"),
    "causalorder": RouteSpec("openreview forum; challenge", absence="captcha"),
    "causaltab": RouteSpec("openreview forum; challenge", absence="captcha"),
    "posttreatmentcfm": RouteSpec("openreview forum; challenge", absence="captcha"),
    "agata": RouteSpec("LG landing has no payload; openreview challenged",
                       absence="captcha"),
    "bsplinenorm": RouteSpec("LG landing has no payload; openreview challenged",
                             absence="captcha"),
    # Cloudflare "Just a moment" on the publisher's own page.
    "ggpl": RouteSpec("dl.acm.org; cloudflare challenge", absence="captcha"),
    "zerorel": RouteSpec("dl.acm.org; cloudflare challenge", absence="captcha"),
    "stablepfn": RouteSpec("dl.acm.org; cloudflare challenge", absence="captcha"),
    "tfm-systematic-survey": RouteSpec("ssrn; cloudflare challenge", absence="captcha"),
    "twostagefinance": RouteSpec("ssrn; cloudflare challenge", absence="captcha"),
    "icl-order": RouteSpec("researchgate; cookie/JS challenge", absence="captcha"),
    # Subscription full text withheld; metadata says closed.
    "sdi": RouteSpec("elsevier/sciencedirect; 403, crossref+openalex closed",
                     absence="paywall"),
    "kamel": RouteSpec("elsevier/sciencedirect; 403, crossref+openalex closed",
                       absence="paywall"),
    "qdhgan": RouteSpec("elsevier/sciencedirect; 403, openalex closed",
                        absence="paywall"),
    "tabllama": RouteSpec("elsevier/sciencedirect; 403, openalex closed",
                          absence="paywall"),
    "mmda": RouteSpec("ieee xplore; stamp.jsp redirects to abstract", absence="paywall"),
    "exo-zeroshot-tsfm": RouteSpec("ieee xplore; stamp.jsp redirects to abstract",
                                   absence="paywall"),
    "augtab": RouteSpec("springer chapter; content/pdf redirects to landing",
                        absence="paywall"),
    # The canonical non-life actuarial methodology (#47). Journal-only, pre-arXiv or
    # with no preprint: the DOI resolves, the full text is a subscription. Recorded
    # rather than probed on every run, as the audit rows above are.
    "distribution-free-calculation-of-the-standard-error-of-chain-ladder-reserve":
        RouteSpec("cambridge core / astin bulletin; subscription", absence="paywall"),
    "stochastic-claims-reserving-in-general-insurance":
        RouteSpec("cambridge core / british actuarial journal; subscription",
                  absence="paywall"),
    "actuarial-applications-of-a-hierarchical-insurance-claims-model":
        RouteSpec("cambridge core / astin bulletin; subscription", absence="paywall"),
    "fitting-tweedies-compound-poisson-model-to-insurance-claims-data":
        RouteSpec("taylor & francis; subscription", absence="paywall"),
    "zero-inflated-poisson-regression-with-an-application-to-defects":
        RouteSpec("jstor; subscription", absence="paywall"),
    "specification-and-testing-of-some-modified-count-data-models":
        RouteSpec("elsevier / sciencedirect; subscription", absence="paywall"),
    # Dead: a 404, a DNS failure, or a stub redirect to something else.
    "kumorfm": RouteSpec("pdf stub redirects to nvidia product docs; no second id",
                          absence="dead"),
    "timestral": RouteSpec("site redirects to an unrelated page (seedvr2.net)",
                           absence="dead"),
    # Could not decide: bot defence with no observable paywall, or landing only.
    "rt-j": RouteSpec("project page 200, no PDF link; openreview challenged",
                      absence="unknown"),
    "ratab": RouteSpec("LG landing 200, abstract only, no payload", absence="unknown"),
    "orchecause": RouteSpec("LG landing 200, abstract only, no payload",
                            absence="unknown"),
    "cwfm": RouteSpec("mdpi 403 access denied; crossref/openalex say gold OA",
                      absence="unknown"),
    "bitcoinllmforecast": RouteSpec(
        "sciencedirect 403 bot defence; openalex says hybrid OA", absence="unknown"),
    "machine-learning-in-p-and-c-insurance-a-review-for-pricing-and-reserving":
        RouteSpec("mdpi 403 access denied; open access per the publisher, no payload",
                  absence="unknown"),

    # --- publisher PDF ------------------------------------------------------
    # Licence and sharing record for each route entry (decision on #9: "unknown is
    # never permission"). Seeded from the audit table in research/no-arxiv-payload.md
    # and confirmed against the fetched payload; `licence_source` is the URL the
    # claim was read from -- for "none stated" that is the document itself, which is
    # evidence of absence, not permission. `shareable` is "yes" only for an explicit
    # permissive grant: today tabpfnv2, tabssldataselect and schemapile (CC BY 4.0).
    "tabpfnv2": RouteSpec(
        note="Nature article -> PMC PDF -> Europe PMC full-text XML fallback",
        publisher=True,
        licence="CC BY 4.0",
        licence_source="https://www.nature.com/articles/s41586-024-08328-6",
        shareable="yes"),
    "tabssldataselect": RouteSpec(
        note="Springer article -> content/pdf",
        publisher=True,
        licence="CC BY 4.0",
        licence_source="https://link.springer.com/article/10.1007/s10994-026-07133-8",
        shareable="yes"),
    "schemapile": RouteSpec(
        note="CWI/ACM article PDF",
        publisher=True,
        licence="CC BY 4.0",
        licence_source="https://ir.cwi.nl/pub/34763/34763.pdf",
        shareable="yes"),

    # --- direct PDF ---------------------------------------------------------
    "tfm-agents-humans": RouteSpec(
        licence="none stated",
        licence_source="https://ir.cwi.nl/pub/36086/36086.pdf",
        shareable="unknown"),
    "era-of-experience": RouteSpec(
        licence="none stated",
        licence_source="https://storage.googleapis.com/deepmind-media/Era-of-Experience%20/The%20Era%20of%20Experience%20Paper.pdf",
        shareable="unknown"),
    "pfnsyn": RouteSpec(
        licence="CC BY-NC-ND 4.0",
        licence_source="https://tabular-data-analysis.github.io/tada2026/papers/TaDA26_16.pdf",
        shareable="no"),
    "good-bad-controls": RouteSpec(
        licence="none stated",
        licence_source="https://ftp.cs.ucla.edu/pub/stat_ser/r493.pdf",
        shareable="unknown"),
    "cdc-prompt": RouteSpec(
        licence="none stated",
        licence_source="https://cdn.openai.com/pdf/04d1d1e4-bc75-476a-97cf-49055cd98d31/cdc_prompt.pdf",
        shareable="unknown"),
    "mit-ai-report": RouteSpec(
        licence="© MIT, no reuse grant",
        licence_source="https://bpb-us-e1.wpmucdn.com/sites.mit.edu/dist/d/2418/files/2026/09/AI-Committee-Final-Report-Aug-13.pdf",
        shareable="no"),
    "dfs": RouteSpec(
        licence="unknown",
        licence_source="https://groups.csail.mit.edu/EVO-DesignOpt/groupWebSite/uploads/Site/DSAA_DSM_2015.pdf",
        shareable="unknown"),
    "quantile-regression-forests": RouteSpec(
        note="JMLR article PDF; no arXiv preprint (#47)",
        licence="none stated",
        licence_source="https://www.jmlr.org/papers/volume7/meinshausen06a/meinshausen06a.pdf",
        shareable="unknown"),
    "the-actuary-and-ibnr": RouteSpec(
        note="CAS proceedings scan, PCAS LIX (1972); no DOI exists (#47)",
        licence="none stated",
        licence_source="https://www.casact.org/sites/default/files/database/proceed_proceed72_72181.pdf",
        shareable="unknown"),

    # --- PMLR (copyright line, no reuse licence) ---------------------------
    "ptnas": RouteSpec(
        licence="PMLR copyright, no reuse licence",
        licence_source="https://proceedings.mlr.press/v306/xing26a.html",
        shareable="no"),
    "baguan-ts": RouteSpec(
        licence="PMLR copyright, no reuse licence",
        licence_source="https://proceedings.mlr.press/v306/yang26ac.html",
        shareable="no"),
    "pf-ges": RouteSpec(
        licence="PMLR copyright, no reuse licence",
        licence_source="https://proceedings.mlr.press/v323/gajewski26a.html",
        shareable="no"),

    # --- NeurIPS proceedings ----------------------------------------------
    "wikidbs": RouteSpec(
        licence="unknown -- CC BY 4.0 stated for the dataset and code, not the paper",
        licence_source="https://proceedings.neurips.cc/paper_files/paper/2024/file/4847447cae911dde321ca19afe7d8707-Paper-Datasets_and_Benchmarks_Track.pdf",
        shareable="unknown"),
    "lightgbm": RouteSpec(
        note="NeurIPS 2017 proceedings PDF; no arXiv preprint exists (#47)",
        licence="none stated",
        licence_source="https://proceedings.neurips.cc/paper_files/paper/2017/file/6449f44a102fde848669bdd9eb6b76fa-Paper.pdf",
        shareable="unknown"),

    # --- web-native HTML: `html_key` is the link key holding the paper's own
    # URL. These pages are server-rendered full papers, not abstracts: a landing
    # page without the paper fails the length guard in extract_text_from_html()
    # and is recorded as unreachable instead.
    "circuits-framework": RouteSpec(
        html_key="blog",
        licence="none stated",
        licence_source="https://transformer-circuits.pub/2021/framework/index.html",
        shareable="unknown"),
    "monosemanticity": RouteSpec(
        html_key="blog",
        licence="none stated",
        licence_source="https://transformer-circuits.pub/2023/monosemantic-features/index.html",
        shareable="unknown"),
    "nonergodic-geometry": RouteSpec(
        html_key="site",
        licence="none stated",
        licence_source="https://simplex.pub/nonergodic-geometry/",
        shareable="unknown"),
    "dust": RouteSpec(
        html_key="site",
        licence="unknown",
        licence_source="https://qlabs.sh/research/dust",
        shareable="unknown"),
}


def route_spec(slug: str) -> RouteSpec | None:
    """The static audit record for one slug, or None when the index links a paper."""
    return ROUTES.get(slug)


def recorded_absence(slug: str) -> str:
    """The reason a row has no payload before any fetch, or "" if a route exists.

    The one vocabulary `absence_status()`, `route_candidates()` and `fetch_route()`
    share: a row is either not a paper, unreachable for a named reason, or has a
    route to try.
    """
    spec = route_spec(slug)
    return spec.status if spec else ""


def licence_record(slug: str) -> dict[str, str]:
    """The licence/shareable record for one route entry ({} when it has none)."""
    spec = route_spec(slug)
    return spec.licence_record if spec else {}


@dataclass(frozen=True)
class Route:
    """One way to obtain an entry's payload: a URL and how to read the bytes."""

    kind: str   # "pdf" | "html" | "xml"
    url: str
    family: str  # direct-pdf | publisher-pdf | pmlr | neurips | web-native


def pmc_pdf(pmc_url: str) -> str:
    """PMC landing (`/pmc/articles/PMC11711098/`) -> the article's PDF endpoint."""
    m = re.search(r"(PMC\d+)", pmc_url)
    return (f"https://pmc.ncbi.nlm.nih.gov/articles/{m.group(1)}/pdf/"
            if m else pmc_url)


def nature_pdf(article_url: str) -> str:
    """Nature article page -> the same article's PDF (`.pdf` on the path)."""
    return article_url.rstrip("/") + ".pdf"


def springer_pdf(landing: str) -> str:
    """Springer article/chapter page -> `/content/pdf/<doi>.pdf`.

    The chapter form still redirects to the landing page when access is not
    granted, so a gated chapter fails rather than storing HTML as a PDF.
    """
    m = re.search(r"/(?:article|chapter)/(10\.\d{4,9}/[^/?#]+)", landing)
    return (f"https://link.springer.com/content/pdf/{m.group(1)}.pdf"
            if m else landing)


def pmlr_pdf(landing: str) -> str:
    """PMLR landing (`/v306/xing26a.html`) -> the paper PDF it links to.

    PMLR's own `/v306/xing26a/xing26a.pdf` path 404s; the landing page points at
    the proceedings repo's built asset, which is the canonical PDF:
    `raw.githubusercontent.com/mlresearch/<vol>/main/assets/<paper>/<paper>.pdf`.
    """
    m = re.match(r"https?://proceedings\.mlr\.press/(v\d+)/([A-Za-z0-9]+)\.html$", landing)
    return (f"https://raw.githubusercontent.com/mlresearch/{m.group(1)}/main/assets/"
            f"{m.group(2)}/{m.group(2)}.pdf" if m else landing)


def europepmc_xml(pmc_url: str) -> str:
    """PMC id -> Europe PMC's full-text JATS XML for the same article.

    Last-resort fallback for a PMC-mirrored paper whose PDF endpoints are behind
    a browser challenge (Nature and PMC both were on 2026-10-31). This is the
    article's full text, not an abstract page, and it needs no credentials.
    """
    m = re.search(r"(PMC\d+)", pmc_url)
    return (f"https://www.ebi.ac.uk/europepmc/webservices/rest/{m.group(1)}/fullTextXML"
            if m else "")


def route_candidates(paper: Paper) -> list[Route]:
    """The ordered routes for one id-less entry, derived from its index links.

    Empty for anything already handled by the arXiv path, for repo/blog rows,
    and for rows the audit established as unreachable -- those carry a reason
    instead, so we do not hit a publisher to relearn a 403.
    """
    if paper.arxiv_id or recorded_absence(paper.slug):
        return []

    slug, links = paper.slug, paper.links
    spec = route_spec(slug)
    routes: list[Route] = []

    if spec and spec.html_key:
        if spec.html_key in links:
            routes.append(Route("html", links[spec.html_key], "web-native"))
        return routes

    if "pdf" in links:
        family = "publisher-pdf" if spec and spec.publisher else "direct-pdf"
        routes.append(Route("pdf", links["pdf"], family))
    if "nature" in links:
        routes.append(Route("pdf", nature_pdf(links["nature"]), "publisher-pdf"))
        if "pmc" in links:  # fallback mirror, same article
            routes.append(Route("pdf", pmc_pdf(links["pmc"]), "publisher-pdf"))
            # Full-text XML, not an abstract page: used only when both PDF
            # endpoints answer with a browser challenge.
            xml = europepmc_xml(links["pmc"])
            if xml:
                routes.append(Route("xml", xml, "publisher-pdf"))
    if "springer" in links:
        routes.append(Route("pdf", springer_pdf(links["springer"]), "publisher-pdf"))
    for key in ("pmlr", "icml"):  # both keys point at a PMLR landing when present
        if key in links and "proceedings.mlr.press" in links[key]:
            routes.append(Route("pdf", pmlr_pdf(links[key]), "pmlr"))
    if "neurips" in links:
        routes.append(Route("pdf", links["neurips"], "neurips"))
    return routes


def normalise_arxiv_id(raw: str) -> str:
    """Canonicalise a matched id so every URL builder works from the stored form.

    Strip a trailing version suffix (`...v2`), keeping the archive/subclass case
    as published. The stored id is always unversioned, which is what makes
    `arxiv.org/src/<id>`, `arxiv.org/abs/<id>` and version-suffixed variants
    (`<id>v1`) resolve from one value, modern or legacy alike. The resolved
    revision is stored separately in `Paper.arxiv_rev` (#33), so stripping here
    never discards it.
    """
    return re.sub(r"v\d+$", "", raw.strip())
LINK_RE = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<url>[^)]+)\)")
# Optional backslashes: this README and upstream's both write `— [nie et al. 2023]`
# unescaped, so requiring `\[` matched nothing and citation was empty on every entry
# ever committed. parse_index() strips links out before applying this, which is what
# keeps `[arxiv]` and `[video]` from being read as the citation.
CITATION_RE = re.compile(r"\\?\[(?P<cite>[^\[\]]+?)\\?\]")

# The version an export-API Atom entry describes: `<id>.../abs/2102.10154v3</id>`.
# The id fragment is shared with the README patterns above; `vN` is read, never
# constructed. A legacy id (`cond-mat/0011094`) matches too, slash and all.
ARXIV_VERSION_RE = re.compile(rf"/abs/(?P<id>{ARXIV_ID})v(?P<rev>\d+)\s*</id>")
# The same fact on the abs page's submission history: `/abs/<id>vN` links.
ARXIV_ABS_VERSION_RE = re.compile(rf"/abs/(?P<id>{ARXIV_ID})v(?P<rev>\d+)")

# Section headings in the README: "## papers", "## queue", "## extras", plus
# category headers like "  - tabular" and "    - forecasting".
CATEGORY_RE = re.compile(r"^(?P<indent>\s*)-\s+(?P<name>[^\n]+?)\s*$")
H2_RE = re.compile(r"^##\s+(?P<name>.+?)\s*$")
# An INDENTED `##` is a sub-heading inside a bullet group, not a new section: the
# actuarial block uses these for its severity / frequency / tail split. H2_RE is
# anchored at the start of the line and CATEGORY_RE needs a "- " bullet, so without
# this neither matches and all 28 entries lose their subcategory.
SUB_H2_RE = re.compile(r"^(?P<indent>\s+)##\s+(?P<name>.+?)\s*$")

# Sections that are listed in the README but never parsed into entries: workshop
# and site links ("extras"), Prior Labs cookbook recipes and blog posts, the setup
# preamble, and the upstream banner. They are catalogue rows, not papers, so they
# carry no entry, status or fetch attempt.
NON_PAPER_H2 = {"extras", "cookbooks", "blog", "how 2 set up", "fm4sd papers"}


@dataclass
class Paper:
    """One resolvable entry from the index."""

    slug: str
    arxiv_id: str
    section: str
    category: str
    subcategory: str
    citation: str = ""
    links: dict[str, str] = field(default_factory=dict)

    # Pinned arXiv revision N of id@vN (#33). `arxiv_id` stays unversioned --
    # slugs, licence carry-forward and match_year key off it -- so the revision
    # lives beside it. 0 means unresolved/unpinned and is omitted from the JSON.
    arxiv_rev: int = 0

    # Populated by fetch.
    source: str = ""          # "tex" | "pdf" | "html" | "xml"
    route: str = ""           # non-arXiv family used: direct-pdf | publisher-pdf | pmlr | neurips | web-native
    path: str = ""            # papers/<slug>/
    text_bytes: int = 0       # size of extracted plain text
    pages: int = 0            # PDF page count (pdf only)
    n_tex_files: int = 0      # .tex files extracted (tex only)
    sha256: str = ""          # of the downloaded bundle
    fetch_status: str = ""    # "ok" | "cached" | "skipped:not-paper" | "skipped:unreachable:<reason>"

    # Keys other tools wrote into the manifest that this script does not derive but
    # must not destroy when the manifest is rebuilt -- the licence fields from
    # fm4sd_licences.py. Flattened back into the JSON by to_json(), never serialised
    # as an "extra" object, so a manifest built here and a manifest built before the
    # split read the same way.
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def has_code(self) -> bool:
        return any(k in self.links for k in ("github", "code"))

    @property
    def venues(self) -> list[str]:
        return [v for k, v in self.links.items() if k not in ("arxiv", "pdf")]

    def to_json(self) -> dict:
        d = asdict(self)
        d.update(d.pop("extra", {}))
        # `route` describes a non-arXiv payload only; an empty value is omitted so
        # the 323 arXiv rows keep exactly the shape they had before #29 added the
        # field (a full manifest rewrite should show them as unchanged).
        if not d.get("route"):
            d.pop("route", None)
        # Same for the revision pin: id-less rows have none, and omitting it keeps
        # their shape unchanged.
        if not d.get("arxiv_rev"):
            d.pop("arxiv_rev", None)
        d["has_code"] = self.has_code
        return d


def slugify(text: str) -> str:
    """Normalise a README slug to a safe directory name."""
    s = re.sub(r"\\\[|\\\]", "", text).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


class RateLimiter:
    """Block until REQS_PER_SECOND worth of time has passed since the last call.

    A plain call, not a generator: a generator's frame stays live across the
    yield, so a concurrent next() re-enters it and raises
    ValueError("generator already executing"). That surfaced as a wave of fake
    "fetch failed" statuses. Here the mutex spans sleep-and-stamp, so threads
    queue up correctly.
    """

    def __init__(self, rate: float = REQS_PER_SECOND) -> None:
        self.interval = 1.0 / rate
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = self._last + self.interval - now
            if delay > 0:
                time.sleep(delay)
            self._last = time.monotonic()


class Limiters:
    """One limiter per politeness contract: arXiv 3 req/s, web routes ~1 req/s."""

    def __init__(self) -> None:
        self.arxiv = RateLimiter(REQS_PER_SECOND)
        self.web = RateLimiter(POLITE_REQS_PER_SECOND)


def http_get(url: str, limiter: RateLimiter, retries: int = 3) -> bytes:
    """GET with backoff. Raises on final failure."""
    last_err: Exception | None = None
    for attempt in range(retries):
        limiter.wait()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last_err = e
            # 404 is definitive; do not retry it.
            if isinstance(e, urllib.error.HTTPError) and e.code == 404:
                raise
            time.sleep(2**attempt)
    raise last_err  # type: ignore[misc]


def resolve_arxiv_rev(arxiv_id: str, limiter: RateLimiter,
                      fallback: RateLimiter | None = None) -> int:
    """Return the revision number arXiv currently serves for an unversioned id.

    One export-API call per id: `id_list=<id>` returns the paper's Atom entry,
    whose `<id>` is `.../abs/<id>vN`. The revision is read off that response --
    never constructed from a version count we would have to guess. Returns 0
    when the API cannot be read or the id has no version, so the caller can
    record an honest gap instead of pinning something invented.

    If the API refuses the query (it answered 429 to every uncached request after
    the #33 migration's opening burst), fall back to the paper's abs page, whose
    submission history links every `/abs/<id>vN`; the highest N is the same fact
    read from the same record. Pass `fallback` to control that limiter.
    """
    url = f"{ARXIV_API}{urllib.parse.quote(arxiv_id, safe='/')}"
    try:
        blob = http_get(url, limiter)
    except Exception as e:  # noqa: BLE001
        if DEBUG:
            traceback.print_exc()
        print(f"    {arxiv_id}: API resolution failed ({type(e).__name__}); "
              f"reading the abs page instead", flush=True)
        return resolve_arxiv_rev_from_abs(arxiv_id, fallback or limiter)

    for m in ARXIV_VERSION_RE.finditer(blob.decode("utf-8", "replace")):
        if normalise_arxiv_id(m.group("id")).lower() == arxiv_id.lower():
            return int(m.group("rev"))
    print(f"    {arxiv_id}: the API response carried no version", flush=True)
    return 0


def resolve_arxiv_rev_from_abs(arxiv_id: str, limiter: RateLimiter) -> int:
    """Fallback: the highest revision linked from the paper's abs page.

    `/abs/<id>` lists the submission history as `/abs/<id>v1` … `/abs/<id>vN`;
    the maximum is the current revision. Nothing is constructed -- the page's own
    links are the evidence -- and 0 means the page could not be read.
    """
    url = f"https://arxiv.org/abs/{urllib.parse.quote(arxiv_id, safe='/')}"
    try:
        blob = http_get(url, limiter)
    except Exception as e:  # noqa: BLE001
        if DEBUG:
            traceback.print_exc()
        print(f"    {arxiv_id}: abs page resolution failed ({type(e).__name__})",
              flush=True)
        return 0
    versions = [int(m.group("rev"))
                for m in ARXIV_ABS_VERSION_RE.finditer(blob.decode("utf-8", "replace"))
                if normalise_arxiv_id(m.group("id")).lower() == arxiv_id.lower()]
    return max(versions, default=0)


def resolve_arxiv_revs(arxiv_ids: list[str], limiter: RateLimiter,
                       fallback: RateLimiter | None = None) -> dict[str, int]:
    """Resolve many ids in as few export-API calls as politeness allows.

    `id_list` accepts a comma-separated list, so the 323-id migration costs a
    handful of requests instead of 323. That matters: a long sequential run of
    single-id queries drew HTTP 429 from `export.arxiv.org` on 2026-10-31, even
    at 3 req/s -- the API's own guidance is much slower. Batches are spaced by
    the shared arXiv limiter; ids absent from a response stay unresolved (0),
    and a failed batch is reported rather than silently treated as "no version".

    Any id the API still has not answered for is resolved from its abs page, at
    `fallback`'s pace (the web limiter by default) rather than hammering the API.

    Keys are lowercased ids, because Atom responses are normalised in shape but
    we should not depend on the case of a legacy archive/subclass being echoed.
    """
    out: dict[str, int] = {}
    uniq = sorted(set(arxiv_ids))
    for start in range(0, len(uniq), ARXIV_API_BATCH):
        chunk = uniq[start:start + ARXIV_API_BATCH]
        query = ",".join(urllib.parse.quote(a, safe="/") for a in chunk)
        try:
            blob = http_get(f"{ARXIV_API}{query}", limiter)
        except Exception as e:  # noqa: BLE001
            if DEBUG:
                traceback.print_exc()
            print(f"    revision batch {start // ARXIV_API_BATCH + 1}: "
                  f"resolution failed ({type(e).__name__}: {e})", flush=True)
            continue
        for m in ARXIV_VERSION_RE.finditer(blob.decode("utf-8", "replace")):
            out[normalise_arxiv_id(m.group("id")).lower()] = int(m.group("rev"))

    leftover = [a for a in uniq if a.lower() not in out]
    if leftover:
        print(f"    {len(leftover)} id(s) unresolved by the API; reading their "
              f"abs pages at the web rate", flush=True)
        slow = fallback or RateLimiter(POLITE_REQS_PER_SECOND)
        for aid in leftover:
            rev = resolve_arxiv_rev_from_abs(aid, slow)
            if rev:
                out[aid.lower()] = rev
    return out


def marker_text(kind: str, sha256: str, rev: int = 0) -> str:
    """The `.fetched` marker body: kind, digest, and the pinned revision (#33).

    Three lines when pinned (`tex\\n<sha256>\\nv3`), two otherwise, so markers
    written before #33 stay readable by reconcile().
    """
    return f"{kind}\n{sha256}\n" + (f"v{rev}\n" if rev else "")


@dataclass(frozen=True)
class Marker:
    """What a `.fetched` marker records about the payload on disk."""

    kind: str
    sha256: str
    rev: int


def read_marker(dest: Path) -> Marker | None:
    """Read `papers/<slug>/.fetched`, or None when this entry has no payload.

    The marker is the record of what was fetched -- kind, our digest of the
    download, and (since #33) the pinned revision -- written by marker_text().
    Parsing it in one place is what stops the two fetch paths and reconcile()
    from disagreeing about its shape (#38): one copy recovered the revision, the
    other did not. A marker with only the kind line (pre-#29) yields an empty
    digest and revision 0, so the caller keeps what the manifest already had.
    """
    marker = dest / ".fetched"
    if not marker.exists():
        return None
    fields = marker.read_text().split()
    rev = 0
    if len(fields) > 2 and fields[2].startswith("v"):
        try:
            rev = int(fields[2][1:])
        except ValueError:
            rev = 0
    return Marker(kind=fields[0] if fields else "tex",
                  sha256=fields[1] if len(fields) > 1 else "",
                  rev=rev)


def cached_entry(paper: Paper, force: bool) -> bool:
    """Credit the payload already on disk. True when there is nothing to fetch.

    The cache short-circuit both fetch paths share, so the marker's digest and
    pinned revision are recovered identically whichever path owns the entry.
    """
    dest = PAPERS / paper.slug
    marker = read_marker(dest)
    if marker is None or force:
        return False
    paper.fetch_status = "cached"
    paper.path = str(dest.relative_to(REPO))
    if marker.sha256:
        paper.sha256 = marker.sha256
    if marker.rev:
        # The marker describes the payload actually on disk, so its revision wins
        # over a manifest that may have been rebuilt elsewhere.
        paper.arxiv_rev = marker.rev
    return True


def parse_index(markdown: str) -> list[Paper]:
    """Walk the README and pull out one Paper per resolvable entry."""
    papers: list[Paper] = []
    section = ""
    # Category stack keyed by indent width, so nested headers reset correctly.
    cats: list[tuple[int, str]] = []

    for raw in markdown.splitlines():
        line = raw.rstrip()

        h2 = H2_RE.match(line)
        if h2:
            name = h2.group("name").strip()
            section = "" if name.lower() in NON_PAPER_H2 else name.lower()
            cats = []
            continue

        if not section:
            continue

        sub = SUB_H2_RE.match(line)
        if sub:
            indent = len(sub.group("indent"))
            cats = [(i, n) for i, n in cats if i < indent]
            # Truncate at the first colon: "severity: loss distributions and heavy
            # tails" is worth reading in the README but too long to filter on, and
            # the head of it ("severity") is the part a query names.
            cats.append((indent, sub.group("name").split(":", 1)[0].strip()))
            continue

        # Category header: a bullet with no trailing content and no links.
        cat = CATEGORY_RE.match(line)
        if cat and "[" not in line:
            indent = len(cat.group("indent"))
            cats = [(i, n) for i, n in cats if i < indent]
            cats.append((indent, cat.group("name").strip()))
            continue

        entry = ENTRY_RE.match(line)
        if not entry:
            continue

        rest = entry.group("rest")
        links = {m.group("text").strip().lower(): m.group("url") for m in LINK_RE.finditer(rest)}
        cite = CITATION_RE.search(LINK_RE.sub("", rest))

        arxiv = ""
        for pattern in (ARXIV_RE, ARXIV_PDF_RE, ARXIV_ABS_RE):
            m = pattern.search(rest)
            if m:
                arxiv = normalise_arxiv_id(m.group("id"))
                break

        # Entries with no arXiv id are either benchmarks, blogs, or a link to
        # something else entirely. Keep them in the manifest so the count is
        # honest, but mark them so fetch skips them.
        category = cats[0][1] if cats else ""
        subcategory = cats[1][1] if len(cats) > 1 else ""

        papers.append(
            Paper(
                slug=slugify(entry.group("slug")),
                arxiv_id=arxiv,
                section=section,
                category=category.lower(),
                subcategory=subcategory.lower(),
                citation=(cite.group("cite") if cite else ""),
                links=links,
            )
        )

    return papers


# --------------------------------------------------------------------------
# Fetch
# --------------------------------------------------------------------------

def extract_text_from_tex(bundle: Path, dest: Path) -> tuple[int, int, Path]:
    """Unpack a .tar.gz of LaTeX sources and concatenate them into one .txt.

    Returns (n_tex_files, bytes_of_text, src_dir). Size is a crude quality
    signal: a bundle that yields only a few hundred bytes is a wrapper paper with
    no real content, and the caller should fall back to the PDF.
    """
    tex_dir = dest / "src"
    tex_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(bundle, "r:gz") as tf:
        # Defensive: refuse paths that escape the destination.
        for member in tf.getmembers():
            if member.name.startswith("/") or ".." in Path(member.name).parts:
                continue
            try:
                tf.extract(member, tex_dir, filter="data")
            except (tarfile.TarError, OSError):
                continue

    tex_files = sorted(tex_dir.rglob("*.tex"))
    chunks: list[str] = []
    for tf_path in tex_files:
        try:
            body = tf_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = tf_path.relative_to(tex_dir)
        chunks.append(f"\n\n===== FILE: {rel} =====\n\n{body}")

    text = "".join(chunks).encode("utf-8", "replace")
    (dest / "text.txt").write_bytes(text)
    return len(tex_files), len(text), tex_dir


def extract_text_from_pdf(pdf_bytes: bytes, dest: Path) -> tuple[int, bytes]:
    """Write the PDF and extract its text with PyMuPDF."""
    pdf_path = dest / "paper.pdf"
    pdf_path.write_bytes(pdf_bytes)

    import pymupdf  # imported lazily so --index works without it

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    parts = []
    for page in doc:
        parts.append(f"\n\n===== PAGE {page.number + 1} =====\n\n{page.get_text()}")
    pages = doc.page_count
    doc.close()

    text = "".join(parts).encode("utf-8", "replace")
    (dest / "text.txt").write_bytes(text)
    return pages, len(text)


class _HTMLText(HTMLParser):
    """Strip tags from a server-rendered HTML paper, keeping block structure.

    Stdlib only, no readability heuristics: the four HTML papers in the index are
    single-column article pages, so block boundaries plus dropped script/style
    give greppable prose with headings and paragraphs intact. Anything that
    depends on JavaScript to render (a shell with no body text) exits near zero
    bytes and is rejected by the caller's length guard rather than stored.
    """

    SKIP = {"script", "style", "noscript", "template", "svg", "head"}
    BLOCK = {"p", "div", "section", "article", "main", "header", "footer", "aside",
             "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "br", "hr",
             "tr", "table", "pre", "blockquote", "figure", "figcaption"}

    def __init__(self, all_tags_block: bool = False) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self._all = all_tags_block
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self.SKIP:
            self._skip += 1
        elif tag in self.BLOCK or self._all:
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        if tag in self.BLOCK or self._all:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP:
            self._skip = max(0, self._skip - 1)
        elif tag in self.BLOCK or self._all:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def extract_text_from_html(html_bytes: bytes, dest: Path, all_tags_block: bool = False) -> tuple[int, int]:
    """Write the page and its extracted text. Returns (0 pages, bytes of text).

    Used for both server-rendered HTML papers and JATS XML full text; pass
    `all_tags_block=True` for XML, where every element boundary is a line break.
    """
    (dest / "page.html").write_bytes(html_bytes)

    ex = _HTMLText(all_tags_block=all_tags_block)
    ex.feed(html_bytes.decode("utf-8", "replace"))
    ex.close()

    text = "".join(ex.parts)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    data = text.encode("utf-8", "replace")
    (dest / "text.txt").write_bytes(data)
    return 0, len(data)


class RoutePayloadError(Exception):
    """A route answered, but with something that is not the paper."""

    def __init__(self, message: str, reason: str = "unknown") -> None:
        super().__init__(message)
        self.reason = reason


# Bodies that mean "a browser challenge got in the way", not "wrong document":
# F5 ("Client Challenge" -- Nature, Springer), Cloudflare ("Just a moment"),
# OpenReview ("Verifying your browser"). Matched case-insensitively in the head
# of an HTML response where a PDF was expected.
CHALLENGE_MARKERS = (b"client challenge", b"just a moment", b"verifying your browser",
                     b"challenge-platform", b"captcha")


def looks_challenged(blob: bytes) -> bool:
    head = blob[:8192].lower()
    return any(m in head for m in CHALLENGE_MARKERS)


def classify_failure(exc: BaseException) -> str:
    """Map a failed route to the reason vocabulary the manifest records.

    Deliberately coarse. The authority for a row that is known unreachable is the
    static audit table (ROUTES), not this function; this only labels a route that
    failed today, so that a route rotting between probes still says *why* rather
    than leaving an identifier-gap status behind. 403 is labelled `captcha`
    because every 403 observed in the audit was a browser challenge (Cloudflare,
    OpenReview, ResearchGate) rather than a subscription wall; a 401/402 is a
    `paywall`.
    """
    if isinstance(exc, RoutePayloadError) and exc.reason != "unknown":
        return exc.reason
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in (401, 402):
            return "paywall"
        if exc.code in (403, 407, 429, 503):
            return "captcha"
        if exc.code in (404, 410):
            return "dead"
        return "unknown"
    if isinstance(exc, urllib.error.URLError):
        return "dead" if isinstance(exc.reason, socket.gaierror) else "unknown"
    return "unknown"


def fetch_arxiv(paper: Paper, limiter: RateLimiter, force: bool = False) -> Paper:
    """Resolve one arXiv paper to papers/<slug>/{bundle,src|text.txt}.

    The revision is pinned before anything is downloaded (#33): a fresh row is
    resolved through the export API on first fetch, and a row that already has
    `arxiv_rev` keeps that pin. Only `--force` re-resolves and moves the pin to
    the current revision -- a newer upstream version is otherwise reported, not
    adopted. URLs are built from the version-suffixed form, so the recorded
    sha256 means "this revision, byte for byte".
    """
    dest = PAPERS / paper.slug
    if cached_entry(paper, force):
        return paper

    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / ".fetched"
    aid = paper.arxiv_id
    paper.path = str(dest.relative_to(REPO))

    # --- pin the revision first ---
    # cmd_fetch resolves every needed id in one batched pass first (including
    # under --force), so only an unresolved id retries here.
    if not paper.arxiv_rev:
        rev = resolve_arxiv_rev(aid, limiter)
        if rev:
            if paper.arxiv_rev and paper.arxiv_rev != rev:
                print(f"    {paper.slug}: bumped {aid}v{paper.arxiv_rev} -> v{rev}",
                      flush=True)
            paper.arxiv_rev = rev
    # No resolved revision -> the bare URL (old behaviour), so an API outage
    # costs a pin, not the payload. The row then has a digest but no revision,
    # which --status/--check-revisions report plainly.
    suffix = f"v{paper.arxiv_rev}" if paper.arxiv_rev else ""

    # --- try LaTeX source first ---
    try:
        blob = http_get(f"https://arxiv.org/src/{aid}{suffix}", limiter)
        bundle = dest / "source.tar.gz"
        bundle.write_bytes(blob)
        paper.sha256 = hashlib.sha256(blob).hexdigest()
        n_tex, n_bytes, tex_dir = extract_text_from_tex(bundle, dest)

        # A stub bundle (no .tex, or almost no text) is not worth keeping.
        if n_tex > 0 and n_bytes > MIN_TEXT_BYTES:
            paper.source = "tex"
            paper.n_tex_files = n_tex
            paper.text_bytes = n_bytes
            paper.fetch_status = "ok"
            bundle.unlink(missing_ok=True)
            # Drop the unpacked sources. They carry .pdf/.png figure binaries and
            # dominate disk (~2.6 MB src vs 152 KB text for a single paper), and
            # text.txt already holds every word. --keep-src retains them when
            # figures are actually wanted.
            if not KEEP_SRC:
                shutil.rmtree(tex_dir, ignore_errors=True)
            marker.write_text(marker_text("tex", paper.sha256, paper.arxiv_rev))
            return paper

        for stale in (bundle, dest / "src", dest / "text.txt"):
            shutil.rmtree(stale, ignore_errors=True)
    except Exception as e:  # noqa: BLE001
        if DEBUG:
            traceback.print_exc()
        paper.fetch_status = f"src-error:{type(e).__name__}"

    # --- fall back to PDF ---
    try:
        pdf = http_get(f"https://arxiv.org/pdf/{aid}{suffix}", limiter)
        pages, n_bytes = extract_text_from_pdf(pdf, dest)
        paper.sha256 = hashlib.sha256(pdf).hexdigest()
        paper.source = "pdf"
        paper.pages = pages
        paper.text_bytes = n_bytes
        paper.fetch_status = "ok"
        marker.write_text(marker_text("pdf", paper.sha256, paper.arxiv_rev))
        return paper
    except Exception as e:  # noqa: BLE001
        if DEBUG:
            traceback.print_exc()
        paper.fetch_status = f"pdf-error:{type(e).__name__}"

    return paper


def fetch_route(paper: Paper, limiter: RateLimiter, force: bool = False) -> Paper:
    """Resolve a non-arXiv entry through its route families, in order.

    Each candidate is a plain GET. A PDF route must return `%PDF-` and an HTML
    route must yield a paper's worth of text, otherwise the route has answered
    with a landing page, a challenge or a stub and the next candidate is tried.
    If every candidate fails, the entry records `skipped:unreachable:<reason>` --
    never an error class from the transport, and never `no-arxiv-id`.
    """
    dest = PAPERS / paper.slug
    if cached_entry(paper, force):
        paper.extra.update(licence_record(paper.slug))
        return paper

    routes = route_candidates(paper)
    if not routes:
        # Not reachable, not a paper, or an id-less row no route covers yet: the
        # same cascade --index stamps, from one definition. `pending` is
        # unreachable here because the branch requires an empty route list.
        paper.fetch_status = absence_status(paper)
        return paper

    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / ".fetched"
    paper.path = str(dest.relative_to(REPO))
    paper.extra.update(licence_record(paper.slug))

    reasons: list[str] = []
    for route in routes:
        try:
            blob = http_get(route.url, limiter)
            if route.kind == "pdf":
                if not blob.startswith(b"%PDF"):
                    reason = "captcha" if looks_challenged(blob) else "unknown"
                    raise RoutePayloadError(
                        f"{route.url} did not return a PDF"
                        + (" (browser challenge)" if reason == "captcha" else ""),
                        reason=reason)
                pages, n_bytes = extract_text_from_pdf(blob, dest)
                paper.pages = pages
            else:
                if looks_challenged(blob):
                    raise RoutePayloadError(
                        f"{route.url} is a browser challenge", reason="captcha")
                pages, n_bytes = extract_text_from_html(
                    blob, dest, all_tags_block=(route.kind == "xml"))
                if n_bytes < MIN_TEXT_BYTES:
                    raise RoutePayloadError(
                        f"{route.url} yielded {n_bytes} bytes of text")
            paper.sha256 = hashlib.sha256(blob).hexdigest()
            paper.source = route.kind
            paper.route = route.family
            paper.text_bytes = n_bytes
            paper.fetch_status = "ok"
            marker.write_text(marker_text(route.kind, paper.sha256, paper.arxiv_rev))
            return paper
        except Exception as e:  # noqa: BLE001
            if DEBUG:
                traceback.print_exc()
            reasons.append(classify_failure(e))
            print(f"    {paper.slug}: {route.family} failed "
                  f"({type(e).__name__}: {e})", flush=True)

    # Keep the most specific reason: a challenge is a different fact from a 404.
    for reason in ("captcha", "paywall", "dead", "unknown"):
        if reason in reasons:
            paper.fetch_status = f"skipped:unreachable:{reason}"
            break

    # Do not leave a half-written payload behind for a row that did not fetch.
    for stale in ("text.txt", "paper.pdf", "page.html"):
        (dest / stale).unlink(missing_ok=True)
    paper.source = paper.route = ""
    paper.path = ""
    paper.text_bytes = paper.pages = 0
    paper.sha256 = ""
    return paper


def fetch_one(paper: Paper, limiters: "Limiters", force: bool = False) -> Paper:
    """Dispatch one entry to the arXiv path or a non-arXiv route family."""
    if paper.arxiv_id:
        return fetch_arxiv(paper, limiters.arxiv, force)
    return fetch_route(paper, limiters.web, force)


MANIFEST_DELIM = "\n--- entries ---\n"


def dump_manifest(papers: list[Paper], source: str) -> str:
    """Manifest is a header object, a delimiter line, then the entries array.

    A delimiter rather than a bare newline, so reading it back is unambiguous
    instead of depending on where the header object happens to end.
    """
    header = json.dumps({
        "source": source,
        "note": "Parsed from the fm4sd README. Payload lives in gitignored papers/.",
        "count": len(papers),
    }, indent=2)
    return f"{header}{MANIFEST_DELIM}{json.dumps([p.to_json() for p in papers], indent=2)}\n"


def load_manifest() -> list[dict]:
    """Read the entries array back out of the manifest."""
    raw = MANIFEST.read_text()
    if MANIFEST_DELIM not in raw:
        sys.exit(f"{MANIFEST} is malformed; rerun --index")
    return json.loads(raw.split(MANIFEST_DELIM, 1)[1])


def save_manifest(entries: list[dict]) -> None:
    header = MANIFEST.read_text().split(MANIFEST_DELIM, 1)[0]
    MANIFEST.write_text(f"{header}{MANIFEST_DELIM}{json.dumps(entries, indent=2)}\n")


def corpus_figures(entries: list[dict]) -> dict[str, int | float]:
    """Every corpus figure the documents publish, derived from manifest entries.

    The one definition: `fm4sd_search.py stats` prints from it and the
    reproducibility gate compares the published prose against it, so a change to
    what "fetched", "tex" or "code" means lands in one place instead of two that
    can drift (#38). Counts are payload-derived, so this reads the manifest and
    never `papers/`.
    """
    fetched = [e for e in entries if e.get("fetch_status") in FETCHED_STATUSES]
    return {
        "entries": len(entries),
        "with_id": sum(1 for e in entries if e.get("arxiv_id")),
        "without_id": sum(1 for e in entries if not e.get("arxiv_id")),
        "fetched": len(fetched),
        "tex": sum(1 for e in fetched if e.get("source") == "tex"),
        "pdf": sum(1 for e in fetched if e.get("source") == "pdf"),
        "html": sum(1 for e in fetched if e.get("source") in ("html", "xml")),
        "code": sum(1 for e in entries if e.get("has_code")),
        "text_bytes": sum(int(e.get("text_bytes") or 0) for e in fetched),
        "licences": sum(1 for e in entries if e.get("licence") == "api-omitted"),
        "licence_url_rows": sum(1 for e in entries if e.get("licence_url")),
        "licence_source_rows": sum(1 for e in entries if e.get("licence_source")),
        "skipped_total": sum(
            1 for e in entries if str(e.get("fetch_status") or "").startswith("skipped:")
        ),
        "skip_captcha": sum(
            1 for e in entries
            if e.get("fetch_status") == "skipped:unreachable:captcha"
        ),
        "skip_paywall": sum(
            1 for e in entries
            if e.get("fetch_status") == "skipped:unreachable:paywall"
        ),
        "skip_unknown": sum(
            1 for e in entries
            if e.get("fetch_status") == "skipped:unreachable:unknown"
        ),
        "skip_dead": sum(
            1 for e in entries
            if e.get("fetch_status") == "skipped:unreachable:dead"
        ),
        "not_paper": sum(
            1 for e in entries if e.get("fetch_status") == "skipped:not-paper"
        ),
    }


def reconcile(papers: list[Paper]) -> int:
    """Recover fetch metadata from payload already on disk.

    Re-running --index rebuilds entries from the README and would otherwise drop
    every fetch_status, forcing a needless refetch of text we already have.
    Anything with a .fetched marker and a readable text.txt is credited back.

    The marker's second line, written since #29, is the payload's sha256; older
    markers carry only the kind, and their digest is recovered from the prior
    manifest by preserve_fetch() instead. The same raise-or-die rule applies to
    id-less route entries: a payload on disk is `ok` whatever the index says.
    """
    recovered = 0
    for p in papers:
        dest = PAPERS / p.slug
        marker = read_marker(dest)
        text = dest / "text.txt"
        if marker is None or not text.exists():
            continue
        p.source = marker.kind if marker.kind in ("tex", "pdf", "html", "xml") else "tex"
        p.text_bytes = text.stat().st_size
        p.path = str(dest.relative_to(REPO))
        p.fetch_status = "ok"
        if marker.sha256:
            p.sha256 = marker.sha256
        if marker.rev:
            p.arxiv_rev = marker.rev
        if marker.kind == "pdf":
            pdf = dest / "paper.pdf"
            if pdf.exists():
                p.pages = 0  # page count not stored; cheap to re-derive if needed
        recovered += 1
    return recovered


def load_prior() -> dict[str, dict]:
    """The manifest as it stands now, keyed by slug. Missing or malformed -> {}.

    This is the only place `--index` learns about fields it does not derive itself.
    """
    if not MANIFEST.exists():
        return {}
    try:
        return {e["slug"]: e for e in load_manifest()}
    except SystemExit:
        return {}
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}


def carry_forward(papers: list[Paper], prior: dict[str, dict]) -> int:
    """Keep metadata other tools wrote into the manifest across a rebuild.

    `cmd_index()` re-derives everything from the README, so any key that is not a
    `Paper` field -- the licence, published-date and title records written by
    fm4sd_licences.py, and the licence/licence_source/shareable records written by
    the route fetcher -- was being deleted by the next `--index`. The README tells
    you to run `--index` first, so that was the documented path to losing them:
    253 licence records went to 0 on a fresh clone.

    Carried only when the arXiv id is unchanged. Licence, title and published date
    all hang off that id, so a corrected link must not inherit them from the old
    one -- the entry just loses its carried metadata and gets re-resolved. Id-less
    rows compare "" == "" and keep their route licence record, which is what makes
    the 18 non-arXiv rows survive `--index`.
    """
    kept = 0
    fields = set(Paper.__annotations__)
    for p in papers:
        old = prior.get(p.slug)
        if not old or old.get("arxiv_id") != p.arxiv_id:
            continue
        carried = {k: v for k, v in old.items() if k not in fields and k != "has_code"}
        if carried:
            p.extra = carried
            kept += 1
    return kept


FETCH_FIELDS = ("source", "route", "path", "text_bytes", "pages", "n_tex_files",
                "sha256", "fetch_status", "arxiv_rev")


def preserve_fetch(papers: list[Paper], prior: dict[str, dict]) -> int:
    """Restore recorded fetch metadata when the payload is not on this tree.

    #33 recorded which arXiv revision a digest belongs to and made the fetch URL
    version-suffixed; this is still the narrower half: the manifest is a record of
    a fetch that happened, and rebuilding it on a machine without `papers/` (the
    normal state of a clone -- the payload is gitignored) must not erase that
    record. Reconcile covers the payload-present
    case; this covers the payload-absent one, and only when the identity is
    unchanged (same slug, same arXiv id) and the static route tables have not
    since learned the row is unreachable. A stale `ok` is therefore never used to
    contradict a reason the code now records.
    """
    kept = 0
    for p in papers:
        old = prior.get(p.slug)
        if not old or old.get("arxiv_id") != p.arxiv_id:
            continue
        if recorded_absence(p.slug):
            continue  # the recorded reason is newer knowledge than the old record
        if not (p.arxiv_id or route_candidates(p)):
            continue
        if p.fetch_status not in FETCHED_STATUSES:
            old_status = old.get("fetch_status") or ""
            if old_status in FETCHED_STATUSES:
                for k in FETCH_FIELDS:
                    if k in old:
                        setattr(p, k, old[k])
                kept += 1
                continue
            # A route we tried and failed yesterday is newer knowledge than the
            # static tables, which only record the audit's probe. Preserve the
            # reason until --fetch retries the route; the reason tables above win
            # because they are code, not a past run.
            if (old_status.startswith("skipped:unreachable:") and route_candidates(p)):
                for k in ("path", "licence", *LICENCE_URL_FIELDS, "shareable"):
                    if old.get(k):
                        if k in FETCH_FIELDS:
                            setattr(p, k, old[k])
                        else:
                            p.extra[k] = old[k]
                p.fetch_status = old_status
                kept += 1
            continue
        # Payload was found on disk: fill in what the marker cannot carry.
        for k in ("route", "sha256", "arxiv_rev", "pages", "n_tex_files"):
            if not getattr(p, k) and old.get(k):
                setattr(p, k, old[k])
    return kept


def absence_status(paper: Paper) -> str:
    """The status an id-less entry carries before any fetch is attempted.

    The one cascade `--index` stamps every id-less row with and `fetch_route`
    reaches when no candidate route exists. Retires `skipped:no-arxiv-id` (#29):
    an entry without an arXiv id is either not a paper, known unreachable for a
    named reason, or has a route to try (`pending`).
    """
    recorded = recorded_absence(paper.slug)
    if recorded:
        return recorded
    if route_candidates(paper):
        return "pending"
    return "skipped:unreachable:unknown"


def compare_remote() -> None:
    """Parse upstream's index and diff it against ours. Writes nothing.

    `--remote` used to be `cmd_index(remote=True)` in disguise: it wrote MANIFEST
    from upstream's README, which swapped our 303 entries for upstream's 355 and
    took the 28 actuarial papers with them. Reading one side of a fork must not be
    able to overwrite the record on the other side.
    """
    limiter = RateLimiter()
    md = http_get(INDEX_URL, limiter).decode("utf-8", "replace")
    up = parse_index(md)

    local: list[Paper] = []
    local_path = REPO / "README.md"
    if local_path.exists():
        local = parse_index(local_path.read_text(encoding="utf-8", errors="replace"))
    elif MANIFEST.exists():
        local = [Paper(**{k: v for k, v in e.items() if k in Paper.__annotations__})
                 for e in load_prior().values()]

    us = {p.slug for p in up}
    ls = {p.slug for p in local}

    def with_arxiv(ps: list[Paper]) -> int:
        return sum(1 for p in ps if p.arxiv_id)

    print(f"upstream  {len(up)} entries ({with_arxiv(up)} with an arXiv id)   {INDEX_URL}")
    print(f"local     {len(local)} entries ({with_arxiv(local)} with an arXiv id)")
    if local:
        print(f"  {len(us - ls):4d} upstream only — not in this index yet")
        print(f"  {len(ls - us):4d} local only    — ours, e.g. candidates for a PR back")
        print(f"  {len(us & ls):4d} in both")
        for label, slugs in (("upstream only", sorted(us - ls)), ("local only", sorted(ls - us))):
            if not slugs:
                continue
            shown = ", ".join(slugs[:20])
            more = f", … +{len(slugs) - 20} more" if len(slugs) > 20 else ""
            print(f"\n{label}:\n  {shown}{more}")
    print("\nnothing written — this flag only reads upstream")


def cmd_index(remote: bool = False) -> None:
    # Default to the LOCAL README. This repo is a fork we took over, so local edits -- a new
    # category, a corrected link -- must be what gets parsed. Fetching the upstream URL
    # silently ignored every local addition, which is how 28 freshly added entries parsed
    # to zero until this branch caught it. `--remote` reads upstream instead, but only to
    # compare: see compare_remote().
    if remote:
        compare_remote()
        return

    missing = [rel for rel, required in INDEX_INPUTS if required and not (REPO / rel).exists()]
    if missing:
        sys.exit(f"--index needs {', '.join(missing)} at the repo root; "
                 f"--remote compares against upstream without writing")
    local = REPO / "README.md"
    source = "LOCAL README.md"
    md = local.read_text(encoding="utf-8", errors="replace")
    papers = parse_index(md)
    # Id-less entries are stamped with the reason they are absent, not with the
    # identifier they lack (#29). `pending` is reserved for a row that has a
    # route to try and has not been fetched yet; reconcile() below overrides it
    # to "ok" where a payload is already on disk.
    uncovered: list[str] = []
    for p in papers:
        if not p.arxiv_id:
            p.fetch_status = absence_status(p)
            if p.fetch_status == "skipped:unreachable:unknown" and not recorded_absence(p.slug):
                uncovered.append(p.slug)
    prior = load_prior()
    carried = carry_forward(papers, prior)
    recovered = reconcile(papers)
    preserved = preserve_fetch(papers, prior)
    # The licence/shareability record for a route entry is static evidence, not a
    # fetch artefact, so it is reproducible from the index alone -- a fresh clone
    # gets the same `licence`/`licence_source`/`shareable` rows as a fetched tree.
    for p in papers:
        p.extra.update(licence_record(p.slug))
    # `--status` and the manifest must speak one vocabulary: an unfetched entry
    # with a route to try is `pending`, whichever fetch path it belongs to.
    for p in papers:
        if not p.fetch_status:
            p.fetch_status = "pending"

    REFERENCES.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(dump_manifest(papers, source))

    with_arxiv = sum(1 for p in papers if p.arxiv_id)
    with_code = sum(1 for p in papers if p.has_code)
    fetched = sum(1 for p in papers if p.fetch_status == "ok")
    routable = sum(1 for p in papers if not p.arxiv_id and route_candidates(p))
    print(f"parsed {len(papers)} entries -> {MANIFEST.relative_to(REPO)}")
    print(f"  {with_arxiv} have an arXiv id ({with_arxiv / len(papers):.0%})")
    print(f"  {routable} have a non-arXiv route (direct/publisher PDF, PMLR, NeurIPS, HTML)")
    not_paper = sum(1 for s in ROUTES.values() if s.absence == "not-paper")
    unreachable = sum(1 for s in ROUTES.values()
                      if s.absence and s.absence != "not-paper")
    print(f"  {not_paper} are not papers; {unreachable} are unreachable by plain HTTP")
    print(f"  {with_code} link released code")
    if recovered:
        print(f"  {recovered} already fetched locally (metadata recovered from disk)")
    else:
        print(f"  {fetched} fetched locally")
    if preserved:
        print(f"  {preserved} fetch records preserved from the prior manifest (payload not on this tree)")
    if carried:
        print(f"  {carried} carried forward metadata other tools wrote (licence, published, …)")
    for slug in uncovered:
        print(f"  ! {slug} has no arXiv id, no route and no recorded reason — add a "
              f"RouteSpec to ROUTES with an absence reason")
    for section in sorted({p.section for p in papers}):
        n = sum(1 for p in papers if p.section == section)
        print(f"  section {section or '(none)'}: {n}")


def cmd_fetch(only: list[str], force: bool, workers: int) -> None:
    if not MANIFEST.exists():
        sys.exit("no manifest; run --index first")

    entries = load_manifest()
    papers = [Paper(**{k: v for k, v in e.items() if k in Paper.__annotations__}) for e in entries]
    # arXiv entries and entries with a route; repo/blog rows and known-unreachable
    # rows are not attempted, they already carry the reason they are absent.
    papers = [p for p in papers if p.arxiv_id or route_candidates(p)]
    if only:
        known = {p.slug for p in papers} | {p.arxiv_id for p in papers}
        for name in only:
            if name not in known:
                print(f"  {name}: no arXiv id and no route — nothing to fetch "
                      f"(see --status for its reason)", flush=True)
        papers = [p for p in papers if p.slug in only or p.arxiv_id in only]

    PAPERS.mkdir(parents=True, exist_ok=True)
    limiters = Limiters()
    done = 0
    total = len(papers)

    # Resolve every unpinned (or, with --force, every) id up front in batched
    # export-API calls. Doing this per paper from four workers is what drew 429s
    # during the #33 migration; one batched pass is both faster and politer.
    unresolved_before = {p.slug: p.arxiv_rev for p in papers if p.arxiv_id}
    to_resolve = [p.arxiv_id for p in papers
                  if p.arxiv_id and (force or not p.arxiv_rev)]
    if to_resolve:
        batches = (len(set(to_resolve)) + ARXIV_API_BATCH - 1) // ARXIV_API_BATCH
        print(f"resolving {len(set(to_resolve))} arXiv revisions "
              f"({batches} export-API request{'s' if batches != 1 else ''})…", flush=True)
        resolved = resolve_arxiv_revs(to_resolve, limiters.arxiv, limiters.web)
        for p in papers:
            if not p.arxiv_id or not (force or not p.arxiv_rev):
                continue
            rev = resolved.get(p.arxiv_id.lower())
            if not rev:
                continue
            old = unresolved_before[p.slug]
            if old and old != rev:
                print(f"  bumped {p.slug}: {p.arxiv_id}v{old} -> v{rev}", flush=True)
            p.arxiv_rev = rev
        missing = sum(1 for p in papers if p.arxiv_id and not p.arxiv_rev)
        if missing:
            print(f"  ! {missing} id(s) left unpinned — the API did not give a "
                  f"version; they fetch the moving URL and are reported by "
                  f"--check-revisions", flush=True)

    # arXiv and web routes carry separate limiters, so a shared pool cannot turn
    # four workers into four requests per second against a publisher: the web
    # limiter serialises those at ~1 req/s while arXiv keeps its own budget.
    with futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch_one, p, limiters, force): p for p in papers}
        for fut in futures.as_completed(futs):
            p = fut.result()
            done += 1
            size_kb = p.text_bytes / 1024
            print(f"[{done:3d}/{total}] {p.slug:<42} {p.route or p.source or '-':<14} "
                  f"{size_kb:8.1f} KB  {p.fetch_status}", flush=True)

    entries_new = load_manifest()
    by_slug = {p.slug: p for p in papers}
    for e in entries_new:
        if e["slug"] in by_slug:
            e.update({k: v for k, v in by_slug[e["slug"]].to_json().items()
                      if k in (*FETCH_FIELDS, "licence", *LICENCE_URL_FIELDS, "shareable")})
    save_manifest(entries_new)

    ok = sum(1 for p in papers if p.fetch_status in FETCHED_STATUSES)
    tex = sum(1 for p in papers if p.source == "tex")
    pdf = sum(1 for p in papers if p.source == "pdf")
    html = sum(1 for p in papers if p.source in ("html", "xml"))
    mb = sum(p.text_bytes for p in papers) / 1e6
    print(f"\nfetched {ok}/{len(papers)}  ({tex} latex, {pdf} pdf, {html} html)  "
          f"{mb:.1f} MB of text")


def cmd_check_revisions(only: list[str]) -> None:
    """Resolve every pinned id and report drift against the manifest. Writes nothing.

    A digest pins one revision, and arXiv keeps every version, so a new `v(N+1)`
    does not invalidate the recorded digest -- it simply makes a newer revision
    available. This reports which pins are now behind without touching them, in
    keeping with #33's rule that a bump is deliberate: `--fetch --force --only
    <slug>` moves one pin, `--fetch --force` moves them all.
    """
    if not MANIFEST.exists():
        sys.exit("no manifest; run --index first")
    rows = [e for e in load_manifest() if e.get("arxiv_id")]
    if only:
        rows = [e for e in rows if e["slug"] in only or e["arxiv_id"] in only]

    limiter = RateLimiter(REQS_PER_SECOND)
    fallback = RateLimiter(POLITE_REQS_PER_SECOND)
    resolved = resolve_arxiv_revs(
        [e["arxiv_id"] for e in rows], limiter, fallback)
    current_count = behind = unpinned = unresolved = 0
    for e in rows:
        pinned = int(e.get("arxiv_rev") or 0)
        current = resolved.get(e["arxiv_id"].lower(), 0)
        if not current:
            unresolved += 1
            print(f"  unresolved  {e['slug']:<40} {e['arxiv_id']}")
        elif not pinned:
            unpinned += 1
            print(f"  unpinned    {e['slug']:<40} {e['arxiv_id']} -> v{current}")
        elif current == pinned:
            current_count += 1
        elif current > pinned:
            behind += 1
            print(f"  behind      {e['slug']:<40} {e['arxiv_id']}v{pinned} -> v{current}")
        else:
            unresolved += 1
            print(f"  ! pinned v{pinned} but the API says v{current} "
                  f"{e['slug']:<38} {e['arxiv_id']}")

    print(f"\n{len(rows)} id-bearing rows: {current_count} pinned to the current revision, "
          f"{behind} behind, {unpinned} unpinned, {unresolved} unresolved")
    if behind or unpinned:
        print("bump deliberately: --fetch --force [--only <slug> …] re-resolves and refetches")


def cmd_status() -> None:
    if not MANIFEST.exists():
        sys.exit("no manifest; run --index first")
    entries = load_manifest()
    ok = [e for e in entries if e.get("fetch_status") in FETCHED_STATUSES]
    print(f"{len(ok)}/{len(entries)} entries fetched locally")

    # A tally, so the reason vocabulary is checkable at a glance and the docs'
    # figures have one place to come from.
    tally: dict[str, int] = {}
    for e in entries:
        if e.get("fetch_status") in FETCHED_STATUSES:
            continue
        s = e.get("fetch_status") or "(pending)"
        tally[s] = tally.get(s, 0) + 1
    for s, n in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {n:3d}  {s}")

    for e in sorted(entries, key=lambda x: x["slug"]):
        if e.get("fetch_status") not in FETCHED_STATUSES:
            print(f"  {e['slug']:<44} {e.get('fetch_status') or '(pending)'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", action="store_true", help="parse the README into a manifest")
    ap.add_argument("--remote", action="store_true",
                    help="--index: diff the upstream index against ours; writes nothing")
    ap.add_argument("--fetch", action="store_true", help="fetch + extract text")
    ap.add_argument("--status", action="store_true", help="show what is fetched")
    ap.add_argument("--check-revisions", action="store_true", dest="check_revisions",
                    help="report pinned revisions that are behind upstream; writes nothing")
    ap.add_argument("--only", nargs="*", default=None, help="restrict to these slugs/ids")
    ap.add_argument("--force", action="store_true", help="refetch even if cached")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    if args.index:
        cmd_index(remote=args.remote)
    if args.fetch:
        cmd_fetch(args.only or [], args.force, args.workers)
    if args.status:
        cmd_status()
    if args.check_revisions:
        cmd_check_revisions(args.only or [])
    if not (args.index or args.fetch or args.status or args.check_revisions):
        ap.print_help()


if __name__ == "__main__":
    main()