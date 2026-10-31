# fm4sd — Agent Instructions

## Canonical test command

```bash
python3 scripts/check_reproducibility.py
```

No test framework and no dependency installs — the gate is reproducibility, and this command
is it. It needs no payload (`papers/` is absent in CI) and makes one network call. Three
checks:

1. `--index` regenerated in a scratch copy equals `references/manifest.json` on every
   README-derived field — `slug`, `arxiv_id`, `section`, `category`, `subcategory`,
   `citation`, `links`, `has_code`, the header and entry order. Payload-derived fields
   (`source`, `path`, `text_bytes`, `pages`, `n_tex_files`, `sha256`, `arxiv_rev`,
   `fetch_status`) and the
   licence/title/date records `fm4sd_licences.py` writes are excluded by construction: a
   payload-less `--index` cannot reproduce them (that wipe is #33, not this gate).
2. `--index --remote` leaves the manifest byte-identical — it must only compare upstream.
3. The counts published in the live documents — `README.md`, `references/README.md`,
   `PROVENANCE.md`, `references/summaries/README.md`, `docs/RESEARCH.md` — equal the figures
   derived from the manifest, and `fm4sd_search.py stats` agrees with both. The figures are
   read out of the documents, not hardcoded, so moving the corpus means updating the prose
   in the same commit. Any *other* tracked document that publishes an `N entries, M fetched`
   pair fails closed until it joins `LIVE_DOCS` (or moves under `docs/plans/` if it is
   history). The digests' prose about papers remains a manual read; their corpus figures are
   not.

CI runs the same command (`.github/workflows/reproducibility.yml`) on every PR and push to
`main`. State which checks you ran when you report a change. A change to corpus-building or a
figure needs `PROVENANCE.md` updated in the same commit.

### Branch protection — admin, once

A red run only blocks a merge when `main` requires the check. Repo admin, once:

1. Settings → Branches → branch protection rule for `main` (edit the existing one, if any).
2. Enable **Require status checks to pass before merging** and select the
   **reproducibility** job from `reproducibility.yml`.
3. Save, then confirm on any open PR that the merge button is disabled while the check is
   red or still running.

Documented rather than scripted: branch protection is a repo-admin setting that a PR cannot
apply or verify, so it stays a setup step.

## Plans

Write docs/plans/<task>.md before non-trivial work: what you intend to change and
why. Commit it with the change.

## Research layer

Research findings live on `research/<gap>` branches and never merge: the ticket closes
with its finding cited from the branch, so `main` has no `research/` directory. Read
`docs/RESEARCH.md` before proposing a PR for a research branch.

## Working copies

Dispatching a writer means running `scripts/new-worktree.sh <branch> [base]` and quoting its
output in the prompt. It places the worktree beside the main clone under `<repo>-wt/`. If it
refuses, stop and resolve the collision — never fall back to the main clone. One writer per
worktree; the main clone stays free for parallel sessions.

## Conventions

This is a **research/corpus repo**, not an application. There is no test suite and there is
deliberately no build step — the "gate" is **reproducibility**, not tests.

- **`papers/`** holds downloaded PDFs and is **gitignored**. Only the slugs are tracked. A
  missing `papers/` directory is normal — rebuild it with the fetch script rather than
  treating it as a missing file.
- **`scripts/`** — `entry.py` (the entry vocabulary: id and status), `manifest.py` + `payload.py` (the manifest format and
  the payload probe), `arxiv_meta.py`
  (batched, cached arXiv metadata), `fm4sd_fetch.py` (corpus build),
  `fm4sd_search.py` (query),
  `fm4sd_licences.py`, `check_reproducibility.py` (the gate), and `new-worktree.sh` (dispatch
  helper). Deterministic workflows go
  through these scripts, not ad-hoc loops.
- **`references/manifest.json`** is machine-readable and generated; `references/summaries/`
  holds the per-paper digests.
- **`PROVENANCE.md` is the enforcement doc** — every claim about the corpus must resolve to
  it. If you change how the corpus is built or how a figure is derived, update
  `PROVENANCE.md` in the same change. This is the repo's `check-docs` equivalent.

**Fork lineage.** This is a fork of `borawhocodess/fm4sd`; upstream's index is preserved
verbatim in `README.md`. Remotes are machine-local, so a fresh clone has only `origin` —
add the upstream remote as a setup step:

```bash
git remote add upstream https://github.com/borawhocodess/fm4sd.git && git fetch upstream
```

With it in place, `git diff upstream/main` still works and index-only improvements can be
PRed back. **Do not rewrite the upstream index** — the divergence 2026-10-07 was the
research layer only.

**Verification for a change here:** run `python3 scripts/check_reproducibility.py` (above),
then read the `references/summaries/` digests the change touches. State which you did.

<!-- Replace this block with gotchas as you find them. -->

## Review

Every change is reviewed before merge, in a fresh context, against the plan and the
judgement calls in `CODING_STANDARDS.md`.

## Issue tracker

Config: docs/issue-tracker.md
