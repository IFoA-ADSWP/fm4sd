# Plan: remove `dedupe()` from `scripts/fm4sd_fetch.py` (issue #13)

## Finding

`dedupe()`'s docstring asserts the index repeats papers across sections (the
tabpfnv2 example). Measured with the repo's own `parse_index()` + `dedupe()`:

| index                  | parse_index | dedupe | dropped | dup arXiv ids | dup slugs |
|------------------------|-------------|--------|---------|---------------|-----------|
| `upstream/main` README | 355         | 355    | 0       | 0             | 0         |
| local README           | 303         | 303    | 0       | 0             | 0         |

Upstream is duplicate-free too, so `dedupe()` is not defending against future
upstream merges either — it drops zero entries everywhere. Nothing else in the
repo (README, PROVENANCE.md, docs) references dedupe or claims the index has
duplicates, so there is no contradiction to report.

## Change

Issue #13's brief: if no duplicates upstream, remove `dedupe()` and its call
sites as dead weight.

- Delete the `dedupe()` function (its docstring is the only claim that the index
  currently contains duplicates).
- Un-wrap its three call sites: `compare_remote()` (twice) and `cmd_index()`
  become `parse_index(md)` directly.

## Why this is safe

`dedupe()` is a no-op on both indexes (measured above), so the parsed paper list
is byte-identical with and without it. Re-running `fm4sd_fetch.py --index` must
therefore leave `references/manifest.json` unchanged — that is the verification
gate (no test suite in this repo). `PROVENANCE.md` documents how the corpus is
built; the build's behavior does not change, so it needs no edit.

## Scope discipline

A concurrent agent is editing the arXiv-id regex section of the same file on
another branch. This plan's edits are confined to the `dedupe()` function body
and its three call expressions so the merge stays clean.
