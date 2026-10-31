# Plan — statuses constructed and read in one place (2026-10-31)

Ticket #67 (T2 of spec #65). Evidence: `FETCHED_STATUSES` plus five f-string constructors and
four decoders; "what counts as fetched" is re-decided per consumer.

## What

- `entry.py` grows the status half: a `Status` value with `is_fetched`, `reason`, `recognised`;
  constructors `fetched()`, `cached()`, `absent(reason)`, `failed(stage, kind)`, `pending()`;
  a `parse()` for stored strings. The reason vocabulary is closed and validated.
- Constructors used by the fetcher; readers (`corpus_figures`, publisher, search, the gate) ask
  `is_fetched` / `reason` instead of comparing strings.
- Stored values are unchanged, so the manifest stays byte-identical.

## Why

An unrecognised status should be an explicit state, not silently "not fetched". Constructing
through one module makes a new reason one declaration; decoding through it stops the fourth
copy of the fetched pair.

## Verification

- fixtures: every stored status parses to the same is-fetched/reason the string checks gave;
  constructors round-trip to the stored strings; an unknown string is `recognised=False`
- `--index` byte-identical and idempotent; gate 3/3; counts unchanged
- no consumer compares `ok`/`cached`/`skipped:` literals after the change

## Out of scope

Gate invariants and deleting the last constants (T3); new statuses or reasons.
