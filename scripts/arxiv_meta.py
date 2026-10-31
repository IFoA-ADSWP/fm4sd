#!/usr/bin/env python3
"""arxiv_meta.py — batched, cached arXiv metadata for ids you already have.

    python3 scripts/arxiv_meta.py 2102.10154 cond-mat/0011094
    python3 scripts/arxiv_meta.py --json --offline 2102.10154

Prints one record per id: id, revision, year, first author, title. The cache
lives under .cache/arxiv-meta/ (gitignored), so a repeat run costs no request.

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
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://export.arxiv.org/api/query"
BATCH = 50
PAUSE_SECONDS = 1.5  # the API's guidance is well below the fetcher's 3 req/s
RETRIES = 5
TIMEOUT = 60
CACHE = Path(os.environ.get("FM4SD_ARXIV_CACHE", ".cache/arxiv-meta"))
UA = "fm4sd-arxiv-meta/1.0 (+https://github.com/IFoA-ADSWP/fm4sd)"

ENTRY_RE = re.compile(r"<entry>(.*?)</entry>", re.S)
ABS_RE = re.compile(r"<id>\s*https?://arxiv\.org/abs/([^<\s]+)\s*</id>")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
PUBLISHED_RE = re.compile(r"<published>\s*([0-9]{4})-[0-9]{2}-[0-9]{2}")
AUTHOR_RE = re.compile(r"<author>\s*<name>([^<]+)</name>", re.S)
REV_RE = re.compile(r"^(?P<aid>.+?)v(?P<rev>\d+)$")


def cache_path(aid: str) -> Path:
    return CACHE / (aid.replace("/", "_") + ".json")


def load_cached(aid: str) -> dict | None:
    path = cache_path(aid)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def store(record: dict) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_path(record["id"]).write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")


def fetch(url: str) -> bytes:
    """GET with backoff on 429/503, honouring Retry-After when it is numeric."""
    last: Exception | None = None
    for attempt in range(RETRIES):
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            last = error
            if error.code not in (429, 503):
                raise
            retry_after = (error.headers.get("Retry-After") or "").strip()
            delay = float(retry_after) if retry_after.isdigit() else min(60.0, 2.0 ** attempt)
            print(f"arxiv_meta: HTTP {error.code}; retrying in {delay:.0f}s "
                  f"(attempt {attempt + 1}/{RETRIES})", file=sys.stderr)
            time.sleep(delay)
    raise RuntimeError(f"giving up: {last}")


def parse_feed(xml: str) -> dict[str, dict]:
    """Map id-without-version -> record. The feed echoes each id with its vN."""
    records: dict[str, dict] = {}
    for entry in ENTRY_RE.findall(xml):
        abs_match = ABS_RE.search(entry)
        title_match = TITLE_RE.search(entry)
        if not abs_match or not title_match:
            continue
        raw_id = abs_match.group(1).strip()
        rev_match = REV_RE.match(raw_id)
        if rev_match:
            aid, rev = rev_match.group("aid"), int(rev_match.group("rev"))
        else:  # an entry that never had a version suffix
            aid, rev = raw_id, 0
        published = PUBLISHED_RE.search(entry)
        author = AUTHOR_RE.search(entry)
        records[aid] = {
            "id": aid,
            "rev": rev,
            "year": int(published.group(1)) if published else None,
            "first_author": re.sub(r"\s+", " ", author.group(1)).strip() if author else "",
            "title": re.sub(r"\s+", " ", title_match.group(1)).strip(),
        }
    return records


def resolve(wanted: list[str], offline: bool) -> tuple[dict[str, dict], list[str]]:
    found: dict[str, dict] = {}
    missing: list[str] = []
    for aid in wanted:
        cached = load_cached(aid)
        if cached:
            found[aid] = cached
        else:
            missing.append(aid)
    if offline or not missing:
        return found, [aid for aid in missing]

    unresolved: list[str] = []
    for start in range(0, len(missing), BATCH):
        chunk = missing[start:start + BATCH]
        query = urllib.parse.urlencode({"id_list": ",".join(chunk)})
        try:
            records = parse_feed(fetch(f"{API}?{query}").decode("utf-8", "replace"))
        except Exception as error:  # noqa: BLE001 - reported per batch, not fatal
            print(f"arxiv_meta: batch {start // BATCH + 1} failed: {error}", file=sys.stderr)
            records = {}
        for aid in chunk:
            record = records.get(aid)
            if record:
                found[aid] = record
                store(record)
            else:
                unresolved.append(aid)
        if start + BATCH < len(missing):
            time.sleep(PAUSE_SECONDS)
    return found, unresolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ids", nargs="+", help="arXiv ids, with or without a version suffix")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of lines")
    parser.add_argument("--offline", action="store_true",
                        help="read the cache only; fail on a miss")
    args = parser.parse_args(argv)

    wanted = [REV_RE.match(aid).group("aid") if REV_RE.match(aid) else aid for aid in args.ids]
    found, missing = resolve(wanted, args.offline)

    if args.json:
        print(json.dumps([found[aid] for aid in wanted if aid in found], indent=2))
    else:
        for aid in wanted:
            record = found.get(aid)
            if record:
                print(f"{aid}\tv{record['rev']}\t{record['year']}\t"
                      f"{record['first_author']}\t{record['title']}")

    if missing:
        for aid in missing:
            print(f"arxiv_meta: could not resolve {aid}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
