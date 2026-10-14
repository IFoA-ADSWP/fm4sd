# fm4sd — Agent Instructions

## Canonical test command

No test suite — this is a research/corpus repo.

Verification is reproducibility: re-run the relevant `scripts/fm4sd_*.py` and confirm
`references/manifest.json`, `references/summaries/` and `PROVENANCE.md` still agree.
State which of those you checked. A change to corpus-building or a figure needs
`PROVENANCE.md` updated in the same commit.

## Plans

Write docs/plans/<task>.md before non-trivial work: what you intend to change and
why. Commit it with the change.

## Conventions

This is a **research/corpus repo**, not an application. There is no test suite and there is
deliberately no build step — the "gate" is **reproducibility**, not tests.

- **`papers/`** holds downloaded PDFs and is **gitignored**. Only the slugs are tracked. A
  missing `papers/` directory is normal — rebuild it with the fetch script rather than
  treating it as a missing file.
- **`scripts/`** — `fm4sd_fetch.py` (corpus build), `fm4sd_search.py` (query),
  `fm4sd_licences.py`. Deterministic workflows go through these scripts, not ad-hoc loops.
- **`references/manifest.json`** is machine-readable and generated; `references/summaries/`
  holds the per-paper digests.
- **`PROVENANCE.md` is the enforcement doc** — every claim about the corpus must resolve to
  it. If you change how the corpus is built or how a figure is derived, update
  `PROVENANCE.md` in the same change. This is the repo's `check-docs` equivalent.

**Fork lineage.** This is a fork of `borawhocodess/fm4sd`; upstream's index is preserved
verbatim in `README.md`. An `upstream` remote exists so `git diff upstream/main` still works
and index-only improvements can be PRed back. **Do not rewrite the upstream index** — the
divergence 2026-10-07 was the research layer only.

**Verification for a change here:** re-run the relevant script and confirm the manifest,
summaries and `PROVENANCE.md` still agree. State which of those you checked.

<!-- Replace this block with gotchas as you find them. -->

## Review

Every change is reviewed before merge, in a fresh context, against the plan.
