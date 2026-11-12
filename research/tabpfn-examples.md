# The vendor's repository as a source: `PriorLabs/TabPFN`

**Part 1** reads the `examples/` set (17 scripts). **Part 2** registers the repository
itself — `src/`, `tests/`, `changelog/`, the build file and CI — because the corpus had never
read it at all, and the fine-tuning claims that matter are decided in `src/`, not `examples/`.

> **Status:** reading only, written 2026-11-12. **No script was executed and no model was fitted.**
> Nothing here is a measurement — it is what the vendor's repository *says*, read at source.
> Research ticket [#83](https://github.com/IFoA-ADSWP/fm4sd/issues/83). This file lives on a branch
> because the research layer never merges (`docs/RESEARCH.md`); `main` has no `research/` directory.
>
> **Pin:** `PriorLabs/TabPFN@3f2e9f9bcb20984354727a8c0075f64bc0744ea3` (2026-11-11, "[RES-3640] Run the
> safepower preset on GPU (#1398)"). Read at that commit, not at `main`, because `main` moves ~daily.

Tags used throughout: **verified** (line read in the pinned file) · **verified-in-code** (checked
against an installed package, command stated) · **unverified** (the source says it, we cannot check it).

---

## 0. Why this is not a paper digest

The corpus indexes papers. This note covers an artifact no paper replaces: the vendor's repository —
17 example scripts, and the `src/`, `tests/` and `changelog/` that decide what those examples mean. They carry the *constants* a paper omits — the fine-tuning recipe down to
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
- The tree moves under us: `main` was at `3f2e9f9` when this was read. A later reading supersedes
  this one; do not silently edit it.

---

# Part 2 — the repository as a source

## 12. Coverage: what has been read, and what has not

The tree at the pin is **322 files / 6.0 MB, of which 213 are Python**. Reading all of it is not the
job; knowing which part a claim rests on is.

| Area | Files | What was done | Tag |
|---|---:|---|---|
| `examples/` | 19 (17 `.py`, 2 `.ipynb`) | all 17 scripts read in full; notebooks listed only | **verified** |
| `src/` | 96 (94 `.py`) | names and module layout surveyed; two bodies read in full — elsewhere, in `tabpfn-reserving` (`finetuning/data_util.py`, `finetuning/finetuned_base.py`) | **listed** |
| `tests/` | 145 (99 `.py`) | inventory by directory and filename; no test body read | **listed** |
| `changelog/` | 25 | all 24 fragments' first line; 4 read in full | **verified** (as stated) |
| `CHANGELOG.md` | 73 KB | release sections for 8.5.0, 9.0.0, 9.1.0 and 9.2.0 read | **verified** |
| `docs/` | 2 | two SVG assets, no prose | **verified** (absence) |
| `pyproject.toml`, `.github/workflows/` | 1 + 12 | read / name-and-trigger only | **verified** / **listed** |

The honest summary: **17 of 213 Python files read in full (~8%)**, plus the changelog, the build file
and the CI inventory. Nothing below claims more than that.

## 13. The module map

`src/tabpfn/` is organised so that a claim can be traced to a file. The names are the vendor's:

| Module | Files | What it owns |
|---|---:|---|
| `preprocessing/` | 43 (+11 under `torch/`) | the whole front end: `modality_detection`, `clean`, `datetimes`, `group_ids`, `label_encoder`, `ensemble`, `pipeline_factory`, and `steps/` — `reshape_feature_distribution_step`, `adaptive_quantile_transformer`, `kdi_transformer`, `safe_power_transformer`, `squashing_scaler_transformer`, `remove_constant_features_step`, `add_svd_features_step`, `add_fingerprint_features_step`, `differentiable_z_norm_step`, `shuffle_features_step`. `target_transform.py` + `presets.py` hold the target-transform registry; `torch/` is the GPU path |
| `architectures/` | 22 | **one module per model version** — `tabpfn_v2`, `_v2_5`, `_v2_6`, `_v3`, `_v3_5` — plus `shared/bar_distribution.py` (the bucket grid), `kv_cache`, and attention backends (`fa3_`, `mlx_`, MPS workarounds) |
| `finetuning/` | 8 | `data_util`, `finetuned_base`, `finetuned_classifier`, `finetuned_regressor`, `train_util`, `logging`, `_torch_compat` |
| top level | 15 | the estimators (`classifier`, `regressor`), `inference`, `inference_config`, `inference_tuning`, `model_loading`, `checkpoint`, `validation`, `settings`, `regression_metrics`, `parallel_execute`, `downsample_correction`, `memory`, `browser_auth` |
| `visualisation/`, `misc/` | 4 | `regression_distribution`; `_sklearn_compat`, `debug_versions` |

Two things follow. First, "preprocessing" is not one thing: it is a pipeline of named steps, each of
which can change a prediction, and `preprocessing/steps/` is where the vendor documentation's
preprocessing levers actually live. Second, the model lineage is **in the code as files** — a version
is a module, not a label on one checkpoint.

## 14. The version lineage — and the default-model flip

`CHANGELOG.md` is the ledger. Release headings present at the pin:

| Release | Date | Bearing on us |
|---|---|---|
| **8.5.0** | 2026-08-27 | **our pin** in `tabular-foundation-model` |
| **9.0.0** | 2026-09-15 | **the default model changes** (below); two `eval_metric` combinations now raise |
| 9.1.0 | 2026-10-02 | `ModelSpecs` replaces three spec classes; `kv_cache_precision="adaptive"` |
| 9.2.0 | 2026-10-12 | `enable_torch_compile`; batched v3/v3.5 cached-inference fix |

### 14.1 The flip, which is the single most useful line in the repository

> **verified**, `CHANGELOG.md`, 9.0.0: "TabPFN-3.5 is the default model: `TabPFNClassifier()` and
> `TabPFNRegressor()` now load `ModelVersion.V3_5` unless a `model_path` or another version is given.
> The previous default, TabPFN-3, stays available through `create_default_for_version(ModelVersion.V3)`."

> **verified-in-code**, `tabpfn==8.5.0`: `ModelVersion` has no `V3_5` member — it enumerates
> `[V2, V2_5, V2_6, V3]` — and `resolve_model_path(..., version="v3")` defaults to `v3`.

So an unpinned estimator resolves to **v3 on 8.5.0** and to **v3.5 on 9.0.0 or later**, with
2026-09-15 as the boundary. That is a dated, checkable answer to the question "what did `auto`
mean?"— and it is version-specific: the same source line means two different models either side of
it. Any result measured with an unpinned estimator needs its package version beside it, not just its
model label.

### 14.2 Two `eval_metric` combinations became errors

> **verified**, 9.0.0: "`eval_metric="roc_auc"` combined with `tune_decision_thresholds=True` now
> raises instead of silently optimizing balanced accuracy" — and `log_loss` with the same flag "now
> raises instead of silently optimizing accuracy. … Use `calibrate_temperature=True`, which optimizes
> log loss directly."

The classifier tuning example (§6) passes `eval_metric="f1"` with `tune_decision_thresholds=True`,
which survives; a reader copying the pattern with `log_loss` gets an exception on 9.x and a silently
different objective on 8.x. Same code, two behaviours.

## 15. Merged but unreleased: the changes that will move a number

At the pin, `changelog/` holds 24 towncrier fragments written but not yet in a release. Ranked by
what they would do to a measurement:

| Fragment | Change | Why it bears on a number |
|---|---|---|
| `1198.breaking.md` | "Previously saved fitted regressors (`.tabpfn_fit` archives and pickled estimators) are incompatible with the updated target preprocessing and must be refitted. **Custom fine-tuning loops must pass `y_train_mean` and `y_train_std` to `fit_from_preprocessed`.**" | A saved artifact stops loading; a hand-written fine-tuning loop changes signature |
| `1199.changed.md` | "Regression target transforms now act on **raw targets** before final standardization. Both `power` and `safepower` retain input standardization; `None` and `"none"` retain standardization only." | The target transform is the vendor's main regression lever. Its meaning moves, so a result either side of it is not comparable |
| `1392.added.md` | "`TabPFNClassifier` and `TabPFNRegressor` take `group_col`: … or a list of labels whose joint value is one composite key. The selected columns are replaced by one categorical feature holding that key's integer code, **fitted on the training rows alone**." | **First-class grouped data.** This is the lever insurance work needs, and it does not exist in our pin |
| `1198.changed.md` | "Regression ensembles now normalize targets using each member's training rows; without subsampling, only floating-point differences are expected." | Named effect size, per ensemble member |
| `1402.changed.md` | Attention over an int8/float8 KV cache casts the cache and folds the scales into the query | Cached inference is the cost lever of §5 |
| `1397.added.md`, `1398.added.md` | The `quantile_norm*` and `safepower` presets now run on GPU | Preprocessing cost, not correctness |
| `1381.added.md` | Optional random sign flipping for numericals, reproducible per ensemble member | A new preprocessing option, off by default |
| `1375.fixed.md` | Quantiles accept any real in `[0, 1]`, including `np.float32` and the ints 0 and 1 | A quantile call that raised now works |
| `1376.fixed.md` | Constant features are removed **before** polynomial features are added | Changes predictions when `POLYNOMIAL_FEATURES` is set |
| `1339.changed.md` | Licence and README text state that datasets stay local and are never sent to Prior Labs | A data-governance claim about the local path, worth quoting rather than paraphrasing |

> **verified-in-code:** `group_col` and `enable_torch_compile` are absent from `tabpfn==8.5.0`'s
> estimator signatures, so the two most interesting additions above are **after** our pin.

Read as a set, these are a re-test trigger list: anything measured on 8.5.0 is measured against
pre-9 target preprocessing, without `group_col`, and without per-member normalisation.

## 16. Tests as specification

145 test files, and the layout says what the vendor treats as load-bearing:

| Path | Files | What it is |
|---|---:|---|
| `tests/test_preprocessing/` | 55 | the largest suite, by a wide margin — one test module per preprocessing step |
| `tests/` root | 40 | the interface and behaviour suite |
| `tests/test_architectures/` | 21 | one per architecture, plus shared components |
| `tests/reference_predictions/` | 18 | **golden reference outputs** — the vendor pins predicted values |
| `tests/test_torch_preprocessing/` | 11 | the GPU preprocessing path against the CPU one |

The root suite names its own contract: `test_finetuning_regressor.py`, `test_finetuning_classifier.py`,
`test_fit_from_preprocessed.py`, `test_save_load_fitted_model.py`, `test_inference_tuning.py`,
`test_consistency.py`, `test_batched_prediction_shape_safety.py`, `test_input_immutability.py`,
`test_model_specs.py`, `test_validation.py`.

For our purposes the two fine-tuning test modules are the nearest thing to a specification of §3: the
examples show what the vendor *ran*, the tests assert what the wrapper *must do*. Neither has been
read here — that is the obvious next read, and it is named rather than implied.

## 17. Build, CI, and what the repository does not contain

- `pyproject.toml`: `name = "tabpfn"`, `version = "9.2.0"`, `requires-python = ">=3.10"`. So the tree
  at the pin is a **9.2.0 tree**; the examples are 9.x code even where they demonstrate 8.x-compatible
  calls.
- 12 workflows: `ci.yml`, `check-changelog.yml` (towncrier — this is why `changelog/` exists and why
  the fragments are reliable), `release-create-pr.yml`, `release-tag-on-merge.yml`,
  `release-publish.yml`, `nightly-notebook-check.yml`, three Slack/Dependabot/PR helpers, and two
  Claude review workflows. Triggers only; bodies not read.
- `docs/` contains **two SVG diagrams and no prose**. The documentation is the external site
  (`docs.priorlabs.ai`), which fm4sd does not hold either — so the vendor's written guidance is
  outside this corpus by construction, not by oversight.

## 18. What this changes for the corpus

1. **A repository cannot be a corpus entry.** The glossary defines `skipped:not-paper` as "when the
   link is a code repository or blog post", and 7 of 431 entries carry it. Reading code therefore has
   no home in `references/`: the research layer is the only place it can live, which is why this file
   is on a branch rather than beside the digests.
2. **The corpus's only link to TabPFN's code is stale.** The 2023 `tabpfn` entry's `github` link is
   `https://github.com/automl/TabPFN`; the current repository, `PriorLabs/TabPFN`, appears nowhere in
   the manifest. The one `PriorLabs/*` repository entry is `tabpfn-rel`, a different project.
3. **The version flip is a fact worth sharing.** `9.0.0` changed the default model on 2026-09-15, in
   the local package. Any sibling work holding a number measured without a pin should be re-read
   against its package version. That is a corpus-level caution, not a result.
4. **Two candidate rules, for the owner, not for this note.** Either (a) the research layer is the
   permanent home for code-level findings, and then the `research/<gap>` branch convention has to work
   — it does not today (Housekeeping) — or (b) the corpus gains a `code` status/route, and the manifest
   can record a repository as a first-class source. This note does not choose.

## Housekeeping

The `research/<gap>` branch convention in `docs/RESEARCH.md` is currently blocked in this clone: a
local branch named `research` (2 commits ahead of `main`, unmerged) occupies the namespace, so
`git worktree add -b research/<name>` fails with `refs/heads/research exists; cannot create
refs/heads/research/<name>`. This note therefore sits on `corpus/tabpfn-examples`. Renaming the old
branch — by its owner, since it holds unmerged work — restores the documented convention.
