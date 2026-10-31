# Plan — two clients onto net.get (2026-10-31)

Ticket #74 (T2 of spec #72). The metadata helper and the licence pass each carry their own retry
loop; both are single-shot clients with no threads, which makes them the safe first migration.

## What

- `arxiv_meta.fetch()` becomes a call to `net.get()` with its own user agent, timeout and attempt
  count. Its 1.5 s pause between batches stays where it is (between batches, not per request).
- `fm4sd_licences.fetch_batch()` keeps its batching, its `api-omitted` rule and its batch-failure
  report, but loses its own loop; the 3 s pause between batches stays.
- Behaviour: same URLs, same parsing, same records. The retry **status set** does move: the
  licence pass's blanket retry becomes 408/429/5xx-retryable with 4xx final, and the metadata
  helper's 429/503 widens to 408 + all 5xx. Spacing keeps each script's floor through the pace
  adapter (3 s for licences, the existing batch pause for metadata).

## Why

Their loops are the two that disagree most: one honours `Retry-After`, the other retries
everything. Moving them first proves `net.get` against real callers before the corpus builder's
limiters and threads are involved.

## Verification

- `arxiv_meta.py` resolves an id live, and `--offline` still serves the cache.
- A stubbed `net.get` proves `fetch_batch` still parses a response and still names a batch failure.
- The licence fixture still returns `api-omitted` for an entry with no licence element.
- Gate 3/3; `references/manifest.json` unchanged.

## Out of scope

The corpus builder (#75); changing any pace or batching; the gate's subprocess seam.
