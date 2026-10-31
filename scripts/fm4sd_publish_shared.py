#!/usr/bin/env python3
"""Publish the licence-verified text extracts under corpus-shared/.

`papers/` is gitignored because most of the index is not redistributable, not
because none of it is. For a few entries the manifest records a licence that
plainly allows republication (`shareable: yes`), and this script copies exactly
those entries' extracted text into a tracked directory so people who cannot run
the fetcher can still read them:

    corpus-shared/<slug>/text.txt      byte-identical to papers/<slug>/text.txt
    corpus-shared/<slug>/LICENSE.txt   title, source, licence, evidence, retrieval date
    corpus-shared/README.md            what is published, what is pending, and why

Publication is deliberately a separate step from fetching. A fetcher re-run must
not be able to widen the redistributed set on its own -- that is a licence
decision, made per entry and recorded in the manifest, and re-checking it is a
human's job (PROVENANCE.md, "Licence and sharing").

Rules this script holds to:

- `shareable: yes` **and** fetched, or nothing is written. `no` and `unknown` are
  never published; unknown is not permission.
- A shareable entry that is not fetched is reported **pending**, not as an error.
  This is `tabssldataselect` today: Springer serves a browser challenge, and the
  project never solves a CAPTCHA. It publishes on the first run after a fetch
  succeeds, with no edit here.
- Text is copied, never re-extracted, so what is published is the same bytes the
  digests were written from. If the payload's size disagrees with the manifest,
  that entry is refused rather than published stale.
- The output is deterministic and the script is idempotent: files are written
  only when their bytes differ, so a second run changes nothing. The one value
  that cannot be derived from the manifest is the retrieval date, so it is
  stamped from the payload's mtime on first publish and then read back out of the
  committed LICENSE.txt -- a re-run on another clone reproduces the committed
  bytes instead of re-dating them. It is re-stamped when the text itself changes.
- `<slug>/` is removed when the manifest no longer says `shareable: yes` (a
  licence re-check downgraded it) -- that is what keeps `corpus-shared/` exactly
  the published set. A payload that is merely absent from *this* clone never
  deletes anything: a payload-less clone must not be able to empty the directory.

Usage:
    python3 scripts/fm4sd_publish_shared.py            # write / update corpus-shared/
    python3 scripts/fm4sd_publish_shared.py --check    # report drift, write nothing
    python3 scripts/fm4sd_publish_shared.py --status   # what would be published and why

Exit status is 0 when the run is clean, including when entries are pending. It is
1 when the published set cannot be produced faithfully: a payload that disagrees
with the manifest, a fetched shareable entry with neither payload nor a published
copy, or (with --check) any difference between planned and committed files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "references" / "manifest.json"
PAPERS = REPO / "papers"
SHARED = REPO / "corpus-shared"
DELIM = "\n--- entries ---\n"

FETCHED = ("ok", "cached")

# The canonical licence text for the names the manifest records. `licence` is a
# short name ("CC BY 4.0"), not a URL, and a reader of the published extract
# should be able to reach the terms without trusting our paraphrase. An
# unrecognised name is simply left out of the header -- never guessed at.
LICENCE_URLS = {
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/legalcode",
}

# The index is a list of links: it carries a slug and a citation, not a title,
# and `fm4sd_licences.py` records `arxiv_title` for arXiv entries only. So the
# published set carries its titles here, transcribed from each paper's first page
# and checked against its extracted text. A shareable entry with no title still
# publishes under its slug, with a warning -- a missing title is noise, not a
# permission problem.
TITLES = {
    "tabpfnv2": "Accurate predictions on small data with a tabular foundation model",
    "schemapile": "SchemaPile: A Large Collection of Relational Database Schemas",
}

# Preferred order for the "Source URL" line: the version of record first, the
# payload's own location (pdf) next, the mirror last. Links not listed here
# (videos, slides, code) are skipped unless there is nothing else.
SOURCE_PRIORITY = ("doi", "arxiv", "nature", "springer", "pmlr", "neurips", "pdf", "pmc")

RETRIEVED_RE = re.compile(r"^Retrieved:\s+(\d{4}-\d{2}-\d{2})\s*$", re.M)
SHA_RE = re.compile(r"sha256\s+([0-9a-f]{64})")


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------

def load_entries() -> list[dict]:
    raw = MANIFEST.read_text(encoding="utf-8")
    if DELIM not in raw:
        sys.exit(f"{MANIFEST} is malformed (no '{DELIM.strip()}' line); run --index first")
    return json.loads(raw.split(DELIM, 1)[1])


def text_path(entry: dict) -> Path:
    return PAPERS / entry["slug"] / "text.txt"


def payload_bytes(entry: dict) -> bytes | None:
    """The entry's extracted text, or None when this clone has no payload."""
    p = text_path(entry)
    return p.read_bytes() if p.is_file() else None


