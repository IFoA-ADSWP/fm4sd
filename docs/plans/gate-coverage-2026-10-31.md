# Plan — gate reads every document that publishes corpus figures (2026-10-31)

Ticket #55, from retro candidate #2. Evidence: two stale figures survived a green gate on
2026-10-31 — `README.md`'s `# ~44 MB` quick-start comment and `references/summaries/README.md`'s
`383 entries, 340 fetched` pointer. Both were published figures; neither document was in the
checker's claim set.

## What

1. A `Claim` for the summaries coverage line (`N entries, M fetched`).
2. A `Claim` for the README quick-start size comment (`# ~N MB`).
3. A sweep over a small `LIVE_DOCS` list for any `N entries, M fetched` pair that disagrees
   with the manifest, so a new document that publishes the pair is covered without a new
   `Claim`. Exempt dated history: corrections-log rows and `→` transitions.

## Why

The gate's purpose is that published figures cannot drift silently. A claim set that enumerates
documents makes every new document a blind spot, and the blind spot is invisible: the gate stays
green. Two instances in one day is enough to treat enumeration as the bug.

## Verification (red, then green)

- Scratch copy with `383 entries, 340 fetched` in the summaries line → check 3 fails, naming file
  and both values.
- Scratch copy with `# ~44 MB` in README → check 3 fails.
- Real tree → 3/3.
- Dated history (corrections-log rows, `→` transitions, `docs/plans/`) → no false positive.

## Out of scope

- Markdown linting, link checking, or any doc-wide number scan: many documents legitimately
  publish non-corpus counts (28 actuarial entries, 12 digests). Only the corpus-figure pair and
  the corpus size are asserted.
- Branch protection (admin), retro candidates #3–#6.
