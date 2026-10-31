# Plan — arxiv_meta.py (2026-10-31)

Ticket #61, retro candidate #4. Evidence: three research agents and the #33 migration hit
`export.arxiv.org` 429s on 2026-10-31; one stalled ~27 minutes, another fell back to a text
proxy. The need — verify an id, read title/first author/year, resolve the current revision —
recurs in research, triage and implementation.

## What

`scripts/arxiv_meta.py <id>...`:

- batches `id_list` (≤50 per request), one request per ~1.5 s
- exponential backoff on 429/503, honouring `Retry-After`
- one cache file per id under `.cache/arxiv-meta/` (gitignored), so a repeat run is free
- `--offline` reads cache only and fails on a miss; `--json` for machine use
- exit non-zero if any requested id could not be resolved, naming each

## Why

The rate limit is not a nuisance to retry blindly: the API's guidance is far below the 3 req/s
the fetcher uses for `/src/`. A helper that batches and paces turns a 323-id pass into seven
requests, and the cache stops three agents re-fetching the same 40 ids.

## Verification

- three ids (one legacy `cond-…` form) resolve; fields match the Atom entry
- warm cache: second run makes no request; `--offline` succeeds; `--offline` with a cold id fails
- an invalid id fails the run and is named
- `python3 -m py_compile`; `check_reproducibility.py` 3/3

## Out of scope

- Replacing the fetcher's own revision resolution (`resolve_arxiv_revs`); that is fetch-path code
  and already batched. This helper is for humans and research/implementation agents.