def title_of(entry: dict) -> tuple[str, bool]:
    """Title for the header, and whether it is transcribed here or a fallback."""
    for key in ("arxiv_title", "title"):
        value = (entry.get(key) or "").strip()
        if value:
            return value, True
    if entry["slug"] in TITLES:
        return TITLES[entry["slug"]], True
    return entry["slug"], False


def source_url(entry: dict) -> str:
    links = entry.get("links") or {}
    for key in SOURCE_PRIORITY:
        if links.get(key):
            return links[key]
    for key in sorted(links):
        if not key.startswith("video"):
            return links[key]
    return entry.get("licence_source") or ""


# --------------------------------------------------------------------------
# Generated files
# --------------------------------------------------------------------------

def rule(title: str) -> str:
    return "=" * max(len(title), 20)


def licence_file(entry: dict, retrieved: str, text: bytes) -> bytes:
    title, _ = title_of(entry)
    licence = (entry.get("licence") or "").strip()
    rows = [
        ("Entry", entry["slug"]),
        ("Citation", (entry.get("citation") or "").strip() or "(not recorded in the index)"),
        ("Source URL", source_url(entry)),
        ("Licence", licence),
        ("Licence evidence", (entry.get("licence_source") or "").strip()),
    ]
    if licence in LICENCE_URLS:
        rows.append(("Licence text", LICENCE_URLS[licence]))
    rows.append(("Retrieved", retrieved))
    rows.append(("Published text", f"text.txt, {len(text)} bytes, "
                                   f"sha256 {hashlib.sha256(text).hexdigest()}"))

    width = max(len(k) for k, _ in rows) + 1
    lines = [title, rule(title), ""]
    lines += [f"{k + ':':<{width}} {v}" for k, v in rows]
    lines += [
        "",
        "This file is the extracted text of the paper named above, republished under",
        "the licence named above with attribution to its authors. It is not the",
        "version of record -- see the source URL for the publisher's copy -- and",
        "reuse is limited to what that licence allows.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def kb(n: int) -> str:
    return f"{n / 1024:.0f} KB"


def examples(entries: list[dict], shareable: str, n: int = 2) -> str:
    """Two representative slugs for a withheld class, so the rule is not abstract."""
    picked = [e for e in sorted(entries, key=lambda e: e["slug"])
              if e.get("shareable") == shareable][:n]
    return ", ".join(f"`{e['slug']}`" for e in picked)


def shared_readme(entries: list[dict], published: list[dict],
                  pending: list[dict]) -> bytes:
    lines = [
        "# Shared extracts",
        "",
        "Extracted text of the papers in the index whose licence plainly allows",
        "redistribution, published here so people who cannot run the fetcher can still",
        "read them. Everything else in the index stays local.",
        "",
        "Generated by `python3 scripts/fm4sd_publish_shared.py` from",
        "`references/manifest.json`; do not edit by hand. Publishing is a separate step",
        "from fetching, so a fetcher re-run cannot add a file here: an entry appears only",
        "while the manifest records `shareable: yes` **and** its payload is fetched.",
        "Policy and the licence record: [`PROVENANCE.md`](../PROVENANCE.md) →",
        "*Published extracts*. Vocabulary: [`GLOSSARY.md`](../GLOSSARY.md#shareable).",
        "",
    ]

    if published:
        lines += [
            "## Published",
            "",
            "| Entry | Title | Licence | Text |",
            "|---|---|---|---|",
        ]
        for entry in published:
            title, _ = title_of(entry)
            slug = entry["slug"]
            lines.append(
                f"| [`{slug}/`]({slug}/) | {title} | "
                f"{(entry.get('licence') or '').strip()} | "
                f"{kb(entry.get('text_bytes') or 0)} |"
            )
        lines += [
            "",
            "Each directory holds `text.txt`, the extracted text, and `LICENSE.txt`,",
            "which names the paper, its source URL, the licence and the evidence for it,",
            "and the date the text was retrieved.",
            "",
        ]

    lines += ["## Pending", ""]
    if pending:
        lines += [
            "Shareable, but with no payload yet. Nothing is published for these, and the",
            "publisher reports them rather than failing; each appears on the first run",
            "after a fetch succeeds, with no change to the script.",
            "",
            "| Entry | Licence | Status |",
            "|---|---|---|",
        ]
        for entry in pending:
            status = entry.get("fetch_status") or "(pending)"
            lines.append(
                f"| `{entry['slug']}` | {(entry.get('licence') or '').strip()} | `{status}` |"
            )
        lines.append("")
    else:
        lines += ["No shareable entry is waiting on a payload.", ""]

    lines += [
        "## Not published",
        "",
        "Every other entry stays in gitignored `papers/`, local to each clone, however",
        "easy to fetch. Open access is not the same as shareable, and unknown is not",
        "permission.",
        "",
    ]
    for value, why in (("no", "the licence forbids republication"),
                       ("unknown", "no licence could be established")):
        names = examples(entries, value)
        if names:
            lines.append(f"- `shareable: {value}` — {why}, e.g. {names}")
    lines.append("")
    return "\n".join(lines).encode("utf-8")


# --------------------------------------------------------------------------
# Plan
# --------------------------------------------------------------------------

def recorded_date(licence_path: Path, sha: str) -> str | None:
    """The retrieval date already committed for this exact text, if any.

    Tied to the text's sha256 so that re-fetching (different bytes) re-stamps the
    date, while an ordinary re-run on another clone keeps the original one.
    """
    if not licence_path.is_file():
        return None
    old = licence_path.read_text(encoding="utf-8", errors="replace")
    m_date, m_sha = RETRIEVED_RE.search(old), SHA_RE.search(old)
    if m_date and m_sha and m_sha.group(1) == sha:
        return m_date.group(1)
    return None


def plan_files(published: list[dict]) -> tuple[dict[Path, bytes], list[dict]]:
    """(relative-to-corpus-shared paths -> bytes, entries with no payload here)."""
    planned: dict[Path, bytes] = {}
    no_payload: list[dict] = []
    for entry in published:
        data = payload_bytes(entry)
        if data is None:
            no_payload.append(entry)
            continue
        want = entry.get("text_bytes") or 0
        if want and len(data) != want:
            raise ValueError(
                f"{entry['slug']}: papers/{entry['slug']}/text.txt is {len(data)} bytes "
                f"but the manifest records {want} -- the payload is stale or truncated. "
                f"Re-fetch it (`--fetch --only {entry['slug']}`) rather than publishing it."
            )
        slug = Path(entry["slug"])
        sha = hashlib.sha256(data).hexdigest()
        retrieved = (recorded_date(SHARED / slug / "LICENSE.txt", sha)
                     or datetime.fromtimestamp(text_path(entry).stat().st_mtime,
                                               tz=timezone.utc).date().isoformat())
        planned[slug / "text.txt"] = data
        planned[slug / "LICENSE.txt"] = licence_file(entry, retrieved, data)
    return planned, no_payload


def stale_dirs(entries: list[dict], published_slugs: set[str]) -> list[Path]:
    """`corpus-shared/<slug>/` for a manifest entry that is no longer published."""
    known = {e["slug"] for e in entries}
    out = []
    if not SHARED.is_dir():
        return out
    for child in sorted(SHARED.iterdir()):
        if child.is_dir() and child.name in known and child.name not in published_slugs:
            out.append(child)
    return out


def unexpected(planned: Iterable[Path]) -> list[Path]:
    """Files under corpus-shared/ that the plan does not produce.

    Nothing here should be hand-edited, so a stray file means either an old layout or a
    copy of something the plan does not licence (a PDF, say). Reported, never deleted:
    the publisher removes only what a licence decision made stale.
    """
    if not SHARED.is_dir():
        return []
    expected = set(planned)
    out = []
    for path in sorted(SHARED.rglob("*")):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        if path.relative_to(SHARED) not in expected:
            out.append(path)
    return out


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--check", action="store_true",
                    help="compare corpus-shared/ with what would be published; write nothing")
    ap.add_argument("--status", action="store_true",
                    help="print the published, pending and withheld sets; write nothing")
    args = ap.parse_args()

    if not MANIFEST.exists():
        sys.exit(f"{MANIFEST} is missing; run --index first")

    entries = load_entries()
    shareable = [e for e in entries if e.get("shareable") == "yes"]
    published = sorted((e for e in shareable if e.get("fetch_status") in FETCHED),
                       key=lambda e: e["slug"])
    pending = sorted((e for e in shareable if e.get("fetch_status") not in FETCHED),
                     key=lambda e: e["slug"])
    withheld = len(entries) - len(shareable)

    try:
        planned, no_payload = plan_files(published)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for entry in published:
        if not title_of(entry)[1]:
            print(f"warning: {entry['slug']} has no title recorded; publishing it under "
                  f"its slug — add the paper's title to TITLES", file=sys.stderr)

    # The shared README describes the manifest's published set, not what this
    # clone happens to have on disk, so it is identical everywhere -- a payload-less
    # clone (CI, a fresh checkout) cannot rewrite it into a shorter table.
    planned[Path("README.md")] = shared_readme(entries, published, pending)

    # A fetched shareable entry with no payload *and* no committed copy cannot be
    # published at all: say so instead of writing a set that is quietly short.
    unpublished = [e for e in no_payload if not (SHARED / e["slug"] / "text.txt").is_file()]

    if args.status:
        for entry in published:
            state = "payload here" if payload_bytes(entry) is not None \
                else "committed copy kept (no payload on this clone)"
            print(f"  published  {entry['slug']:<24} {state}")
        for entry in pending:
            print(f"  pending    {entry['slug']:<24} {entry.get('fetch_status')}")
        print(f"\n{len(published)} published, {len(pending)} pending, "
              f"{withheld} withheld (shareable no/unknown)")
        return 1 if unpublished else 0

    # Refuse before writing anything: publishing a README that lists an entry whose
    # text is neither on this clone nor committed would describe files that do not
    # exist, which is worse than stopping.
    if unpublished and not args.check:
        for entry in unpublished:
            print(f"error: {entry['slug']} is shareable and fetched but has no payload "
                  f"here and nothing published; cannot reproduce corpus-shared/",
                  file=sys.stderr)
        return 1

    wrote: list[str] = []
    kept: list[str] = []
    drift: list[str] = []

    for rel, data in sorted(planned.items()):
        path = SHARED / rel
        if path.is_file() and path.read_bytes() == data:
            kept.append(rel.as_posix())
            continue
        if args.check:
            drift.append(f"{path.relative_to(REPO)}: "
                         f"{'missing' if not path.exists() else 'differs from the plan'}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        wrote.append(rel.as_posix())

    for entry in no_payload:
        if entry not in unpublished:
            kept.append(f"{entry['slug']}/text.txt (payload absent on this clone)")

    removed = stale_dirs(entries, {e["slug"] for e in published})
    for path in removed:
        if args.check:
            drift.append(f"{path.relative_to(REPO)}/: still published but no longer "
                         f"shareable-and-fetched")
        else:
            shutil.rmtree(path)
            print(f"  removed    {path.relative_to(REPO).as_posix()}/  "
                  f"(no longer shareable-and-fetched)")

    # A published entry whose payload this clone lacks keeps its committed text, so both
    # files are expected even though the plan could not produce them here.
    expected = set(planned) | {
        Path(e["slug"]) / name
        for e in no_payload if e not in unpublished
        for name in ("text.txt", "LICENSE.txt")
    }
    for path in unexpected(expected):
        rel = path.relative_to(REPO).as_posix()
        if args.check:
            drift.append(f"{rel}: not produced by the plan")
        else:
            print(f"  warning    {rel} is not produced by the plan; left in place",
                  file=sys.stderr)

    for entry in published:
        data = planned.get(Path(entry["slug"]) / "text.txt")
        size = f"{len(data)} B" if data else "payload absent"
        print(f"  published  {entry['slug']:<24} {size:<16} "
              f"{(entry.get('licence') or '').strip()}")
    for entry in pending:
        print(f"  pending    {entry['slug']:<24} {entry.get('fetch_status')} -- "
              f"no payload, not published; appears after a successful fetch")
    print(f"\n{len(published)} published, {len(pending)} pending, {withheld} withheld "
          f"(shareable no/unknown)")

    if args.check:
        if unpublished:
            for entry in unpublished:
                drift.append(f"corpus-shared/{entry['slug']}/: expected (shareable and "
                             f"fetched) but no payload here and no committed copy")
        if drift:
            print("\ncorpus-shared/ is out of date:", file=sys.stderr)
            for line in drift:
                print(f"  {line}", file=sys.stderr)
            print("\nfix: python3 scripts/fm4sd_publish_shared.py", file=sys.stderr)
            return 1
        print(f"\n--check: {len(kept)} files match the plan, nothing to write")
        return 0

    if wrote:
        print(f"\nwrote {len(wrote)} file(s): " + ", ".join(wrote))
    else:
        print("\nnothing to write: corpus-shared/ already matches the plan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
