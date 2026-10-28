#!/usr/bin/env python3
"""Fill in per-paper licence metadata from the arXiv API.

Licence is the reason the corpus payload stays out of git, so it needs to be a
recorded fact rather than a recollection. The arXiv API returns licence per
entry, which is authoritative and cheap -- one request per batch of ids.

Writes back into references/manifest.json, adding a "licence" key to each entry
that has an arXiv id. Entries the API cannot resolve are marked explicitly
rather than left blank, so "we do not know" never reads as "public domain".
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "references" / "manifest.json"
DELIM = "\n--- entries ---\n"

API = "https://export.arxiv.org/api/query"
BATCH = 50          # ids per request; the API prefers id_list over many queries
NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}
USER_AGENT = "fm4sd-corpus/1.0 (research; https://github.com/IFoA-ADSWP/fm4sd)"


def fetch_batch(ids: list[str], retries: int = 3) -> dict[str, dict]:
    """Return {arxiv_id: {licence, published, title}} for one batch."""
    url = f"{API}?id_list={','.join(ids)}&max_results={len(ids)}"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                xml = r.read()
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(3 * (attempt + 1))
    else:
        raise last  # type: ignore[misc]

    root = ET.fromstring(xml)
    out: dict[str, dict] = {}
    for entry in root.findall("atom:entry", NAMESPACES):
        raw_id = (entry.findtext("atom:id", "", NAMESPACES) or "").strip()
        m = re.search(r"abs/([0-9]{4}\.[0-9]{4,5})", raw_id)
        if not m:
            continue
        # The API does NOT reliably carry licence. Entries frequently have no
        # <arxiv:license> element even when the abs page shows one (verified:
        # 2511.03634 is CC-BY-4.0 on arxiv.org/abs but has no licence element
        # here). So "no element" must NOT be recorded as "no licence" -- it
        # means the API did not report one, and the real answer lives on the abs
        # page. Recording it as a definite value would be a fabricated fact.
        lic_el = entry.find("arxiv:license", NAMESPACES)
        licence = (lic_el.get("href") if lic_el is not None else None) or "api-omitted"
        out[m.group(1)] = {
            "licence": licence,
            "published": (entry.findtext("atom:published", "", NAMESPACES) or "")[:10],
            "title": " ".join((entry.findtext("atom:title", "", NAMESPACES) or "").split()),
        }
    return out


def redistributable(licence: str) -> bool:
    """Triage for 'may this payload be committed?'

    Returns True only on an explicitly permissive licence that the API actually
    reported. Everything else is False -- including "api-omitted", because an
    unreported licence is an unknown one, and unknown must not be treated as
    permission. This is a prompt to keep the file out of git, not legal advice.
    """
    l = licence.lower()
    if "api-omitted" in l or "unresolved" in l:
        return False
    if "creativecommons.org/licenses/by/" in l:
        # by/4.0 ok; by-nc, by-nd, by-sa variants are not, for our purposes.
        tail = l.rstrip("/").split("/")[-1]
        return tail in {"4.0", "3.0", "2.5", "2.0", "1.0"}
    return False


def main() -> None:
    raw = MANIFEST.read_text()
    if DELIM not in raw:
        sys.exit("manifest malformed; rerun fm4sd_fetch.py --index")
    header = raw.split(DELIM, 1)[0]
    entries = json.loads(raw.split(DELIM, 1)[1])

    ids = sorted({e["arxiv_id"] for e in entries if e.get("arxiv_id")})
    print(f"resolving licences for {len(ids)} arXiv ids")

    resolved: dict[str, dict] = {}
    for i in range(0, len(ids), BATCH):
        batch = ids[i : i + BATCH]
        try:
            got = fetch_batch(batch)
            resolved.update(got)
            print(f"  [{i + len(batch):3d}/{len(ids)}] resolved {len(got)}/{len(batch)}")
        except Exception as e:  # noqa: BLE001
            print(f"  [{i + len(batch):3d}/{len(ids)}] batch failed: {type(e).__name__}")
        time.sleep(3)  # arXiv asks for >=3s between API calls

    for e in entries:
        aid = e.get("arxiv_id")
        if not aid:
            continue
        meta = resolved.get(aid)
        if meta:
            e["licence"] = meta["licence"]
            e["licence_url"] = meta["licence"]
            e["published"] = meta["published"]
            e["arxiv_title"] = meta["title"]
            e["redistributable"] = redistributable(meta["licence"])
        else:
            e["licence"] = "unresolved"
            e["licence_note"] = "no API entry returned"
            e["redistributable"] = False

    MANIFEST.write_text(f"{header}{DELIM}{json.dumps(entries, indent=2)}\n")

    counts: dict[str, int] = {}
    for e in entries:
        if e.get("arxiv_id"):
            counts[e.get("licence", "unresolved")] = counts.get(e.get("licence", "unresolved"), 0) + 1
    print("\nlicence distribution:")
    for lic, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        mark = "REDISTRIBUTABLE" if redistributable(lic) else "local only"
        print(f"  {n:3d}  {lic:<52} {mark}")
    free = sum(1 for e in entries if e.get("redistributable"))
    print(f"\n{free}/{len(ids)} have an explicitly permissive licence reported by the API.")
    print("licence is NOT established for the rest, which is why papers/ stays")
    print("gitignored: unknown is not permission. To check a specific paper, read")
    print("the licence line on its arxiv.org/abs page.")


if __name__ == "__main__":
    main()