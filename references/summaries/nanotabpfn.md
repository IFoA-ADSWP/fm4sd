# nanotabpfn — the base architecture

arXiv [2511.03634](https://arxiv.org/abs/2511.03634) · [code](https://github.com/automl/nanoTabPFN)
Pfefferle, Hog, Purucker, Hutter. Source: `papers/nanotabpfn/text.txt`

## Architecture, as described

Four parts:

1. **`FeatureEncoder`** — normalizes each feature by train-set mean/std, **clips outliers**
   (values too large or too small), then a linear layer maps scalars to feature embeddings.
   **No positional embedding**, deliberately, for permutation invariance in datapoints *and*
   features.
2. **`TargetEncoder`** — extends `y_train` with its mean to create `y_test` entries, then linear.
3. **`TransformerEncoderStack`** — each layer applies **bi-attention**: feature attention, then
   datapoint attention. Separate skip connections around each attention block, LayerNorm after
   each. Then a **cell-wise 2-layer MLP**.
   - In datapoint attention: **training data attends only to itself, never to test data**;
     test data attends to training data. This is the ICL mask.
4. **`Decoder`** — 2-layer MLP on `y_test` embeddings → **logits**.

**Explicitly omitted** vs. real TabPFN: combining neighbouring pairs of features in the feature
embedding. The paper's justification — it "substantially increases code complexity, reduces
interpretability and destroys permutation invariance of the features."

## Pretraining config used in the paper

3 layers, 4 heads, embedding 96, MLP hidden 192, **80,000 synthetic datasets**, exactly 150
datapoints × 5 features × 2 classes, batch size 32.

⚠️ The `80,000 × 150 × 5` shape is the **hard cap inherited from the prior dump** — binary
targets, ≤5 features, fixed 150 rows. Confirmed by reading the HDF5 (see the private repo's
`PROVENANCE.md`: `max_num_classes=2`, `num_features` 1–5, `num_datapoints` fixed at 150).
This is the single most important limitation for anyone extending the work.

## Parameter count caveat

Measured instantiation of the paper's own config gives **356,066 parameters**. The paper's
"roughly 1M params" framing is loose by ~3×. Quote the measured number.

## Reported result

Matches k-NN / decision tree / random forest (default scikit-learn config) within **1 minute**
of pretraining on a single GPU. Claimed **160,000× faster** than TabPFN v2 pretraining.

Cited 2026-10-31 (#53): those are **default-config baselines**, and default-config baselines are
not the literature's standard. `tabular-data-deep-learning-is-not-all-you-need` (2106.03253) and
`why-do-tree-based-models-still-outperform-deep-learning` (2207.08815) both compare after tuning,
and the second explicitly accounts for both fitting models and finding good hyperparameters. So
"matches k-NN / DT / RF" is a comparison against untuned scikit-learn defaults, not against the
trees a benchmark would field.

## Why it matters here

It is the reference point for every speedrun record — the thing being optimised. The three
structural properties that shape what can be optimised:

- **Alternating bi-attention** is the cost driver: attention is quadratic in rows *and* in
  features, applied alternately. This is why TabICL's column-then-row factorization exists, and
  why record 3's SDPA rewrite was the single biggest win.
- **The prior is pre-generated**, so pretraining cost is *not* data generation cost. The speedrun
  compares against 80,576 datasets already on disk; a claimed speedup that shifts cost into
  prior generation is not a real speedup. Worth checking when reading any ledger.
- **The hard-coded shape caps the achievable target.** Binary/5-feature/150-row means the eval
  target is weak evidence about the model being good — it is evidence about the model being
  fast *on that restricted shape*.