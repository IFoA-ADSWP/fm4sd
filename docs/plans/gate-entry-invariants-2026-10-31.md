# Plan — gate the entry invariants (2026-10-31)

Ticket #68 (T3 of spec #65). T1 and T2 gave ids and statuses one owner each. This ticket makes the
gate enforce what those modules promise, so a regression is a red check rather than a runtime
surprise — the collision that bit T2 (a second `parse()` shadowing the id parser) is the example.

## What

- The gate's invariant block grows two assertions beside the existing pin/digest pair: **every
  stored status is one this code defines** (`recognised`), and **every arXiv id parses** under the
  one parser. Each failure names the row and the offending value.
- Delete the last old-vocabulary remnants (none remain outside `entry.py` after T2; verified by
  grep, and the check is recorded).

## Why

A status the code cannot classify currently falls through every consumer as "not fetched". The
gate is where that class of drift must surface, because there is no test harness to do it.

## Verification

- synthetic rows: `skipped:unrecognised` and `not-an-id` each turn the gate red, naming the row
- real tree: 3/3, counts unchanged, manifest byte-identical
- grep: no `FETCHED_STATUSES`, no status literals outside `entry.py`

## Out of scope

New checks beyond these two; the network and subprocess seams (#5/#6).
