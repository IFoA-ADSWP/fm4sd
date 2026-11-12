# The vendor's code-level surface: `PriorLabs/TabPFN/examples/`

> **Status:** reading only, written 2026-11-12. **No script was executed and no model was fitted.**
> Nothing here is a measurement — it is what the vendor's runnable examples *say*, read at source.
> Research ticket [#83](https://github.com/IFoA-ADSWP/fm4sd/issues/83). This file lives on a branch
> because the research layer never merges (`docs/RESEARCH.md`); `main` has no `research/` directory.
>
> **Pin:** `PriorLabs/TabPFN@3f2e9f9bcb20984354727a8c0075f64bc0744ea3` (2026-11-11, "[RES-3640] Run the
> safepower preset on GPU (#1398)"). Read at that commit, not at `main`, because `main` moves ~daily.

Tags used throughout: **verified** (line read in the pinned file) · **verified-in-code** (checked
against an installed package, command stated) · **unverified** (the source says it, we cannot check it).

---

## 0. Why this is not a paper digest

The corpus indexes papers. This note covers an artifact no paper replaces: the vendor's 17 example
scripts and 2 notebooks. They carry the *constants* a paper omits — the fine-tuning recipe down to
the patience, the name of each inference-time lever, and what each one costs.

It sits beside the digests, not inside `references/summaries/`: digests quote `papers/<slug>/text.txt`
from the manifest, and an example script has no slug. Keeping it out also keeps the digests' coverage
figures honest.

## 1. Sources

| # | Source | What it is | Tag |
|---|---|---|---|
| **S1** | `PriorLabs/TabPFN` @ `3f2e9f9`, `examples/*.py` (17 files) | the vendor's runnable surface | **verified** (all 17 read) |
| **S2** | same commit, `examples/notebooks/` | `TabPFN_Demo_Local.ipynb`, `Databricks_MLflow.ipynb` | **listed, not read** — no claim here rests on them |
| **S3** | `tabpfn==8.5.0`, installed at `/Users/Scott/projects/tabular-foundation-model/.venv` | whether each lever exists in the pin the sibling repo runs | **verified-in-code** (§8) |
| **S4** | corpus digests `finetuningtfm`, `tabpfnv2closerlook`, `tabicl`, `tabpack` | the paper-level counterparts of §3 and §5 | our own files |
| **S5** | `docs.priorlabs.ai/benchmarking` (linked from `benchmarking_tabpfn.py`) | the doc the example defers to | **not re-read here** — the vendor doc pages were read at source in `tabpfn-reserving` (E7/E10/E11 sources S1–S4) |

## 2. Inventory — 17 examples in seven groups

| File | Lines | What it demonstrates | Lever it names |
|---|---:|---|---|
| `tabpfn_for_regression.py` | 45 | the minimal regressor call on diabetes | — |
| `tabpfn_for_binary_classification.py` | 31 | minimal classifier, breast cancer | — |
| `tabpfn_for_multiclass_classification.py` | 34 | minimal classifier, iris | — |
| `tabpfn_classifier_with_tuning.py` | 57 | `eval_metric="f1"` with/without `tuning_config={"tune_decision_thresholds": True}` | threshold tuning |
| `tabpfn_regressor_with_tuning.py` | 118 | `tuning_config={"calibrate_temperature": True}`, `RegressorEvalMetrics`, NLL/CRPS/quantile coverage | ensemble temperature |
| `finetune_regressor.py` | 161 | full-parameter fine-tune, regressor | `FinetunedTabPFNRegressor` |
| `finetune_classifier.py` | 172 | full-parameter fine-tune, classifier | `FinetunedTabPFNClassifier` |
| `prompt_tuning_regressor.py` | 198 | frozen weights, prompt `(X, y)` tensors as parameters | `differentiable_input` |
| `prompt_tuning_classifier.py` | 177 | the same for classification | `differentiable_input` |
| `kv_cache_fast_prediction.py` | 57 | `fit_mode="fit_with_cache"` vs default | KV cache |
| `batched_classification_cv.py` | 60 | `predict_proba_batched` across 5 folds | fused batch |
| `batched_regression_m4.py` | 104 | `predict_batched` across M4 series | fused batch |
| `save_and_load_model.py` | 31 | `save_fitted_tabpfn_model` / `load_fitted_tabpfn_model`, `.tabpfn_fit` | persistence |
| `input_gradients.py` | 76 | `d prediction / d X` through the frozen model | saliency |
| `plot_regression_distribution.py` | 64 | `tabpfn.visualisation.plot_regression_distribution` | distribution plot |
| `benchmarking_tabpfn.py` | 110 | TabPFN vs two XGBoost configs, ROC-AUC + fit/predict time | the vendor's own benchmark recipe |
| `sagemaker.py` | 412 | SageMaker Runtime endpoint for a **TabPFN 2.5** model | hosted deployment |

## 3. The two fine-tuning recipes, side by side

Both files are explicit that these are *dataset-shaped* constants, not rules:

> **verified:** "These settings work well for the diamonds dataset (OpenML 42225, ~54k rows). For
> other datasets, you may need to adjust these settings to get good results." (`finetune_regressor.py`)
>
> **verified:** "These settings work well for the Higgs dataset." (`finetune_classifier.py`)

| Constant | Regressor (diamonds) | Classifier (Higgs) |
|---|---|---|
| `epochs` | 100 | 100 |
| `learning_rate` | 1e-5 | 1e-5 |
| `lr_warmup_only` | `True` | `True` |
| `n_finetune_ctx_plus_query_samples` | **20,000** | **50,000** |
| `n_estimators_finetune` / `_validation` / `_final_inference` | **8 / 8 / 8** | **4 / 4 / 4** |
| `early_stopping_patience` | 15 | 15 |
| `eval_metric` | not passed | **`"log_loss"`** |
| `random_state` | 0 | 0 |
| Hardware | "80 GB of VRAM", CUDA | same |

**What the table cannot show, and the wrapper decides.** An "epoch" is not a pass over the data. In
`tabpfn==8.5.0` the wrapper takes

> **verified-in-code:** `finetuned_base.py:917` — `n_finetune_ctx_plus_query_samples = min(
> self.n_finetune_ctx_plus_query_samples, len(y_train))`, then builds chunks of at most that size
> (`get_preprocessed_dataset_chunks`, `equal_split_size=False`).

So the chunk cap — not the epoch count — sets how much data one step sees. At diamonds' ~54k rows,
20,000 lands near a third of the training set per step; at 10,000 rows the default 50,000 binds
*down* to the whole set and an epoch is **one optimizer step**. Same word, different quantity. Nothing
in either example says this; it is only visible in the wrapper.

**The non-knobs the files do specify** — each one a correctness or comparability guard:

- `main_process_first()` wraps the dataset download, so under `torchrun` the other ranks read a warm
  cache instead of racing the fetcher (**verified**: "not all sklearn fetchers write their cache
  atomically").
- **One `fit()` per `torchrun` session** (**verified**: "For multiple finetuning runs, use separate
  torchrun invocations"). A warning, unexplained — it says the wrapper carries state across `fit()`.
- A W&B logger is one argument away (`tabpfn.finetuning.logging.WandbLogger`) and is how the per-epoch
  curve gets recorded at all; the examples leave it commented out.
- Early stopping is **on** in both, selecting on validation MSE / log loss. The examples never disable
  it, so "epochs = 100" in practice means "at most 100".
- The *base* model is constructed with `ignore_pretraining_limits=True` — required at 49k rows, inert
  below the checkpoint's limit.

## 4. Prompt tuning: the lever with no paper behind it

> **verified:** "Prompt tuning keeps the TabPFN weights frozen and instead optimizes the in-context
> examples themselves: a small set of (X, y) 'prompt' samples is treated as differentiable parameters
> and updated by gradient descent so that predictions on held-out queries improve."

The mechanism is `differentiable_input=True` plus `fit_with_differentiable_input(prompt_x, prompt_y)`;
the prompt tensors get `requires_grad_(True)` and one Adam step is taken through the frozen model per
batch. Constants in the regressor example: 200 prompt samples of 2,000 total, 5 epochs, batch 128,
`lr=1e-2`, MSE loss, `n_estimators=1`, `inference_precision=torch.float32`, synthetic `make_regression`.

**The regressor's twist is the part worth quoting**, because it is the only place in the whole example
set that spells out the regression head:

> **verified:** "the regressor's `forward` returns bar distribution logits, so we decode a
> differentiable point prediction as the expected value over the bin centers", then "undo the
> z-normalisation applied during fit" with `y_train_std_` / `y_train_mean_`.

Two consequences to carry:

1. Prompt-tuning a **regressor** is an **MSE-on-the-mean** procedure. It never touches the distribution,
   so it cannot be scored by NLL, CRPS or coverage on equal terms with a full fine-tune — the objective
   is different, not just cheaper.
2. The same `borders`-rescaled bar distribution shows up here in code, independently of the vendor
   documentation route: bins fixed in a normalised space, rescaled by the training target's mean and sd.

Cost is the reason this lever matters and the reason it is unmeasured: the examples run it on CPU, on
synthetic data, with no timing against the fine-tune they sit beside.

## 5. Cost and throughput: three ways not to pay for context twice

| Lever | How | Stated trade-off (**verified**) |
|---|---|---|
| KV cache | `fit_mode="fit_with_cache"` | "slower `fit` but faster `predict`"; memory "roughly O(N_samples * N_features)"; "Benefit grows with train size and repeated inference (CV folds, batch eval, etc.)" |
| Batched CV | `predict_proba_batched(X_trains, X_tests)` | "the whole CV run collapses into one fused forward per estimator instead of one per fold" |
| Batched M4 | `predict_batched(...)` | "stacks the series on the model's batch dimension and runs one fused forward per estimator" |

The batched path has a hard precondition, stated bluntly, and it is a good example of a vendor who
chose refusal over silence:

> **verified:** "ragged batches are rejected rather than padded, since padding would feed the model
> fake context rows." (`batched_classification_cv.py` — the demo trims rows to a multiple of the fold count.)

This is the vendor's answer to the cost side of the hardware wall. The corpus's *training-free* answer
is `baps` (context compression); these are complementary, not competing.

## 6. The calibration surface, as code

- **Classifier:** `eval_metric="f1"` with `tuning_config={"tune_decision_thresholds": True}` tunes the
  decision threshold. It is not temperature and does not touch probabilities.
- **Regressor:** `tuning_config={"calibrate_temperature": True}` tunes the **ensemble** softmax
  temperature. The docstring is precise about the scope: "This does not touch the `softmax_temperature`
  of individual ensemble members" — each member is sharpened by its checkpoint's own declared value.
- The regressor example then evaluates NLL, CRPS and **empirical quantile coverage** at
  `[0.1, 0.25, 0.5, 0.75, 0.9]`, with the calibration test stated plainly: "A well-calibrated
  distribution puts a `q` fraction of the targets below its `q`-quantile. Under-dispersed predictions
  undershoot in both tails."

That last quote is the vendor stating the exact test our own coverage work uses, on a
`make_friedman1` toy. It is a recipe, not a result.

## 7. Version era: one example is pinned in the past

`sagemaker.py` targets a **TabPFN 2.5** endpoint. Every other file is unversioned and assumes whatever
`tabpfn` ships alongside it. Since a finding is only meaningful against the version it was measured
with, treat this set as *API-era current, model-era mixed*: read it for the lever, never for the number.

## 8. What exists in our environment (`tabpfn==8.5.0`, verified-in-code)

Checked by import and signature inspection against `/Users/Scott/projects/tabular-foundation-model/.venv`:

| Lever from the examples | In `tabpfn==8.5.0`? |
|---|---|
| `FinetunedTabPFNRegressor` / `FinetunedTabPFNClassifier` | yes |
| `tabpfn.finetuning.main_process_first`, `.logging.WandbLogger` | yes |
| `fit_mode` | yes — `Literal['low_memory', 'fit_preprocessors', 'fit_with_cache', 'batched']` |
| `predict_batched` (regressor), `predict_proba_batched` (classifier) | yes |
| `differentiable_input`, `fit_with_differentiable_input` | yes, both estimators |
| `save_fitted_tabpfn_model` / `load_fitted_tabpfn_model` | yes |
| `tabpfn.visualisation.plot_regression_distribution` | yes |
| `tabpfn.inference_tuning.RegressorEvalMetrics` | yes |
| `tuning_config`, `eval_metric`, `inference_config` constructor arguments | yes |

**So "the examples are newer than our pin" is not a blocker for any lever in this set.** The pinned
package carries one thing the examples do not show at all: `tabpfn/inference_tuning.py`, which holds a
guard no example mentions — `MIN_NUM_SAMPLES_RECOMMENDED_FOR_TUNING = 500`.

## 9. What the examples do not give you

1. **No defaults.** The constants are anecdotes for two datasets. Both files tell you to change them.
2. **No measurement protocol.** Single 90/10 holdout, one seed, no repeats, no paired comparison with a
   noise floor. The printed deltas are a demo, not evidence by this repo's standard.
3. **No cost model.** One sentence — "80 GB of VRAM" — and no timing table.
4. **No data-shape caveats.** Nothing about grouped rows, exposure weights, clustering, or log targets.
   For insurance targets those are the first three things that break a naive split.
5. **No statement of what an epoch costs.** §3 recovers it from the wrapper, not the example.
6. **No early-stopping ablation.** Selection-on-validation is the vendor's default in both fine-tune
   examples, and no example shows what the same budget does without it.

## 10. Cross-references

- **`finetuningtfm`** — the paper behind §3: full fine-tuning best, via improved query–key retrieval,
  and *unstable* exactly on temporal shift + wide tables. The examples' dataset-shaped constants are
  the practical face of that instability.
- **`tabpfnv2closerlook`**, **`tabpack`**, **`tabicl`** — the architectural and tuning-cost counterparts
  of §5: failure modes at width, tuning by sampling ranges, and row/column factorisation.
- **`baps`** — training-free context compression; the other answer to "don't pay for context twice".
- **Pointer, not a result (sibling repo):** the fine-tuning fair test in `tabular-foundation-model`
  runs arms `B_ft3` / `B_ft10` / `B_ft30` on fold training capped at 10,000 rows. By §3's `min()`, the
  chunk cap binds there and each arm's "epoch" is **one optimizer step on the whole fold** — roughly 30
  steps against this example's ~245 at diamonds. That comparison is the reason this note exists; the
  measurement belongs to that repo, not this one.

## 11. Limits of this note

- Every claim is tagged; the untagged ones do not exist.
- Nothing was run. No timing, memory, accuracy or coverage number in this file comes from us.
- The example set moves under us: `main` was at `3f2e9f9` when this was read. A later reading supersedes
  this one; do not silently edit it.

## Housekeeping

The `research/<gap>` branch convention in `docs/RESEARCH.md` is currently blocked in this clone: a
local branch named `research` (2 commits ahead of `main`, unmerged) occupies the namespace, so
`git worktree add -b research/<name>` fails with `refs/heads/research exists; cannot create
refs/heads/research/<name>`. This note therefore sits on `corpus/tabpfn-examples`. Renaming the old
branch — by its owner, since it holds unmerged work — restores the documented convention.
