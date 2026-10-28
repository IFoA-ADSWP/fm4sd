#!/usr/bin/env python3
"""Build a local, greppable corpus of papers from the fm4sd reading index.

The upstream repo (borawhocodess/fm4sd) is a README of links, nothing more --
its papers/ directory is gitignored, so there is nothing there to vendor. This
script reconstructs a local corpus from the same index by resolving each link.

For every entry it prefers the arXiv LaTeX source bundle (/src/<id>) over the
PDF, because the .tex files are plain text with section structure intact, which
is what makes the corpus greppable and cheap for a model to read. It falls back
to the PDF only when no source bundle exists.

Nothing here is committed except references/manifest.json. Raw bundles, .tex and
extracted text all live under papers/, which is gitignored -- several papers in
the index are arXiv non-exclusive-distrib or CC-BY-NC-SA, so redistributing the
payload would be a licensing problem. See PROVENANCE.md.

Usage:
    python3 scripts/fm4sd_fetch.py --index          # parse README -> manifest
    python3 scripts/fm4sd_fetch.py --fetch          # fetch + extract, all missing
    python3 scripts/fm4sd_fetch.py --fetch --only nanotabpfn modded-nanotabpfn
    python3 scripts/fm4sd_fetch.py --status
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import threading
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAPERS = REPO / "papers"
REFERENCES = REPO / "references"
MANIFEST = REFERENCES / "manifest.json"

INDEX_URL = "https://raw.githubusercontent.com/borawhocodess/fm4sd/main/README.md"
USER_AGENT = "fm4sd-corpus/1.0 (research; https://github.com/IFoA-ADSWP/fm4sd)"

# Politeness: arXiv asks that automated clients stay light. 3 req/s across a
# small pool is far below anything that would look like abuse.
REQS_PER_SECOND = 3.0
TIMEOUT = 60
DEBUG = bool(os.environ.get("FM4SD_DEBUG"))
KEEP_SRC = bool(os.environ.get("FM4SD_KEEP_SRC"))

# Entry shape in the README, e.g.
#   - tabpfn — [arxiv](https://arxiv.org/abs/2207.01848) · [iclr](...) — \[hollmann et al. 2023\]
ENTRY_RE = re.compile(r"^\s*-\s+(?P<slug>[^\n—]+?)\s+—\s+(?P<rest>.*)$")
ARXIV_RE = re.compile(r"https?://arxiv\.org/(?:abs|pdf)/(?P<id>\d{4}\.\d{4,5})")
ARXIV_PDF_RE = re.compile(r"https?://arxiv\.org/pdf/(?P<id>\d{4}\.\d{4,5})")
ARXIV_ABS_RE = re.compile(r"https?://arxiv\.org/abs/(?P<id>\d{4}\.\d{4,5})")
LINK_RE = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<url>[^)]+)\)")
CITATION_RE = re.compile(r"\\\[(?P<cite>[^\]]+)\\\]")

# Section headings in the README: "## papers", "## queue", "## extras", plus
# category headers like "  - tabular" and "    - forecasting".
CATEGORY_RE = re.compile(r"^(?P<indent>\s*)-\s+(?P<name>[^\n]+?)\s*$")
H2_RE = re.compile(r"^##\s+(?P<name>.+?)\s*$")

# The "extras" section is a list of workshops, surveys and site links -- not
# papers. Fetching those as if they were papers would just produce noise.
NON_PAPER_H2 = {"extras", "how 2 set up", "fm4sd papers"}


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

    # Populated by fetch.
    source: str = ""          # "tex" | "pdf"
    path: str = ""            # papers/<slug>/
    text_bytes: int = 0       # size of extracted plain text
    pages: int = 0            # PDF page count (pdf only)
    n_tex_files: int = 0      # .tex files extracted (tex only)
    sha256: str = ""          # of the downloaded bundle
    fetch_status: str = ""    # "ok" | "no-source" | "error: ..."

    @property
    def has_code(self) -> bool:
        return any(k in self.links for k in ("github", "code"))

    @property
    def venues(self) -> list[str]:
        return [v for k, v in self.links.items() if k not in ("arxiv", "pdf")]

    def to_json(self) -> dict:
        d = asdict(self)
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
        cite = CITATION_RE.search(rest)

        arxiv = ""
        for pattern in (ARXIV_RE, ARXIV_PDF_RE, ARXIV_ABS_RE):
            m = pattern.search(rest)
            if m:
                arxiv = m.group("id")
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


def dedupe(papers: list[Paper]) -> list[Paper]:
    """Collapse entries that resolve to the same arXiv id.

    The index repeats a few papers across sections (e.g. tabpfnv2 closer look
    appears in both papers and queue). Keep the first, which is the curated one.
    """
    seen: set[str] = set()
    out: list[Paper] = []
    for p in papers:
        key = p.arxiv_id or p.slug
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


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


def fetch_one(paper: Paper, limiter: RateLimiter, force: bool = False) -> Paper:
    """Resolve one paper to papers/<slug>/{bundle,src|text.txt}."""
    dest = PAPERS / paper.slug
    marker = dest / ".fetched"
    if marker.exists() and not force:
        paper.fetch_status = "cached"
        paper.path = str(dest.relative_to(REPO))
        return paper

    if not paper.arxiv_id:
        paper.fetch_status = "skipped:no-arxiv-id"
        return paper

    dest.mkdir(parents=True, exist_ok=True)
    aid = paper.arxiv_id
    paper.path = str(dest.relative_to(REPO))

    # --- try LaTeX source first ---
    try:
        blob = http_get(f"https://arxiv.org/src/{aid}", limiter)
        bundle = dest / "source.tar.gz"
        bundle.write_bytes(blob)
        paper.sha256 = hashlib.sha256(blob).hexdigest()
        n_tex, n_bytes, tex_dir = extract_text_from_tex(bundle, dest)

        # A stub bundle (no .tex, or almost no text) is not worth keeping.
        if n_tex > 0 and n_bytes > 4000:
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
            marker.write_text("tex\n")
            return paper

        for stale in (bundle, dest / "src", dest / "text.txt"):
            shutil.rmtree(stale, ignore_errors=True)
    except Exception as e:  # noqa: BLE001
        if DEBUG:
            traceback.print_exc()
        paper.fetch_status = f"src-error:{type(e).__name__}"

    # --- fall back to PDF ---
    try:
        pdf = http_get(f"https://arxiv.org/pdf/{aid}", limiter)
        pages, n_bytes = extract_text_from_pdf(pdf, dest)
        paper.sha256 = hashlib.sha256(pdf).hexdigest()
        paper.source = "pdf"
        paper.pages = pages
        paper.text_bytes = n_bytes
        paper.fetch_status = "ok"
        marker.write_text("pdf\n")
        return paper
    except Exception as e:  # noqa: BLE001
        if DEBUG:
            traceback.print_exc()
        paper.fetch_status = f"pdf-error:{type(e).__name__}"

    return paper


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


def reconcile(papers: list[Paper]) -> int:
    """Recover fetch metadata from payload already on disk.

    Re-running --index rebuilds entries from the README and would otherwise drop
    every fetch_status, forcing a needless refetch of text we already have.
    Anything with a .fetched marker and a readable text.txt is credited back.
    """
    recovered = 0
    for p in papers:
        marker = PAPERS / p.slug / ".fetched"
        text = PAPERS / p.slug / "text.txt"
        if not marker.exists() or not text.exists():
            continue
        kind = marker.read_text().strip() or "tex"
        p.source = kind if kind in ("tex", "pdf") else "tex"
        p.text_bytes = text.stat().st_size
        p.path = str((PAPERS / p.slug).relative_to(REPO))
        p.fetch_status = "ok"
        if kind == "pdf":
            pdf = PAPERS / p.slug / "paper.pdf"
            if pdf.exists():
                p.pages = 0  # page count not stored; cheap to re-derive if needed
        recovered += 1
    return recovered


def cmd_index(remote: bool = False) -> None:
    limiter = RateLimiter()
    # Default to the LOCAL README. This repo is a fork we took over, so local edits -- a new
    # category, a corrected link -- must be what gets parsed. Fetching the upstream URL
    # silently ignored every local addition, which is how 28 freshly added entries parsed
    # to zero until this branch caught it. `--remote` reads upstream instead, for checking
    # what the original index says.
    if remote:
        source = INDEX_URL
        md = http_get(INDEX_URL, limiter).decode("utf-8", "replace")
    else:
        local = REPO / "README.md"
        if not local.exists():
            sys.exit("no local README.md; use --remote to read the upstream index")
        source = "LOCAL README.md"
        md = local.read_text(encoding="utf-8", errors="replace")
    papers = dedupe(parse_index(md))
    recovered = reconcile(papers)

    REFERENCES.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(dump_manifest(papers, source))

    with_arxiv = sum(1 for p in papers if p.arxiv_id)
    with_code = sum(1 for p in papers if p.has_code)
    local = sum(1 for p in papers if p.fetch_status == "ok")
    print(f"parsed {len(papers)} entries -> {MANIFEST.relative_to(REPO)}")
    print(f"  {with_arxiv} have an arXiv id ({with_arxiv / len(papers):.0%})")
    print(f"  {with_code} link released code")
    if recovered:
        print(f"  {recovered} already fetched locally (metadata recovered from disk)")
    else:
        print(f"  {local} fetched locally")
    for section in sorted({p.section for p in papers}):
        n = sum(1 for p in papers if p.section == section)
        print(f"  section {section or '(none)'}: {n}")


def cmd_fetch(only: list[str], force: bool, workers: int) -> None:
    if not MANIFEST.exists():
        sys.exit("no manifest; run --index first")

    entries = load_manifest()
    papers = [Paper(**{k: v for k, v in e.items() if k in Paper.__annotations__}) for e in entries]
    papers = [p for p in papers if p.arxiv_id]
    if only:
        papers = [p for p in papers if p.slug in only or p.arxiv_id in only]

    PAPERS.mkdir(parents=True, exist_ok=True)
    limiter = RateLimiter()
    done = 0
    total = len(papers)

    with futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch_one, p, limiter, force): p for p in papers}
        for fut in futures.as_completed(futs):
            p = fut.result()
            done += 1
            size_kb = p.text_bytes / 1024
            print(f"[{done:3d}/{total}] {p.slug:<42} {p.source or '-':<4} "
                  f"{size_kb:8.1f} KB  {p.fetch_status}", flush=True)

    entries_new = load_manifest()
    by_slug = {p.slug: p for p in papers}
    for e in entries_new:
        if e["slug"] in by_slug:
            e.update({k: v for k, v in by_slug[e["slug"]].to_json().items()
                      if k in ("source", "path", "text_bytes", "pages",
                               "n_tex_files", "sha256", "fetch_status")})
    save_manifest(entries_new)

    ok = sum(1 for p in papers if p.fetch_status in ("ok", "cached"))
    tex = sum(1 for p in papers if p.source == "tex")
    pdf = sum(1 for p in papers if p.source == "pdf")
    mb = sum(p.text_bytes for p in papers) / 1e6
    print(f"\nfetched {ok}/{len(papers)}  ({tex} latex, {pdf} pdf)  {mb:.1f} MB of text")


def cmd_status() -> None:
    if not MANIFEST.exists():
        sys.exit("no manifest; run --index first")
    entries = load_manifest()
    ok = [e for e in entries if e.get("fetch_status") in ("ok", "cached")]
    print(f"{len(ok)}/{len(entries)} entries fetched locally")
    for e in sorted(entries, key=lambda x: x["slug"]):
        if e.get("fetch_status") not in ("ok", "cached"):
            print(f"  {e['slug']:<44} {e.get('fetch_status') or '(pending)'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", action="store_true", help="parse the README into a manifest")
    ap.add_argument("--remote", action="store_true",
                    help="--index: read the upstream index URL instead of the local README")
    ap.add_argument("--fetch", action="store_true", help="fetch + extract text")
    ap.add_argument("--status", action="store_true", help="show what is fetched")
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
    if not (args.index or args.fetch or args.status):
        ap.print_help()


if __name__ == "__main__":
    main()