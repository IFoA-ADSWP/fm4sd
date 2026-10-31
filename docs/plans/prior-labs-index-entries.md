# Plan — Prior Labs resources in the index (2026-10-31)

Follows the maintainer's decision to index Prior Labs' public research surface: all 25
cookbook case studies, the substantive blog posts, and the public repos — without touching the
parsed corpus.

## What

- `README.md`: a `## cookbooks` section listing all 25 recipes (docs links + frontmatter
  titles), a `## blog` section listing the 11 posts that bear on the corpus, and four public
  repos appended to `extras`.
- `scripts/fm4sd_fetch.py`: `cookbooks` and `blog` join `NON_PAPER_H2`, the existing mechanism
  for listed-but-not-parsed sections.
- `PROVENANCE.md` and `GLOSSARY.md`: record the listed-vs-parsed distinction, so a reader can
  tell a catalogue row from an omission.

## Why

The index is where this project's evidence base lives; Prior Labs' own case studies and
method notes are primary material for it. None of it is a paper: the recipes are notebooks and
prose, and the cookbook repo carries no licence, so under #9's scope line there is no
fetchable or publishable payload.

## Verification

- `check_reproducibility.py` 3/3; the manifest stays at 383 entries (a fresh `--index` without
  the parser change would read 408 — the gate catches exactly that).
- Every listed URL returns 200 (25 recipes against the docs page's 26 links, 11 posts, 4 repos).

## Out of scope

- Promoting any of these to manifest entries (would add `skipped:not-paper` rows and move
  published counts).
- Upstream PRs; the additions are local by decision.
