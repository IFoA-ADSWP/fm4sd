# Plan — fixes for the 2026-10-29 review findings

Review of this repo at `ed57b2b` produced 14 findings. Seven are small, self-contained and
safe to fix now; the other seven are filed as issues for a decision first (index drift,
non-arXiv fetching, stale docstrings, missing CI).

This plan covers the seven being fixed here: **#1, #2, #3, #5, #6, #8, #9**.

## What is changing and why

### #1 — `--index` destroys licence metadata (`scripts/fm4sd_fetch.py`)

`cmd_index()` rebuilds every entry from a fresh `Paper`, and `dump_manifest()` only writes
`Paper` fields. Anything `fm4sd_licences.py` wrote afterwards — `licence`, `licence_url`,
`published`, `arxiv_title`, `redistributable` — is therefore dropped by the next `--index`,
which is the first command the README tells you to run. Reproduced: 253 licence records → 0.

**Change:** give `Paper` an `extra` dict that `to_json()` flattens, and have `cmd_index()`
carry forward any prior-manifest key that is not a `Paper` field, but only when the entry's
arXiv id is unchanged (licence, title and published date are all derived from the id, so a
corrected link must not inherit them). Fetch metadata keeps coming from `reconcile()` /
payload on disk — that part was already correct.

**Why `extra` rather than a fixed allowlist:** the next metadata key anyone adds to
`fm4sd_licences.py` would otherwise need a second patch here.

### #2 — `--index --remote` overwrites the manifest (`scripts/fm4sd_fetch.py`)

Documented as reading upstream "for comparison", it writes `MANIFEST`. Reproduced: 303 → 355
entries, all 28 actuarial entries deleted, licence fields deleted.

**Change:** `--remote` parses upstream and prints a comparison against the local README —
counts, upstream-only slugs, local-only slugs — then returns without writing. The flag
becomes read-only, which is what `--remote` has always implied.

### #3 — three documents state three different corpus sizes

`README.md` and `references/README.md` still say 275 entries / 225 fetched / 30.5 MB; the
manifest and `PROVENANCE.md` say 303 / 253 / 33.3 MB. `AGENTS.md` makes agreement between
manifest, summaries and PROVENANCE the repo's gate, and the file a reader lands on is the
stale one.

**Change:** correct the research-layer table in `README.md`, the layout and usage numbers in
`references/README.md`, and the `api-omitted` count in `PROVENANCE.md` (225 → 253; that
count grew with the actuarial batch). Digest and sweep counts come from
`references/summaries/README.md` and `SWEEPS.md` (12 digest documents, Q1–Q5 plus A2–D2).

Numbers describing *the sweep as run* ("a sweep across 225 papers") are left alone — they
were correct at the time and are load-bearing for the negative result.

### #5 — `citation` is empty for every entry (`scripts/fm4sd_fetch.py`)

`CITATION_RE` requires an escaped `\[...\]`. Neither this README nor upstream's uses
escaping: 288 plain `[nie et al. 2023]`, zero escaped. Every manifest ever committed has
`citation: ""`, and `fm4sd_search.py list` prints a permanently blank column.

**Change:** strip `[text](url)` links out of the entry first, then match an optional
backslash around the brackets. Stripping links first is what keeps `[arxiv]` and `[video]`
from being mistaken for a citation.

### #6 — the actuarial sub-headings are invisible to the parser (`scripts/fm4sd_fetch.py`)

The severity / frequency / tail groupings are indented `##` headings inside a list item.
`H2_RE` is anchored at `^` and `CATEGORY_RE` needs a `- ` bullet, so neither matches, and all
28 actuarial entries get `subcategory: ""` — unlike every other nested category.

**Change:** recognise an indented `##` as an entry on the category stack at its own indent
(the same mechanism as nested bullets), truncated at the first `:` so the value stays short
enough to filter on: `severity`, `frequency and count models`, `tail metrics, quantiles,
reserving`. Also add `--subcategory` to `fm4sd_search.py list` and `grep`, since a stored
field nothing can query is not much of a fix.

### #8 — `--status` calls 50 permanently unfetchable entries "(pending)" (`scripts/fm4sd_fetch.py`)

`fetch_one()`'s `skipped:no-arxiv-id` branch is unreachable — `cmd_fetch()` filters entries
without an arXiv id before submitting them — so those entries never get a status at all.

**Change:** stamp `skipped:no-arxiv-id` at index time, where the fact (no arXiv id) is
known. `--status` already prints whatever status it finds, so it will now say so. If a
payload appears for one of them, `reconcile()` still credits it as fetched.

### #9 — `grep`'s summary line miscounts (`scripts/fm4sd_search.py`)

With 4 matching papers and `--max-results 2` it prints `1 papers matched, showing 2`. The
unique-paper set is only built from *displayed* snippets, and `shown` counts snippets while
the label says papers.

**Change:** count matched papers across all results and report snippets as snippets.

## What is deliberately not changing

- **Payload handling, licences, and the gitignore.** No position on licences moves; the
  `extra` carry-forward is about not losing recorded facts, not about what they mean.
- **The upstream index itself** — `AGENTS.md` forbids rewriting it, and nothing here does.
- **PROVENANCE's corrections log and docstrings (#11–#13)** and **the 80-entry upstream
  drift (#4)** — filed as issues, they need a decision rather than an edit.
- **`PROVENANCE.md:36`'s list of reasons entries are unfetchable** is known to omit
  `openreview`, the largest group. That is finding #7's territory (non-arXiv fetching) and is
  left for it rather than half-corrected here.

## Verification

Per `AGENTS.md`, the gate is reproducibility, not tests:

1. `python3 scripts/fm4sd_fetch.py --index` in a scratch copy — confirms the manifest it
   produces agrees with the one committed here on every README-derived field.
2. The same, with a payload on disk — confirms fetch metadata survives `--index`.
3. `python3 scripts/fm4sd_fetch.py --index --remote` — confirms it prints a comparison and
   leaves `references/manifest.json` byte-identical.
4. `python3 scripts/fm4sd_search.py stats` / `list` / `grep` — confirms counts, the
   citation and subcategory columns, and the corrected summary line.
5. Re-read `references/manifest.json`, `references/summaries/` and `PROVENANCE.md` for
   agreement, and state what was checked.
