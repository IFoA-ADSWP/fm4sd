# Plan — match pre-2007 (legacy) arXiv ids (#23)

## Problem

`ARXIV_RE` / `ARXIV_PDF_RE` / `ARXIV_ABS_RE` in `scripts/fm4sd_fetch.py` only match the
modern `\d{4}\.\d{4,5}` id form. The index entry `gnr` (*Organization of Growing Random
Networks*, Krapivsky & Redner 2001) links `https://arxiv.org/abs/cond-mat/0011094` — a
pre-2007 legacy id — so the parser records it as having no arXiv id. Consequences:

- `gnr` sits in the manifest as `fetch_status: "skipped:no-arxiv-id"` with no payload,
  although arXiv serves its `/abs`, `/pdf` and `/src` (gzip LaTeX source) with 200.
- Every count reasoning from "entries with no arXiv id" is off by one: the published
  figure is 50, the truth is 49 id-less + 1 misclassified.

## Change

1. **`scripts/fm4sd_fetch.py`** — extend the three arXiv-id patterns with the legacy
   form `archive[/subclass]/yymmnnn` (e.g. `cond-mat/0011094`, `math.GT/0309136`),
   shared as one `ARXIV_ID` fragment so the three regexes cannot drift. Add a
   `normalise_arxiv_id()` helper that strips any `vN` suffix so the *stored* id is always
   unversioned — the same property modern ids already have — which is what makes the
   `/abs/`, `/src/` and version-suffixed URL builders work from one stored value.
2. **`scripts/fm4sd_search.py`** — `match_year()` derives the year from the id; teach it
   the legacy `yymmnnn` tail so `gnr` is counted in `stats --by-year` and `--since`
   filters instead of silently dropping out.
3. **Manifest** — regenerate via the repo's own scripts: parse the index with the fixed
   regex (confirms `gnr` → `cond-mat/0011094`, no other id changes), then
   `fm4sd_fetch.py --fetch --only gnr` to fetch the payload and record
   `source/path/text_bytes/n_tex_files/sha256/fetch_status` through the script's own
   manifest-save path. A full `--index` rebuild is deliberately *not* used: with no
   `papers/` payload on this machine it would reset the fetch metadata of all 253
   already-fetched rows (measured: 1574 manifest lines churned) — the opposite of the
   "zero churn on modern entries" requirement. `papers/` stays gitignored; the payload
   is never committed.
4. **Counts** — recompute with `fm4sd_search.py stats` and fresh parse counts, then
   update every published figure that moves, keeping README.md, PROVENANCE.md and the
   summaries docs mutually consistent:
   - with-an-arXiv-id / fetched: 253 → 254 (248 LaTeX + 6 PDF, per the fetch output)
   - genuinely id-less / not fetchable: 50 → 49
   - extracted text: recompute from stats (33.3 MB + gnr)
   - `PROVENANCE.md` gains a dated section + corrections-log row for the fix; notes that
     `fm4sd_licences.py`'s API-id extractor is still modern-only, so `gnr` has no licence
     record yet (out of scope here, same family as #9).

## Out of scope

- Fetching the other 49 id-less entries (decision pending on #9).
- Direct-PDF-link gaps (#9).
- Re-running `fm4sd_licences.py`; its "api-omitted for all 253" record stays accurate for
  the 253 ids it actually resolved.
