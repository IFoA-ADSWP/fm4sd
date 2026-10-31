# tabicl — ICL at scale, and the two-stage architecture

arXiv [2502.05564](https://arxiv.org/abs/2502.05564) · [code](https://github.com/soda-inria/tabicl) · ICML 2025
Qu, Holzmüller, Varoquaux, Le Morvan (Inria/Soda). Source: `papers/tabicl/text.txt`

## Architecture — the part worth stealing

Two stages, splitting TabPFN v2's alternating bi-attention:

1. **Tabular embedding module**, producing fixed-dimension row embeddings:
   - **Distribution-aware column-wise embedding** — reformulated as a **set-input** problem. A
     permutation-invariant set of cell values in, one-to-one embeddings out, via a **Set
     Transformer** with induced self-attention. Motivation: features have wildly different
     distributions, and conventional feature-specific embedding modules without parameter
     sharing limit cross-table transferability. The set formulation recovers distribution
     metadata per column while remaining transferable.
   - **Context-aware row-wise interaction** — models dependencies between features within a row.
2. **ICL module** — a transformer over the tokenized train+test row embeddings. Labels are used
   **only** here.

Because rows are compressed to fixed dimension in stage 1, stage 2 is not quadratic in features.
That is the whole scaling trick.

## Results

- Pretrained on synthetic datasets up to **60K samples**; handles **500K** samples on affordable
  resources.
- Across **200 TALENT** classification datasets: on par with TabPFN v2, systematically **faster**
  — **1.5×** on small datasets, **3–10×** on large.
- On **53 datasets with >10K samples**, beats both TabPFN v2 and **CatBoost** — the gradient
  boosting library, indexed as `catboost` (1706.09516).
- Fitted runtime scaling laws give ~**5× average speedup** on large datasets.
- Concrete: 10,000 samples × 100 features → ~20 s vs 1 min 40 s for TabPFN v2.
- Achieved by "using fewer of the expensive row-wise and column-wise attention layers with
  smaller embedding dimension before ICL on tokenized rows."

## Prior-design detail

The synthetic prior **oversamples the identity/random function**: the random activation is sampled
**ten times more often** than other activations, "to account for the fact that it can represent
many different functions." Tree depth `r = ceil(log10 k)` for `k` classes, since each split
reduces class count by ≥10×.

## Why it matters here

- **The column-then-row factorization is the structural answer** to the quadratic blow-up that
  forces nanoTabPFN's speedrun to start with an SDPA rewrite. It is a bigger structural lever
  than anything in the speedrun ledger, and it composes with them.
- **That prior-sampling detail is a concrete, cheap lever** nobody in the ledger has tried —
  prior *design* is a separate axis from optimizer and precision, and the speedrun protocol
  only constrains the evaluation pipeline, not the prior. Changing the prior is fair game.
- Beats CatBoost on >10K-sample classification, which this file called "the closest published
  support for the observation that TFMs beat GBDT once data is not scarce."

  *Note 2026-10-31 (#53):* it is no longer the closest support, and the generalisation is now
  contested. `when-do-neural-nets-outperform-boosted-trees-on-tabular-data` (2305.02997) is a
  larger published study — 19 algorithms over 176 datasets — and its headline is the opposite
  framing: the NN/GBDT gap is often negligible, light GBDT tuning matters more than the family
  choice, TabPFN is itself effectively limited to training sets of about 3,000 rows, and GBDTs handle skewed or
  heavy-tailed feature distributions better than NNs. TabICL's own >10K result stands; the
  inference drawn from it does not.

## Caveats

- **Classification only.** No regression objective, and nothing on two-part / zero-heavy
  targets — this paper neither establishes nor refutes anything about decomposition approaches.
- Ties to the prior dump: nanoTabPFN's prior was generated with TabICL's prior implementation
  (per its paper), so the two are already coupled at the data level.
- Later TabICLv2 (arXiv 2602.11139) is a separate, much larger effort — 24.5 H100-days. This
  digest covers v1.