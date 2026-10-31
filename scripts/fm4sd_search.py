#!/usr/bin/env python3
"""Query the local paper corpus and grep across its text.

The corpus exists to answer specific questions, not to be read end to end. This
is the read side: a manifest query, a full-text search, and a context extractor
that returns passages sized for a model.

Examples
--------
    python3 scripts/fm4sd_search.py list --has-code --since 2025
    python3 scripts/fm4sd_search.py show nanotabpfn
    python3 scripts/fm4sd_search.py grep "zero.inflation" --context 2
    python3 scripts/fm4sd_search.py grep "hurdle" --limit 5 --min-hits 3
    python3 scripts/fm4sd_search.py stats
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAPERS = REPO / "papers"
MANIFEST = REPO / "references" / "manifest.json"

# The fetcher owns the manifest format and the published-figure definitions, so
# `stats` prints from them rather than restating them (#38). Resolved from REPO
# so the import works however this script is launched.
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))
from fm4sd_fetch import FETCHED_STATUSES, corpus_figures  # noqa: E402
import entry as entry_vocab  # noqa: E402
import manifest as manifest_store  # noqa: E402
import payload as payload_store  # noqa: E402

# Sentence-ish split for --context. Avoids depending on nltk/spacy.
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")


def load() -> list[dict]:
    try:
        _, entries, _ = manifest_store.read(MANIFEST)
    except manifest_store.ManifestError as error:
        sys.exit(f"{error}; rerun fm4sd_fetch.py --index")
    return entries


def text_path(entry: dict) -> Path | None:
    """The entry's text, using the same payload rule as the corpus builder."""
    if not entry.get("path"):
        return None
    state = payload_store.read(REPO / "papers", entry["slug"])
    return state.directory / payload_store.TEXT if state.ready else None


def cmd_list(entries: list[dict], args) -> None:
    rows = []
    for e in entries:
        if args.has_code and not e.get("has_code"):
            continue
        if args.section and e.get("section") != args.section:
            continue
        if args.category and e.get("category") != args.category:
            continue
        if args.subcategory and e.get("subcategory") != args.subcategory:
            continue
        if args.local and e.get("fetch_status") not in FETCHED_STATUSES:
            continue
        if args.missing and e.get("fetch_status") in FETCHED_STATUSES:
            continue
        year = match_year(e.get("arxiv_id", ""))
        if args.since and (year is None or year < args.since):
            continue
        if args.until and (year is None or year > args.until):
            continue
        rows.append(e)

    for e in rows:
        flags = "".join([
            "C" if e.get("has_code") else " ",
            "L" if e.get("fetch_status") in FETCHED_STATUSES else " ",
        ])
        print(f"{flags} {e['arxiv_id'] or '--------':>12}  {e['slug'][:38]:<38}  "
              f"{e.get('section', ''):<7} {e.get('category', ''):<14} {e.get('citation', '')}")
    print(f"\n{len(rows)} of {len(entries)} entries")


def match_year(arxiv_id: str) -> int | None:
    """The first-submission year encoded in the id (YYMM), via the one parser (#66)."""
    try:
        return entry_vocab.parse(arxiv_id).year
    except entry_vocab.IdError:
        return None


def cmd_show(entries: list[dict], slug: str, args) -> None:
    match = [e for e in entries if e["slug"] == slug or e.get("arxiv_id") == slug]
    if not match:
        sys.exit(f"no entry named {slug}")
    e = match[0]

    print(json.dumps({k: v for k, v in e.items()
                      if k not in ("links",)}, indent=2))
    if e.get("links"):
        print("\nlinks:")
        for k, v in e["links"].items():
            print(f"  {k:<12} {v}")

    path = text_path(e)
    if not path:
        print(f"\nnot fetched locally ({e.get('fetch_status') or 'pending'})")
        return

    body = path.read_text(encoding="utf-8", errors="replace")
    print(f"\n{len(body):,} chars of text at {path.relative_to(REPO)}")
    if args.text:
        print("\n" + body)


