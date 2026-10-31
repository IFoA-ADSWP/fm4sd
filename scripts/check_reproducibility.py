#!/usr/bin/env python3
"""Check that the committed corpus records still reproduce from their sources.

This is the `AGENTS.md` reproducibility gate as a command. It needs no payload
(`papers/` is gitignored and absent in CI), no dependency installs and no test
framework, and it makes exactly one network call: the `--index --remote` check
reads upstream's README once.

    python3 scripts/check_reproducibility.py

Three checks, each independent:

1. **Manifest equality on README-derived fields.** `--index` is re-run in a
   scratch copy of the repo and the regenerated manifest is compared with the
   committed one on the fields that are derived from `README.md`.

   The comparison is a projection, not a file diff, because `--index` on a
   payload-less tree discards fetch metadata: `reconcile()` recovers nothing
   without `papers/`, so `source`, `text_bytes`, `sha256`, the pinned
   `arxiv_rev` and `fetch_status` come back empty. That is issue #33's bug, not
   this gate's, so those fields are excluded by construction rather than allowed
   to paint every CI run red.
   The same goes for the licence/title/date records `fm4sd_licences.py` writes:
   `--index` carries them forward from the manifest it is replacing, so
   comparing them would only re-read the values under test.

2. **`--index --remote` is a read-only no-op.** It once overwrote the manifest
   with upstream's index and deleted the local actuarial category; the flag must
   leave the committed bytes untouched.

3. **Published counts agree with the manifest.** Every figure in the live
   documents (`README.md`, `references/README.md`, `PROVENANCE.md`,
   `references/summaries/README.md`, `docs/RESEARCH.md`) that describes the corpus
   is read out of the document with a phrase-anchored pattern and compared with
   the same figure derived from `references/manifest.json` — never from `papers/`,
   which CI does not have. Any other tracked document that publishes an
   `N entries, M fetched` pair fails closed rather than going unchecked.
   `fm4sd_search.py stats`, which those documents cite as the source of their
   numbers, has to agree too.

Exit status is 0 only when all three pass. Failures name the document, the
figure and both values, so the fix is obvious from the log.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FETCH = REPO / "scripts" / "fm4sd_fetch.py"
SEARCH = REPO / "scripts" / "fm4sd_search.py"
README = REPO / "README.md"
MANIFEST = REPO / "references" / "manifest.json"

# The fetcher owns the manifest's format, the "fetched" pair of statuses, the
# licence-URL field mapping and the figure definitions. Importing them is what
# stops this gate from restating contracts that can drift (#38): the delimiter,
# `manifest_figures()` and a hardcoded `licence_url` all used to be copies here.
sys.path.insert(0, str(FETCH.parent))
from fm4sd_fetch import (  # noqa: E402
    FETCHED_STATUSES,
    INDEX_INPUTS,
    LICENCE_URL_FIELDS,
    MANIFEST_DELIM,
    corpus_figures,
)

# Fields a fresh `--index` derives from README.md alone. These must match the
# committed manifest exactly, values and order.
README_FIELDS = (
    "slug",
    "arxiv_id",
    "section",
    "category",
    "subcategory",
    "citation",
    "links",
    "has_code",  # a property of `links`, so still README-derived
)

# Fields --fetch / reconcile() derive from payload under papers/. Excluded from
# check 1 because CI has no payload; check 3 still holds them to the published
# figures, so a wipe in the real tree is caught there.
PAYLOAD_FIELDS = (
    "source",
    "path",
    "text_bytes",
    "pages",
    "n_tex_files",
    "sha256",
    "fetch_status",
    "arxiv_rev",  # pinned from the export API at fetch time (#33)
)

# Documents a reader treats as current. Check 3 compares their corpus figures, and
# fails closed on any *other* tracked document that starts publishing the pair, so a
# new document forces a decision instead of becoming a blind spot. Dated plans are
# evidence, not live claims.
PLAN_PREFIX = "docs/plans/"
LIVE_DOCS = (
    "README.md",
    "references/README.md",
    "PROVENANCE.md",
    "references/summaries/README.md",
    "docs/RESEARCH.md",
)

# Fields written by fm4sd_licences.py and the fetcher's route records, carried
# forward by --index. Not derivable from the README, and the scratch copy starts
# from the committed manifest, so a comparison would be circular. `licence_url`
# and `licence_source` are one fact under two names; the mapping is the fetcher's.
CARRIED_FIELDS = (
    "licence",
    *LICENCE_URL_FIELDS,
    "shareable",
    "published",
    "redistributable",
    "arxiv_title",
)

# Published MB figures are rounded summaries. Extraction sizes move slightly
# between fetches (PDF text depends on the extractor version), so prose claims
# are compared at whole-MB granularity; every integer count is compared exactly.
MB_TOLERANCE = 0.5
# `stats` prints one decimal, so this is the rounding noise of that line only.
STATS_MB_TOLERANCE = 0.051


class Failure(Exception):
    """One check failed; the message is printed verbatim but indented."""

    def __init__(self, headline: str, detail: list[str] | None = None) -> None:
        super().__init__(headline)
        self.headline = headline
        self.detail = detail or []


# --------------------------------------------------------------------------
# Manifest helpers
# --------------------------------------------------------------------------

def load_manifest(path: Path) -> tuple[dict, list[dict], str]:
    """Return (header, entries, raw_text) for a manifest file."""
    raw = path.read_text(encoding="utf-8")
    if MANIFEST_DELIM not in raw:
        raise Failure(f"{path} is malformed: no {MANIFEST_DELIM.strip()!r} delimiter")
    head, body = raw.split(MANIFEST_DELIM, 1)
    try:
        header = json.loads(head)
        entries = json.loads(body)
    except json.JSONDecodeError as e:
        raise Failure(f"{path} is not valid JSON: {e}") from e
    if not isinstance(entries, list):
        raise Failure(f"{path}: entries section is not a list")
    return header, entries, raw


def stats_numbers(out: str) -> dict[str, float]:
    """Pull the figures `fm4sd_search.py stats` prints.

    Parsed from its output on purpose: the published counts cite `stats`, so a
    change in either has to show up here.
    """
    pats = {
        "entries": r"^entries\s+(\d+)\s*$",
        "fetched": r"^fetched\s+(\d+)\s+\((\d+) latex,\s*(\d+) pdf(?:,\s*\d+ html/xml)?\)\s*$",
        "text_mb": r"^text on disk\s+([\d.]+) MB\s*$",
    }
    found: dict[str, float] = {}
    m = re.search(pats["entries"], out, re.M)
    if not m:
        raise Failure("could not read `entries` from `fm4sd_search.py stats` output")
    found["entries"] = int(m.group(1))
    m = re.search(pats["fetched"], out, re.M)
    if not m:
        raise Failure("could not read `fetched (N latex, M pdf)` from `stats` output")
    found["fetched"], found["tex"], found["pdf"] = (int(g) for g in m.groups())
    m = re.search(pats["text_mb"], out, re.M)
    if not m:
        raise Failure("could not read `text on disk` from `stats` output")
    found["text_mb"] = float(m.group(1))
    return found


# --------------------------------------------------------------------------
# Scratch copies
# --------------------------------------------------------------------------

def make_scratch() -> Path:
    """A throwaway copy of exactly what --index / --remote read and write.

    `fm4sd_fetch.py` resolves the repo from its own path, so placing it at
    scratch/scripts/ makes the scratch directory the repo root. Nothing outside
    the copy is touched, and no payload is carried across.

    The list is checked before copying: a declared input that is missing fails
    loudly. It is a declaration, not the code that reads, so an input `--index`
    gains without a matching entry here can still go unnoticed. The check after
    the copy is what keeps that declaration honest: if `--index` gains an input,
    the gate fails here and names it, instead of comparing a manifest built
    without it (#38).
    """
    root = Path(tempfile.mkdtemp(prefix="fm4sd-repro-"))
    shutil.copy2(README, root / "README.md")
    (root / "scripts").mkdir()
    shutil.copy2(FETCH, root / "scripts" / "fm4sd_fetch.py")
    (root / "references").mkdir()
    shutil.copy2(MANIFEST, root / "references" / "manifest.json")

    missing = [rel for rel, _ in INDEX_INPUTS
               if (REPO / rel).exists() and not (root / rel).exists()]
    if missing:
        raise Failure(
            "make_scratch() did not copy every input --index declares",
            [f"missing from the scratch copy: {', '.join(missing)}",
             "fix: copy it here, keeping fm4sd_fetch.INDEX_INPUTS in step"],
        )
    return root


def run(cmd: list[str], cwd: Path, timeout: int = 180) -> subprocess.CompletedProcess:
    """Run a script from the checkout, with a timeout so CI cannot hang."""
    try:
        return subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except subprocess.TimeoutExpired as e:
        raise Failure(f"`{' '.join(cmd)}` timed out after {timeout}s") from e


def keep_scratch(root: Path) -> None:
    """Keep the scratch tree for inspection when debugging (FM4SD_CHECK_KEEP=1)."""
    if os.environ.get("FM4SD_CHECK_KEEP"):
        print(f"       scratch kept at {root}")
    else:
        shutil.rmtree(root, ignore_errors=True)


def tail(text: str, lines: int = 12) -> list[str]:
    rows = [ln for ln in text.strip().splitlines() if ln.strip()]
    return rows[-lines:]


# --------------------------------------------------------------------------
# Check 1 — manifest equality on README-derived fields
# --------------------------------------------------------------------------

def compare_entries(committed: list[dict], regenerated: list[dict]) -> list[str]:
    """Diff two entry lists on README_FIELDS, in order. Returns messages."""
    problems: list[str] = []
    if len(committed) != len(regenerated):
        problems.append(
            f"entry count: committed manifest has {len(committed)}, "
            f"a fresh --index produces {len(regenerated)}"
        )
    for i, (old, new) in enumerate(zip(committed, regenerated)):
        # Compare the slugs too: a reordered or renamed entry shifts everything
        # after it, and "field X differs on entry i" would be misleading noise.
        for field in README_FIELDS:
            a, b = old.get(field), new.get(field)
            if a != b:
                slug = old.get("slug") or new.get("slug") or f"#{i}"
                problems.append(
                    f"entry {i} ({slug}): {field}: committed {a!r} != regenerated {b!r}"
                )
    return problems


def check_manifest_matches_readme(verbose: bool) -> str:
    header, committed, _ = load_manifest(MANIFEST)

    # The header is README-derived too (`source` names the index that was
    # parsed; `count` is len(entries)); a stale count here is the "four-way
    # disagreement" the review found. Compare it against the regenerated header
    # rather than a copy of today's literals.
    if header.get("source") != "LOCAL README.md":
        raise Failure(
            f"manifest header source is {header.get('source')!r}, expected "
            "'LOCAL README.md' — the manifest was built from upstream's index"
        )
    if header.get("count") != len(committed):
        raise Failure(
            f"manifest header count is {header.get('count')!r}, "
            f"but the entries section holds {len(committed)} entries"
        )

    scratch = make_scratch()
    try:
        proc = run([sys.executable, "scripts/fm4sd_fetch.py", "--index"], scratch)
        if proc.returncode != 0:
            raise Failure(
                "`fm4sd_fetch.py --index` failed in the scratch copy",
                tail(proc.stderr or proc.stdout),
            )
        new_header, regenerated, _ = load_manifest(scratch / "references" / "manifest.json")
    finally:
        keep_scratch(scratch)

    header_problems = [
        f"header {key!r}: committed {header.get(key)!r} != regenerated {new_header.get(key)!r}"
        for key in sorted(set(header) | set(new_header))
        if header.get(key) != new_header.get(key)
    ]
    problems = header_problems + compare_entries(committed, regenerated)
    if problems:
        raise Failure(
            "references/manifest.json disagrees with a fresh --index "
            "on README-derived fields",
            [*problems[:20],
             *([f"… {len(problems) - 20} more"] if len(problems) > 20 else []),
             "fix: run `python3 scripts/fm4sd_fetch.py --index` and commit the result"],
        )

    # Anything outside the three known sets is reported, not failed: the schema
    # grows (e.g. the fetcher extension in #29) and an unknown key should be a
    # prompt to classify it, not a gate that has to be disabled.
    known = set(README_FIELDS) | set(PAYLOAD_FIELDS) | set(CARRIED_FIELDS)
    unknown = sorted({k for e in committed for k in e} - known)
    if verbose:
        print(f"       compared {', '.join(README_FIELDS)}")
        print(f"       excluded payload-derived: {', '.join(PAYLOAD_FIELDS)}")
        print(f"       excluded carried-forward: {', '.join(CARRIED_FIELDS)}")
        if unknown:
            print(f"       not compared (unclassified keys): {', '.join(unknown)}")

    return (
        f"{len(committed)} entries × {len(README_FIELDS)} fields "
        f"(payload-derived and carried-forward fields excluded)"
    )


# --------------------------------------------------------------------------
# Check 2 — `--index --remote` writes nothing
# --------------------------------------------------------------------------

def check_remote_is_read_only(verbose: bool) -> str:
    scratch = make_scratch()
    manifest = scratch / "references" / "manifest.json"
    before = manifest.read_bytes()
    try:
        proc = run([sys.executable, "scripts/fm4sd_fetch.py", "--index", "--remote"],
                   scratch, timeout=120)
        after = manifest.read_bytes()
    finally:
        keep_scratch(scratch)

    if proc.returncode != 0:
        raise Failure(
            "`fm4sd_fetch.py --index --remote` exited non-zero "
            "(upstream unreachable, or the comparison itself broke)",
            tail(proc.stderr or proc.stdout),
        )
    if before != after:
        raise Failure(
            "`--index --remote` rewrote references/manifest.json; it must only read",
            [
                f"bytes before: {len(before)}, after: {len(after)}",
                "fix: --remote must call compare_remote() and return without writing",
            ],
        )
    if verbose:
        print(f"       upstream compared, {len(before)} bytes unchanged")
    return f"manifest byte-identical ({len(before)} bytes)"


# --------------------------------------------------------------------------
# Check 3 — published counts agree with the manifest
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Claim:
    """One published figure, found in a document by its surrounding wording.

    `pattern` is phrase-anchored rather than a bare number search: prose is full
    of numbers that are *not* corpus counts (dates, "225 papers" in a historical
    sweep note, "~33 MB" of download). Every capture group is named after the
    figure it carries from `corpus_figures()`, and the comparison reads the group
    by that name -- a positional binding silently mislabels the figures when a
    pattern gains a group (#38).
    """

    doc: str
    label: str
    pattern: str
    figures: tuple[str, ...]


CLAIMS = (
    # README.md — the research-layer table a reader lands on first.
    Claim("README.md", "entries in the index",
          r"\|\s*\*\*(?P<entries>\d+)\*\*\s*\|\s*entries in the index",
          ("entries",)),
    Claim("README.md", "resolvable to arXiv",
          r"\|\s*\*\*(?P<with_id>\d+)\*\*\s*\|\s*resolvable to arXiv\s*\|",
          ("with_id",)),
    Claim("README.md", "fetched locally",
          r"\|\s*\*\*(?P<fetched>\d+)\*\*\s*\|\s*fetched locally"
          r"\s*\(\*\*(?P<tex>\d+)\*\*\s*LaTeX source,\s*\*\*(?P<pdf>\d+)\*\*\s*PDF"
          r"(?:,\s*\*\*\d+\*\*\s*HTML/XML)?\)",
          ("fetched", "tex", "pdf")),
    Claim("README.md", "quick-start corpus size",
          r"--fetch[^\n]*#\s*~(?P<text_mb>[\d.]+)\s*MB", ("text_mb",)),
    Claim("README.md", "of extracted plain text",
          r"\|\s*\*\*(?P<text_mb>[\d.]+)\s*MB\*\*\s*\|\s*of extracted plain text",
          ("text_mb",)),
    Claim("README.md", "link released code",
          r"\|\s*\*\*(?P<code>\d+)\*\*\s*\|\s*link released code", ("code",)),

    # references/README.md — the layout block and the licence note.
    Claim("references/README.md", "manifest layout entry count",
          r"COMMITTED\s*[—-]\s*(?P<entries>\d+)\s+entries", ("entries",)),
    Claim("references/README.md", "corpus text size",
          r"corpus is\s*~?\s*(?P<text_mb>[\d.]+)\s*MB of text", ("text_mb",)),
    Claim("references/README.md", "api-omitted licence count",
          r"`api-omitted` for all\s+(?P<licences>\d+)", ("licences",)),
    Claim("references/README.md", "entries not in the corpus",
          r"Why\s+(?P<skipped_total>\d+)\s+entries are not in the corpus",
          ("skipped_total",)),
    Claim("references/README.md", "captcha tally",
          r"\|\s*`skipped:unreachable:captcha`\s*\|\s*(?P<skip_captcha>\d+)",
          ("skip_captcha",)),
    Claim("references/README.md", "paywall tally",
          r"\|\s*`skipped:unreachable:paywall`\s*\|\s*(?P<skip_paywall>\d+)",
          ("skip_paywall",)),
    Claim("references/README.md", "unknown tally",
          r"\|\s*`skipped:unreachable:unknown`\s*\|\s*(?P<skip_unknown>\d+)",
          ("skip_unknown",)),
    Claim("references/README.md", "dead tally",
          r"\|\s*`skipped:unreachable:dead`\s*\|\s*(?P<skip_dead>\d+)",
          ("skip_dead",)),
    Claim("references/README.md", "not-paper tally",
          r"\|\s*`skipped:not-paper`\s*\|\s*(?P<not_paper>\d+)",
          ("not_paper",)),

    # PROVENANCE.md — the Corpus table, the enforcement record.
    Claim("PROVENANCE.md", "Entries parsed",
          r"\|\s*Entries parsed\s*\|\s*(?P<entries>\d+)", ("entries",)),
    Claim("PROVENANCE.md", "With an arXiv id",
          r"\|\s*With an arXiv id\s*\|\s*(?P<with_id>\d+)\s*\((?P<with_id_pct>\d+)%\)",
          ("with_id", "with_id_pct")),
    Claim("PROVENANCE.md", "Linking released code",
          r"\|\s*Linking released code\s*\|\s*(?P<code>\d+)", ("code",)),
    Claim("PROVENANCE.md", "Fetched locally",
          r"\|\s*Fetched locally\s*\|\s*(?P<fetched>\d+)\s*[—-]\s*(?P<tex>\d+)\s+LaTeX"
          r" source bundles,\s*(?P<pdf>\d+)\s+PDF(?:,\s*\d+\s+HTML/XML)?",
          ("fetched", "tex", "pdf")),
    Claim("PROVENANCE.md", "licence_url row count",
          r"`licence_url`\s+on\s+the\s+(?P<licence_url_rows>\d+)\s+arXiv\s+rows", ("licence_url_rows",)),
    Claim("PROVENANCE.md", "licence_source row count",
          r"`licence_source`\s+on\s+the\s+(?P<licence_source_rows>\d+)\s+route\s+rows", ("licence_source_rows",)),
    Claim("PROVENANCE.md", "Extracted text",
          r"\|\s*Extracted text\s*\|\s*(?P<text_mb>[\d.]+)\s*MB", ("text_mb",)),
)


def check_published_counts(verbose: bool) -> str:
    _, entries, _ = load_manifest(MANIFEST)
    figures = corpus_figures(entries)
    figures["text_mb"] = figures["text_bytes"] / 1e6
    figures["with_id_pct"] = (
        round(100 * figures["with_id"] / figures["entries"]) if figures["entries"] else 0
    )
    if verbose:
        print("       manifest figures: " + ", ".join(
            f"{k}={v:g}" if isinstance(v, float) else f"{k}={v}"
            for k, v in figures.items()
        ))

    texts: dict[str, str] = {}
    problems: list[str] = []
    checked = 0

    # #33's headline invariant. `arxiv_rev` is payload-derived, so check 1 cannot
    # see a regression that drops every pin; without this, deleting all 323
    # revisions would leave the gate green.
    for e in entries:
        if e.get("arxiv_id") and int(e.get("arxiv_rev") or 0) <= 0:
            problems.append(
                f"manifest: {e['slug']} has an arXiv id but no pinned revision"
            )
        if e.get("fetch_status") in FETCHED_STATUSES:
            sha = str(e.get("sha256") or "").lower()
            if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
                problems.append(
                    f"manifest: {e['slug']} is fetched but its sha256 is not a "
                    f"64-hex digest"
                )

    for claim in CLAIMS:
        if claim.doc not in texts:
            path = REPO / claim.doc
            if not path.exists():
                raise Failure(f"{claim.doc} is missing; the counts check needs it")
            texts[claim.doc] = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(claim.pattern, texts[claim.doc])
        if not m:
            problems.append(
                f"{claim.doc}: could not find the published figure for "
                f"{claim.label!r} — if the wording changed, update "
                f"scripts/check_reproducibility.py in the same commit"
            )
            continue
        names = set(m.re.groupindex)
        if names != set(claim.figures):
            problems.append(
                f"{claim.doc}: pattern for {claim.label!r} captures {sorted(names)}, "
                f"expected {sorted(claim.figures)} — name every group after its figure"
            )
            continue
        for name in claim.figures:
            raw = m.group(name)
            want = figures[name]
            # Everything is compared as a number: the figure types are ints and
            # MB floats, and guessing which from the prose was a source of noise.
            got = float(raw)
            if name == "text_mb":
                if abs(got - want) > MB_TOLERANCE:
                    problems.append(
                        f"{claim.doc}: text size says {got:g} MB, manifest says "
                        f"{want:.1f} MB (tolerance {MB_TOLERANCE:g} MB)"
                    )
            elif got != want:
                problems.append(f"{claim.doc}: {name} says {got:g}, manifest says {want}")
            checked += 1
            if verbose:
                print(f"       {claim.doc}: {name} = {got:g}")

    # A document that publishes corpus figures must not become a blind spot. Live
    # docs are compared; any other tracked doc publishing the pair fails closed, so
    # a new document forces a decision. Two exemptions only: a dated table row (a
    # corrections-log line records what was true), and a transition that joins two
    # numeric pairs ("303 entries, 340 fetched -> 383/381"). The line is flattened of
    # markdown emphasis first, and a line that mentions both words but cannot be
    # parsed fails rather than passing silently.
    listed = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=REPO, capture_output=True, text=True,
        check=False,
    ).stdout.split()
    tracked = listed or [
        str(p.relative_to(REPO)) for p in REPO.rglob("*.md")
        if ".git" not in p.parts
    ]
    dated_row = re.compile(r"^\s*\d{4}-\d{2}-\d{2}\b")
    transition = re.compile(r"(\d+)\s*entries\D{0,12}(\d+)\s*fetched\s*(?:→|->)\s*\d")
    pair = re.compile(r"(\d+)\s*entries\D{0,12}(\d+)\s*fetched")
    scanned = 0
    for doc in sorted(tracked):
        if doc.startswith(PLAN_PREFIX):
            continue
        path = REPO / doc
        if not path.exists():
            continue
        scanned += 1
        for lineno, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            flat = re.sub(r"[*_|`]", " ", line)
            if "entries" not in flat or "fetched" not in flat:
                continue
            if dated_row.match(flat.strip()) or transition.search(flat):
                continue
            m = pair.search(flat)
            if not m:
                continue
            checked += 1
            if doc not in LIVE_DOCS:
                problems.append(
                    f"{doc}:{lineno}: publishes '{m.group(1)} entries, "
                    f"{m.group(2)} fetched' but is not a live document — add it to "
                    f"LIVE_DOCS, or move it under {PLAN_PREFIX} if it is history"
                )
            elif (int(m.group(1)), int(m.group(2))) != (
                    figures["entries"], figures["fetched"]):
                problems.append(
                    f"{doc}:{lineno}: says {m.group(1)} entries / {m.group(2)} fetched, "
                    f"manifest says {figures['entries']} / {figures['fetched']}"
                )

    # `stats` is what those documents cite as the source of their numbers, so
    # it has to agree with the manifest as well.
    scratch = make_scratch()
    try:
        (scratch / "scripts" / "fm4sd_search.py").write_bytes(SEARCH.read_bytes())
        proc = run([sys.executable, "scripts/fm4sd_search.py", "stats"], scratch)
    finally:
        keep_scratch(scratch)
    if proc.returncode != 0:
        raise Failure(
            "`fm4sd_search.py stats` failed",
            tail(proc.stderr or proc.stdout),
        )
    stats = stats_numbers(proc.stdout)
    for key in ("entries", "fetched", "tex", "pdf"):
        if stats[key] != figures[key]:
            problems.append(
                f"fm4sd_search.py stats: {key} = {stats[key]:g}, "
                f"manifest says {figures[key]}"
            )
    if abs(stats["text_mb"] - figures["text_mb"]) > STATS_MB_TOLERANCE:
        problems.append(
            f"fm4sd_search.py stats: text on disk = {stats['text_mb']:g} MB, "
            f"manifest says {figures['text_mb']:.1f} MB"
        )
    if verbose:
        print(f"       stats: {stats}")

    if problems:
        raise Failure(
            "published counts disagree with the manifest",
            [*problems,
             "fix: update the document to the manifest's figures, or re-run "
             "`--index` if the index really changed"],
        )

    docs = sorted({c.doc for c in CLAIMS})
    return (f"{checked} published figures agree with the manifest across {len(docs)} "
            f"claim documents; the pair sweep read {scanned} tracked documents")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

CHECKS = (
    ("manifest matches README-derived fields", check_manifest_matches_readme),
    ("--index --remote is read-only", check_remote_is_read_only),
    ("published counts match the manifest", check_published_counts),
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="print the compared field sets and every figure")
    args = ap.parse_args()

    if not MANIFEST.exists():
        sys.exit(f"{MANIFEST} is missing; nothing to check")

    print("fm4sd reproducibility gate")
    failures = 0
    for i, (name, fn) in enumerate(CHECKS, 1):
        label = f"[{i}/{len(CHECKS)}] {name}"
        try:
            note = fn(args.verbose)
        except Failure as e:
            failures += 1
            print(f"{label} ... FAILED")
            print(f"       {e.headline}")
            for line in e.detail:
                print(f"       {line}")
        else:
            print(f"{label} ... ok — {note}")

    if failures:
        print(f"\n{failures}/{len(CHECKS)} checks failed")
        return 1
    print(f"\n{len(CHECKS)}/{len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
