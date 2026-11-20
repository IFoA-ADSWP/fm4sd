# Plan — index the November 2026 Prior Labs-adjacent releases (2026-11-20)

Follows the Prior Labs community digest of 2026-11-20. Only the items that are *papers* or
*cookbook recipes* belong in this index; the course and the video tutorial are not index rows
(see Out of scope).

## What

- `README.md` `## papers` → `- tabular`: two entries
  - `weights-and-caches` — arXiv **2611.20174**, *Weights & Caches: LLMs Can Program Tabular
    Foundation Models* (Hoo, Buehler, Swelam, Hutter, Purucker, 15 Nov 2026). It programs
    nanoTabPFN from zero-initialised weights and edits TabPFN-3.5's KV cache, so it sits with
    `nanotabpfn` / `modded-nanotabpfn` and `tabpfn-3.5`.
  - `prts-transcriptomics` — arXiv **2611.18774**, *In-context learning predicts clinical
    endpoints from bulk transcriptomes across diseases and platforms* (Wang et al., 12 Nov
    2026). A domain-specific 220M in-context learner benchmarked against TabPFN v3.5; filed in
    `- tabular` beside the other model entries rather than a new category for one paper.
- `README.md` `## cookbooks`: `multi_target_regression` (title and URL read from the published
  page, not from the digest). Listed, not fetched — the section is in `NON_PAPER_H2`, so it
  moves no manifest entry.

## Why

Both ids were verified against arXiv on 2026-11-20 (title and author list match the digest).
Neither is in the index: a repo-wide search for each id returned nothing. The cookbook list is
dated and holds 25 of the recipes, so the new one is absent.

No digest is proposed here. A digest needs a close reading against this project's questions,
and that is a separate decision (map #78).

## Verification

- `python3 scripts/fm4sd_fetch.py --index` regenerates the manifest; `--fetch --only
  weights-and-caches prts-transcriptomics` fills the payload; `--index` again records it.
- `python3 scripts/check_reproducibility.py` 3/3 — the published counts move with the manifest
  in this commit.
- Both arXiv links resolve to the stated titles.

## Out of scope

- The DeepLearning.AI course and the predictive-distributions YouTube walkthrough: the index
  carries papers, Prior Labs cookbook recipes, blog posts and repositories, and attaches videos
  to a paper row rather than listing them.
- `capabilities/thinking-mode` as a new section: the post it links
  (`tabpfn-3-5-thinking-upgrade`) is already under `## blog`, and the recipe
  `experiment_with_thinking_mode` is already under `## cookbooks`.
- The licence pass (`fm4sd_licences.py`): unrun since #66, and PROVENANCE records the next pass
  as the place new arXiv licence rows appear. Both new entries therefore carry no licence
  record yet — the same gap `gnr` has — and an absent record is not permission.
- Digests for either paper (map #78).
