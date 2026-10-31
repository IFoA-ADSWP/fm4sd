# Which classical baselines belong in the corpus?

Research for ticket #42 (child of #41, blocks #47). Branch `research/gap-baselines`;
this file is the only thing on it. Read-only: no change to `README.md`,
`references/manifest.json` or `scripts/`.

## Answer

Eight papers fill the gap, all under a new `papers` category called **`baselines`**.
They are the models the project's severity/frequency comparison is scored against —
XGBoost and CatBoost for gradient boosting, the tree-vs-deep-learning evidence
(Grinsztajn, Shwartz-Ziv & Armon, Gorishniy, McElfresh, Kadra), and the survey that
maps the whole comparison (Borisov et al.).

The shape of the finding: the index is **383 entries and contains not one classical
baseline paper**. Grepping `README.md` for `xgboost`, `lightgbm`, `catboost`,
`random forest`, `gradient boosting`, `gbdt`, `gbm`, `forest`, `breiman`, `friedman`
returns zero. The only `boosting` hits are three *applications* of Tweedie boosting to
insurance claims (`1508.06378`, `1811.10192`, `2307.07771`) inside the actuarial block —
they use the method, they are not it.

That absence is already costing the research layer. Three of the repo's own digests make
baseline claims with no paper in the index behind them:

- `references/summaries/actuarial.md:120` — "CatBoost is the reference frequency model"
  (from an independent auto-claim study), stated twice, sourced to nothing in the corpus.
- `references/summaries/tabicl.md:30` — "beats both TabPFN v2 and **CatBoost**" on 53
  datasets with >10K samples, used as the closest published support for TabICL's claim.
- `references/summaries/SWEEPS.md:107` — a sweep target set to "match Random Forest" on
  validation ROC AUC.

So this is not a completeness exercise: the corpus currently argues against models it
cannot cite.

## Method note

- **De-duplication.** Grepped `README.md` and `references/manifest.json`
  case-insensitively for every candidate's title token and first author:
  `xgboost`, `lightgbm`, `catboost`, `random forest`, `gradient boosting`, `gbdt`,
  `gbm`, `forest`, `grinsztajn`, `shwartz`, `gorishniy`, `borisov`, `kadra`,
  `ponomareva`, `chen`, `guestrin`, `prokhorenkova`, `pedregosa`, `biau`, `breiman`,
  `friedman`. Zero hits for all except `chen` (six unrelated `chen et al.` citations) and
  `grinsztajn` (TabPFN 2.5/3 author citations, not the 2022 paper). Cross-checked the
  literal arXiv ids against the manifest: `0` occurrences for all eight ids below.
  `TabNet` (`1908.07442`) is in the index and is **not** re-proposed — it is a deep
  architecture, not a classical baseline, and it belongs to the deep-learning side of the
  comparison.
- **Verification.** Every id below was read back from the arXiv API
  (`https://export.arxiv.org/api/query?id_list=<id>`), not from memory, and the returned
  `<title>` and `<published>` matched the claim. Titles are quoted as the API returns
  them, including the question marks and capitalisation.
- **Rate limiting, disclosed.** The API 429'd hard after a burst of id lookups from this
  host and stayed 429 for several minutes; the eight below were confirmed before the
  block, one lookup batch at a time. Any candidate that could not be re-confirmed was
  dropped rather than included on recall (see "Considered and not included").

## The list

