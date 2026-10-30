# Plan — merge upstream/main (2026-10-30)

Decision #17, delivery ticket #22. Evidence: `research/upstream-relationship.md` on branch
`research/upstream-relationship`.

## What

1. `git merge upstream/main` (`13b8240`) into `main`. Conflict-free by construction: the
   fork's whole diff against merge-base `62382d2` is the research preamble plus the appended
   28-entry actuarial category; no shared entry was edited.
2. Rebuild the payload (`--fetch`) and regenerate `references/manifest.json` (`--index`) for
   the merged 383-entry index. Payload stays gitignored; only the manifest changes.
3. Record the relationship and drift trigger in `docs/RESEARCH.md` (new) and
   `PROVENANCE.md`.
4. Open the actuarial category upstream as `borawhocodess/fm4sd#5` (done 2026-10-30), with
   the three sub-headings preserved.

## Why

The index is 80 entries behind upstream (355 vs 303 at the fork). A merge keeps the
research layer, the actuarial category and the fetched corpus; a re-sync would destroy all
three. Drift will recur (~3.5 upstream entries/day), so the relationship and the trigger are
recorded once, here.

## Expected state

- 383 entries: 323 with an arXiv id, 60 without (the research's "61" predates #23, which
  gave `gnr` its legacy id).
- Manifest rows for all 383; every id-bearing entry fetched against today's revision.
- The 28 actuarial slugs still parse, still grouped under their three sub-headings.

## Verification

- `parse_index(merged README)` → 383 / 323 / 60.
- `--index` output and `fm4sd_search.py stats` agree with the figures written into
  `README.md` / `PROVENANCE.md`.
- `git diff --stat` shows only README, manifest, docs and the plan — no payload.

## Risks

- Fetching 323 papers takes ~10–20 minutes at the polite rate; failures surface as error
  statuses in the manifest rather than aborting the merge.
- Upstream may ignore the PR indefinitely; the local block stays authoritative meanwhile.

## Note — manifest repair during delivery

`--fetch` iterates the manifest present at start-up, so the merge needed two passes:
`--fetch` (254 existing) → `--index` (383 rows, 254 recovered from disk) → `--fetch`
(remaining 69). The second pass re-wrote already-fetched rows as `cached` and dropped their
digests (`fetch_one`'s cached branch sets neither `sha256` nor `ok`). The 254 pre-merge rows
were restored from `main`'s manifest (same slugs and arXiv ids), keeping their committed
`ok`/`cached` statuses and the 28 digests; the 69 new rows keep today's fetch results. This
is the same `--index`/`--fetch` metadata-loss family as the ticket filed against revision
pinning (#33).
