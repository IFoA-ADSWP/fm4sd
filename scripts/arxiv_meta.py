#!/usr/bin/env python3
"""arxiv_meta.py — batched, cached arXiv metadata for ids you already have.

    python3 scripts/arxiv_meta.py 2102.10154 cond-mat/0011094
    python3 scripts/arxiv_meta.py --json --offline 2102.10154 --refresh

Prints one record per id: id, revision, publication year, first author, title.
The cache lives under .cache/arxiv-meta/ (gitignored, repo-root anchored); each
record carries `fetched_at`, and a cached record older than --max-age is
refetched rather than replayed. `--offline` reads the cache and says how old the
records are.

Why this exists: export.arxiv.org rate-limits hard (#61). The fetcher's own
resolver batches for the corpus build; research and triage agents kept hand-
rolling single-id queries and drawing 429s.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse

import net
from pathlib import Path

import entry as entry_vocab

API = "https://export.arxiv.org/api/query"
BATCH = 50
PAUSE_SECONDS = 1.5  # the API's guidance is well below the fetcher's 3 req/s
RETRIES = 5
TIMEOUT = 60
DEFAULT_MAX_AGE = 24 * 3600
REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(os.environ.get("FM4SD_ARXIV_CACHE") or REPO_ROOT / ".cache" / "arxiv-meta")
UA = "fm4sd-arxiv-meta/1.0 (+https://github.com/IFoA-ADSWP/fm4sd)"

ENTRY_RE = re.compile(r"<entry>(.*?)</entry>", re.S)
ABS_RE = re.compile(r"<id>\s*https?://arxiv\.org/abs/([^<\s]+)\s*</id>")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
PUBLISHED_RE = re.compile(r"<published>\s*(\d{4})-(\d{2})-(\d{2})")
UPDATED_RE = re.compile(r"<updated>\s*(\d{4}-\d{2}-\d{2})")
AUTHOR_RE = re.compile(r"<author>\s*<name>([^<]+)</name>", re.S)


def canon(raw: str) -> str:
    """Validated, version-stripped, lowercase id — the cache and lookup key."""
    try:
        return entry_vocab.parse(raw).key
    except entry_vocab.IdError as error:
        raise SystemExit(f"arxiv_meta: {error}") from error


def cache_path(aid: str) -> Path:
    return CACHE / (urllib.parse.quote(aid, safe="") + ".json")


def load_cached(aid: str) -> dict | None:
    path = cache_path(aid)
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return record if isinstance(record, dict) and "fetched_at" in record else None


def store(record: dict) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_path(record["id"]).write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")


def age(record: dict) -> float:
    return max(0.0, time.time() - float(record.get("fetched_at") or 0))


def human_age(seconds: float) -> str:
    if seconds < 90:
        return f"{seconds:.0f}s"
    if seconds < 5400:
        return f"{seconds / 60:.0f}m"
    return f"{seconds / 3600:.1f}h"


def fetch(url: str) -> bytes:
    """GET through the shared client, with this tool's user agent and patience."""
    return net.get(url, user_agent=UA, timeout=TIMEOUT, attempts=RETRIES,
                   log=lambda message: print(message, file=sys.stderr))


def parse_feed(xml: str) -> dict[str, dict]:
    """Map canonical id -> record. The feed echoes each id with its current vN."""
    records: dict[str, dict] = {}
    for entry in ENTRY_RE.findall(xml):
        abs_match = ABS_RE.search(entry)
        title_match = TITLE_RE.search(entry)
        if not abs_match or not title_match:
            continue
        try:
            parsed = entry_vocab.parse(abs_match.group(1))
        except entry_vocab.IdError:
            continue  # one unparseable entry must not kill the feed
        aid, version = parsed.key, parsed.revision
        published = PUBLISHED_RE.search(entry)
        updated = UPDATED_RE.search(entry)
        author = AUTHOR_RE.search(entry)
        records[aid] = {
            "id": aid,
            "rev": version,
            "year": int(published.group(1)) if published else None,
            "updated": updated.group(1) if updated else None,
            "first_author": re.sub(r"\s+", " ", author.group(1)).strip() if author else "",
            "title": re.sub(r"\s+", " ", title_match.group(1)).strip(),
            "fetched_at": time.time(),
        }
    return records


def resolve(wanted: list[str], *, offline: bool, max_age: float, refresh: bool):
    """Return (records, unresolved, cached_count). Cached records are replayed
    only when fresh enough (or offline), and their age is reported either way."""
    found: dict[str, dict] = {}
    cached_count = 0
    todo: list[str] = []
    for aid in wanted:
        record = None if refresh else load_cached(aid)
        if record and (offline or age(record) <= max_age):
            found[aid] = record
            cached_count += 1
            # Offline replays a cache that may be older than --max-age; say so,
            # because `rev` and `year` are only true as of `fetched_at`.
            if offline and age(record) > max_age:
                print(f"arxiv_meta: {aid} served from a cache {human_age(age(record))} "
                      f"old (--max-age {human_age(max_age)}); revision may be behind",
                      file=sys.stderr)
        else:
            todo.append(aid)
    if offline:
        return found, todo, cached_count

    unresolved: list[str] = []
    for start in range(0, len(todo), BATCH):
        chunk = todo[start:start + BATCH]
        query = urllib.parse.urlencode({"id_list": ",".join(chunk)})
        try:
            records = parse_feed(fetch(f"{API}?{query}").decode("utf-8", "replace"))
        except Exception as error:  # noqa: BLE001 - one bad batch must not kill the run
            print(f"arxiv_meta: batch {start // BATCH + 1} failed: {error}", file=sys.stderr)
            records = {}
        for aid in chunk:
            record = records.get(aid)
            if record:
                found[aid] = record
                store(record)
            else:
                unresolved.append(aid)
        if start + BATCH < len(todo):
            time.sleep(PAUSE_SECONDS)
    return found, unresolved, cached_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ids", nargs="+", help="arXiv ids, with or without a version suffix")
    parser.add_argument("--json", action="store_true", help="emit a JSON envelope")
    parser.add_argument("--offline", action="store_true", help="read the cache only")
    parser.add_argument("--refresh", action="store_true", help="ignore cached records")
    parser.add_argument("--max-age", type=float, default=DEFAULT_MAX_AGE,
                        help=f"seconds a cached record stays usable (default {DEFAULT_MAX_AGE})")
    args = parser.parse_args(argv)

    seen: list[str] = []
    for raw in args.ids:
        aid = canon(raw)
        if aid not in seen:
            seen.append(aid)

    found, missing, cached = resolve(
        seen, offline=args.offline, max_age=args.max_age, refresh=args.refresh)

    if args.json:
        print(json.dumps({
            "records": [found[aid] for aid in seen if aid in found],
            "missing": missing,
        }, indent=2))
    else:
        for aid in seen:
            record = found.get(aid)
            if record:
                print(f"{aid}\tv{record['rev']}\t{record['year']}\t"
                      f"{record['first_author']}\t{record['title']}")
        if cached:
            print(f"arxiv_meta: {cached}/{len(seen)} served from cache", file=sys.stderr)

    if missing:
        for aid in missing:
            print(f"arxiv_meta: could not resolve {aid}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
