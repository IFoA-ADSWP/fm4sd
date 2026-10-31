# Research layer

This repo is a fork of
[borawhocodess/fm4sd](https://github.com/borawhocodess/fm4sd), which curates a reading
index for foundation models on structured data. Upstream ships an index only: no paper
payload, no manifest, one markdown file and a small `scripts/` directory.

The fork keeps upstream's index verbatim under its banner and adds a research layer:
a locally fetched corpus (`papers/`, gitignored), a machine-readable manifest
(`references/manifest.json`), search and statistics (`scripts/fm4sd_search.py`), and
per-paper digests under `references/summaries/`. Figures and their derivation live in
`PROVENANCE.md`; this page records how the fork relates to upstream and when it syncs.

## Upstream relationship

**Posture — merge, not re-sync.** Syncing is a plain `git merge upstream/main`. The
alternative (replace our README with upstream's, then rebuild) was ruled out: it deletes
the 37 local actuarial entries and their manifest records, the three actuarial
sub-categories, the research preamble, and the fetched payload — and buys nothing, because
the fork has patched no shared entry.

**Drift trigger.** Merge when upstream is roughly **25 entries ahead** — about two weeks at
its current ~3.5 entries/day — or whenever a decision session needs fresher data than the
local index holds. There is no calendar tick.

**The local actuarial block.** 37 entries (`actuarial / loss modelling`, grouped under
`severity`, `frequency and count models`, `tail metrics, quantiles, reserving`) live only
in this fork's `README.md`. The original 28 are proposed upstream as
[borawhocodess/fm4sd#5](https://github.com/borawhocodess/fm4sd/pull/5); the nine added by
#47 are not. All 37 stay local while that PR is open, so an ignored PR costs nothing.
Acceptance is genuinely unknown:
upstream has never merged a fork PR, runs no issue tracker, and commits from branches on
its own repo.

**On landing.** Drop the local block from `README.md`, re-run `--index`, and record the
landing in `PROVENANCE.md`. After that, every sync is a pure merge and the local category
stops being authoritative.

**Mechanics.** `git merge upstream/main`, then `python3 scripts/fm4sd_fetch.py --index`
(fetch metadata is recovered from payload on disk; licence records are carried forward by
arXiv id), then `--fetch` the papers the merge added. Divergence point: `62382d2`
(2026-10-05, upstream's "unnest tabpfn versions").

**Record.** Evidence: `research/upstream-relationship.md` on branch
`research/upstream-relationship` (filed under research ticket #21). Decision: #17.
Delivery: #22.
