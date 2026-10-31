# Plan — corpus scope and vocabulary (2026-10-31)

Ticket #31, following the scope decision on #9.

## What

- `PROVENANCE.md`: a **Corpus scope** section — the in-scope route families, the permanent
  no-scraping rule, the reason-flavoured status vocabulary, and the licence/shareable policy
  (manifest fields; `corpus-shared/` publishing only for `shareable: yes`; unknown is never
  permission). No figures restated; the Corpus table and `fm4sd_search.py stats` stay the
  record.
- `GLOSSARY.md` (new): entry / index / payload / route / shareable / status, plus why "the
  corpus" is ambiguous.
- One pointer added to the older "Scope limit: arXiv-only" paragraph, which the new section
  supersedes; without it the file states the retired policy as current fifty lines above the
  replacement.

## Why

The decision lived only on a ticket. The repo's rule is that every corpus claim resolves to
`PROVENANCE.md`, and "the corpus" was being used for three different objects.

## Verification

- No volatile figures in the new prose (route families are named, not counted); no change to
  the Corpus table, README or any script.
- The two permission fields (`shareable` from route fetches, `redistributable` from the
  licence script) are defined against each other so they cannot drift silently.

## Out of scope

Implementation of the fetcher/statuses (#29), CI (#32), revision pinning (#33), publishing
extracts (#30). One PROVENANCE touch to the superseded paragraph is noted above rather than
left as a contradiction.