| # | arXiv id | title (as arXiv returns it) | why it is load-bearing here | category |
|---|---|---|---|---|
| 1 | [1603.02754](https://arxiv.org/abs/1603.02754) | *XGBoost: A Scalable Tree Boosting System* | The default GBDT baseline: the implementation every tabular benchmark runs and the bar every foundation-model claim is scored against. | `baselines` |
| 2 | [1706.09516](https://arxiv.org/abs/1706.09516) | *CatBoost: unbiased boosting with categorical features* | Ordered target statistics + ordered boosting handle high-cardinality categoricals (postcode, vehicle, occupation) without target leakage — the case actuarial rating factors actually are; the digest already calls CatBoost "the reference frequency model". | `baselines` |
| 3 | [2207.08815](https://arxiv.org/abs/2207.08815) | *Why do tree-based models still outperform deep learning on tabular data?* | The canonical tree-vs-DL result on medium-sized tabular data, with three named mechanisms (rotation invariance, uninformative features, non-smooth targets) that TabPFN-class claims have to overturn. | `baselines` |
| 4 | [2106.03253](https://arxiv.org/abs/2106.03253) | *Tabular Data: Deep Learning is Not All You Need* | XGBoost beats DL on 11 datasets and DL+XGBoost ensembles beat both — the "keep the classical baseline in the ensemble" evidence. | `baselines` |
| 5 | [2106.11959](https://arxiv.org/abs/2106.11959) | *Revisiting Deep Learning Models for Tabular Data* | Fixes the comparison protocol (same tuning budget, same preprocessing) and shows a well-tuned simple DL model is competitive but not dominant — the methodology the other comparisons are judged by. | `baselines` |
| 6 | [2305.02997](https://arxiv.org/abs/2305.02997) | *When Do Neural Nets Outperform Boosted Trees on Tabular Data?* | 176 datasets, 19 baselines (TabZilla): the balanced "it depends on dataset properties" answer, so the corpus cannot overclaim from Grinsztajn alone. | `baselines` |
| 7 | [2106.11189](https://arxiv.org/abs/2106.11189) | *Well-tuned Simple Nets Excel on Tabular Datasets* | Shows a large part of the DL deficit is a tuning artefact — regularised MLPs beat GBDT on many datasets when tuned equally; the fairest statement of the debate. | `baselines` |
| 8 | [2110.01889](https://arxiv.org/abs/2110.01889) | *Deep Neural Networks and Tabular Data: A Survey* | The survey that tabulates classical-vs-DL results and protocols across the literature — the orientation document for this category. | `baselines` |

## Why this set, and what it deliberately does not cover

- **Gradient boosting: two of three implementations, by arXiv availability.** XGBoost
  (1) and CatBoost (2) have citable arXiv papers. **LightGBM does not** — Ke et al.'s
  NeurIPS 2017 paper has no arXiv id, and an arXiv title search for `LightGBM` returns
  only application papers (payment security, wave forecasting, sEMG gesture recognition),
  none of them the method. It is not indexed here for that reason, and #41's "every entry
  needs a resolvable arXiv id" rule is what settles it. The intended stand-in — a
  GBDT-implementation benchmarking paper (`1809.04559`) — could not be confirmed inside
  the rate-limit window, so it is left to #45/#47 rather than included on recall; it is
  the natural LightGBM-side entry if someone can resolve the id.
- **Random forests: covered by evidence, not by an implementation paper.** Breiman 2001
  (*Machine Learning* 45:5–32) has no arXiv id — it predates arXiv's ML coverage — so the
  canonical RF citation cannot satisfy the id rule. The RF baseline is instead carried by
  (3), which pits random forests against DL directly, and by the sweep target in
  `SWEEPS.md` that already uses RF as the reference. If the parent wants a dedicated RF
  row, the honest options are a journal-only Breiman citation or scikit-learn's JMLR
  paper, and both are weaker than (3).
- **Deep models are out of scope by construction.** TabNet is already indexed; TabPFN,
  TabICL, TabM, TALENT and TabArena likewise. This category is only the thing they are
  compared *to*.
- **Duplicates removed.** `1810.11363` (*CatBoost: gradient boosting with categorical
  features support*, the 2018 workshop preprint) is the same work as (2) and is rejected
  as a duplicate; the NeurIPS version is the canonical statement.

## Considered and not included

| candidate | why not |
|---|---|
| **LightGBM** — Ke et al., *LightGBM: A Highly Efficient Gradient Boosting Decision Tree* (NeurIPS 2017) | No arXiv id. Title search returns only application papers. Method coverage gap, accepted. |
| **Breiman**, *Random Forests* (Machine Learning 45:5–32, 2001) | Pre-arXiv, journal-only; no id to resolve. RF carried by (3) instead. |
| **Friedman**, *Greedy Function Approximation: A Gradient Boosting Machine* (Annals of Statistics, 2001) | The GBDT origin paper, but pre-arXiv and journal-only. XGBoost (1) is the citable descendant and the one actually benchmarked. |
| **`1810.11363`** — CatBoost workshop preprint | Duplicate of (2). |
| **scikit-learn** — *scikit-learn: Machine Learning in Python* (JMLR 12, 2011) | The implementation every RF/GB baseline is actually run through, but it is a library paper, not comparison evidence; would be the weakest row in the table. |
| **TabNet** (`1908.07442`) | Already in the index (queue → tabular). Deep architecture, not a classical baseline. |
| **AutoGluon-Tabular** (2003.06505) | AutoML ensembling, not a baseline model; belongs with benchmark methodology (#45). |
| **TabArena, TALENT, TabZilla** | Already indexed (TabArena, TALENT) or identical to (6) — TabZilla *is* McElfresh et al. |
| **Gorishniy et al.**, *On Embeddings for Numerical Features in Tabular Deep Learning* | Architecture work by the same group as (5); improves the DL side, says nothing about which baseline to run. |
| **A Tweedie-boosting methods paper** (`1508.06378`, `1811.10192`, `2307.07771`) | Already indexed as actuarial applications; adding them again under `baselines` would duplicate slugs for no gain. |

## Integration notes (deliberately not actioned here)

- **`baselines` is a new top-level bullet under `## papers`, not a sub-bullet.**
  `parse_index()` (`scripts/fm4sd_fetch.py:495–553`) takes `category = cats[0][1]` and
  `subcategory = cats[1][1] if len(cats) > 1`, so one bullet header yields
  `category: "baselines"`, `subcategory: ""` and needs no parser change. Adding a second
  level would create a subcategory instead.
- **Counts move in the same commit.** 383 entries becomes **391**; the figures in
  `README.md`, `references/README.md` and `PROVENANCE.md` are all derived by
  `check_reproducibility.py` check 3 and compared against the prose, so the README, the
  manifest and the prose must change together or the gate goes red. Table rows (1)–(8)
  are all arXiv-resolvable, so the "resolvable to arXiv" figure moves by 8 too.
- **Fetch routes are all standard.** Every entry is a plain `[arxiv]` link, so
  `fetch_route()` takes the arXiv LaTeX path (`.tex` bundle first, PDF fallback) — no
  new route, no `[pdf]`/`[doi]` special-casing. (1)–(8) are old enough that the `/src/`
  bundle is stable in practice, but #33's revision pinning is what would make that
  promise exact.
- **Ordering inside the category.** Chronological reads best for an evidence category:
  (1) 2016 → (2) 2017 → (5) 2021 → (4) 2021 → (7) 2021 → (8) 2021 → (3) 2022 → (6) 2023.
  The slug order in the table above is by role (models, then evidence) and is not a
  proposal for README order.

## Risks

- **One of the eight is a survey** (8); 3, 4, 5, 6, 7 are empirical and 1, 2 are method
  papers. If the parent prefers a leaner set of seven, (8) is the one to
  cut — it is the least load-bearing row, and no argument above depends on it.
- **The evidence papers disagree, and the category should keep it that way.** (3) says
  trees win, (6) says it depends on the dataset, (7) says the DL deficit is tuning. Listing
  them together is the point; reading (3) alone would let the corpus overclaim.
- **(6) is a benchmark, not a method paper** — it could equally live under benchmark
  methodology (#45). It is kept here because its *finding* is about baselines, and #45 has
  its own remit (evaluation protocol, leakage, contamination).
- **Venue/year claims** are from the arXiv records (title and first-publication date); the
  NeurIPS/KDD attributions are common knowledge and are not load-bearing for any argument
  above.