def cmd_grep(entries: list[dict], args) -> None:
    pattern = re.compile(args.pattern, re.I)
    words = [w for w in re.findall(r"[a-z0-9_]+", args.pattern.lower()) if len(w) > 2]

    found = []
    for e in entries:
        # Scoping matters: without it a term like "context" matches the whole
        # corpus and the sweep returns noise instead of the papers on topic.
        if args.category and e.get("category") != args.category:
            continue
        if args.subcategory and e.get("subcategory") != args.subcategory:
            continue
        if args.section and e.get("section") != args.section:
            continue
        if args.has_code and not e.get("has_code"):
            continue
        if args.since and (match_year(e.get("arxiv_id", "")) or 0) < args.since:
            continue

        path = text_path(e)
        if not path:
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

        hits = [i for i, ln in enumerate(lines) if pattern.search(ln)]
        if not hits:
            continue

        # min_hits keeps the signal-to-noise up: one incidental match in a
        # 400-page bundle is noise, five are a claim worth reading.
        if args.min_hits > 1 and len(hits) < args.min_hits:
            continue

        # Sample hits evenly across the file rather than taking the first N.
        # Papers front-load preamble, TOC and author lists, so the first matches
        # are almost always the least informative ones.
        if len(hits) <= args.limit:
            picked = hits
        else:
            step = len(hits) / args.limit
            picked = [hits[int(i * step)] for i in range(args.limit)]

        for i in picked:
            lo, hi = max(0, i - args.context), min(len(lines), i + args.context + 1)
            snippet = "\n".join(lines[lo:hi])
            found.append((len(hits), e, i, snippet))

    # Highest hit-count first: a paper that keeps coming back is the one on topic.
    found.sort(key=lambda t: (-t[0], t[1]["slug"]))

    shown = 0
    seen_papers: set[str] = set()
    for n_hits, e, line_no, snippet in found:
        if shown >= args.max_results:
            break
        marker = "  " if e["slug"] in seen_papers else "->"
        seen_papers.add(e["slug"])
        print(f"\n{marker} {e['slug']}  [{e['arxiv_id']}]  {n_hits} hits  line {line_no}")
        print("    " + snippet.replace("\n", "\n    ")[: args.max_chars])
        shown += 1

    # Counted across every result, not just the ones printed: with --max-results 2
    # and four matching papers this used to report "1 papers matched, showing 2",
    # because the paper set was only built inside the capped display loop and
    # `shown` counted snippets while the label said papers.
    matched = {t[1]["slug"] for t in found}
    print(f"\n--- {len(matched)} papers matched, showing {shown} of {len(found)} snippets ---")
    if words:
        print(f"pattern terms: {', '.join(words)}")

    # Guard the most expensive mistake this tool can make: reporting a null result
    # that is an artefact of the search, not a fact about the literature. It has
    # already happened once -- `--min-hits 3` discarded every paper that mentions
    # zero-inflation (they contain 1-2 hits each), and the null was published as
    # "nothing in the index addresses this".
    if not seen_papers:
        print("\n!! ZERO MATCHES. Before reporting this as a negative result, check:")
        print("   - morphology: try a stem, e.g. 'zero.?inflat' not 'zero-inflation'")
        print("   - threshold: a concept mentioned once will not survive --min-hits 3")
        if args.min_hits > 1:
            print(f"   - you set --min-hits {args.min_hits}; re-run with 1 to be sure")
        if args.category or args.subcategory or args.section or args.since or args.has_code:
            print("   - you scoped the search; re-run unscoped to be sure")
        print("   A null from a scoped or thresholded search is a fact about the")
        print("   query, not about the corpus.")


def cmd_stats(entries: list[dict]) -> None:
    # One definition of the figures, shared with the reproducibility gate.
    figures = corpus_figures(entries)

    print(f"entries        {figures['entries']}")
    print(f"fetched        {figures['fetched']}  ({figures['tex']} latex, "
          f"{figures['pdf']} pdf, {figures['html']} html/xml)")
    print(f"text on disk   {figures['text_bytes'] / 1e6:.1f} MB")

    # Status is the reason vocabulary, not just "missing": the corpus counts in
    # README/PROVENANCE are checked against this block, and `skipped:no-arxiv-id`
    # is retired (#29).
    status: dict[str, int] = {}
    for e in entries:
        s = e.get("fetch_status") or "(pending)"
        status[s] = status.get(s, 0) + 1
    print("\nby status:")
    for s, n in sorted(status.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {s:<32} {n}")

    # Licence records exist for entries that are not fetched too (an assessed
    # paper behind a challenge), so this counts records, not payloads.
    share = [e for e in entries if e.get("shareable")]
    if share:
        print("\nshareable (licence record):")
        for s in ("yes", "no", "unknown"):
            n = sum(1 for e in share if e.get("shareable") == s)
            if n:
                print(f"  {s:<24} {n}")

    def tally(key):
        out: dict[str, int] = {}
        for e in entries:
            out[e.get(key) or "(none)"] = out.get(e.get(key) or "(none)", 0) + 1
        for k, v in sorted(out.items(), key=lambda kv: -kv[1])[:12]:
            print(f"  {k:<24} {v}")

    print("\nby section:")
    tally("section")
    print("\nby category:")
    tally("category")

    years: dict[int, int] = {}
    for e in entries:
        y = match_year(e.get("arxiv_id", ""))
        if y:
            years[y] = years.get(y, 0) + 1
    print("\nby year:  " + "  ".join(f"{y}:{n}" for y, n in sorted(years.items())))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="query the manifest")
    p.add_argument("--has-code", action="store_true", help="only entries with released code")
    p.add_argument("--section")
    p.add_argument("--category")
    p.add_argument("--subcategory", help="restrict to a sub-heading (e.g. forecasting, severity)")
    p.add_argument("--local", action="store_true", help="only fetched locally")
    p.add_argument("--missing", action="store_true", help="only NOT fetched")
    p.add_argument("--since", type=int, help="year >= N")
    p.add_argument("--until", type=int, help="year <= N")

    p = sub.add_parser("show", help="metadata, links, and optionally full text")
    p.add_argument("slug")
    p.add_argument("--text", action="store_true", help="dump the whole extracted text")

    p = sub.add_parser("grep", help="full-text search across the local corpus")
    p.add_argument("pattern")
    p.add_argument("--category", help="restrict to a category (e.g. tabular, causal)")
    p.add_argument("--subcategory", help="restrict to a sub-heading (e.g. forecasting, severity)")
    p.add_argument("--section", help="restrict to papers / queue")
    p.add_argument("--since", type=int, help="only papers from year >= N")
    p.add_argument("--has-code", action="store_true", help="only papers with released code")
    p.add_argument("--context", type=int, default=1, help="lines either side")
    p.add_argument("--limit", type=int, default=3, help="hits shown per paper")
    p.add_argument("--max-results", type=int, default=10, help="papers shown in total")
    p.add_argument("--min-hits", type=int, default=1, help="require N hits in a paper")
    p.add_argument("--max-chars", type=int, default=600)

    sub.add_parser("stats", help="corpus overview")

    args = ap.parse_args()
    entries = load()
    if not entries:
        sys.exit("manifest empty; rerun fm4sd_fetch.py --index")

    if args.cmd == "stats":
        cmd_stats(entries)
    elif args.cmd == "show":
        cmd_show(entries, args.slug, args)
    else:
        {"list": cmd_list, "grep": cmd_grep}[args.cmd](entries, args)


if __name__ == "__main__":
    main()