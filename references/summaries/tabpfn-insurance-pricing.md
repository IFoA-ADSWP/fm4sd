# tabpfn-insurance-pricing — TabPFN against GLM and XGBoost on MTPL frequency and severity

arXiv [2605.22892](https://arxiv.org/abs/2605.22892) · [code](https://github.com/B-Deprez/tabpfn_insurance)
Deprez, Verbeke, Verdonck. Source: `papers/tabpfn-insurance-pricing/text.txt`

## Why this is here

It is the closest published study to this project's central puzzle: **the same two datasets**
(`freMTPL2`, `beMTPL97`), 5-fold cross-validation, the same baseline family (Poisson/gamma GLM,
XGBoost), and the same question — does TabPFN beat them for insurance pricing? Its answer is
the one this repo measured: not on frequency.

`freMTPL2` and `beMTPL97` are "about 678,000 and 163,000 policies" in the paper's own words,
which is the size of our `freMTPL2freq` (678,013 rows) and `bemt97` (163,212).

## What it finds

Frequency, exposure-weighted Poisson deviance (lower is better), from its Table 1 — TabPFN-v2.6
at 100k context and TabPFN-v3 on the full fold:

| model | freMTPL2 | beMTPL97 |
|---|---:|---:|
| GLM | **0.296** ± 0.001 | **0.551** ± 0.004 |
| XGBoost | 0.344 ± 0.001 | 0.583 ± 0.004 |
| TabPFN-v3, full fold | 0.343 ± 0.002 | 0.626 ± 0.008 |
| TabPFN-v2.6, 100k context | 0.379 ± 0.005 | 0.563 ± 0.006 |

> TabPFN does not consistently outperform established baselines: it falls behind the GLM on
> claim frequency, where its performance depends on the size of the in-context training set,
> but it is competitive on claim severity, where data are scarcer.

and its conclusion: "TabPFN cannot yet replace established actuarial methods for claim
frequency."

Severity is more mixed than the abstract's framing suggests: on the Belgian set TabPFN-v3 is
best, on the French set XGBoost is best and TabPFN-v2.6 sits between it and the GLM, with the
paper noting the spread is "mostly influenced by one outlier".

**Context size does not close it.** On RMSE the response is flat — the paper says context size
"does not seem to affect RMSE values much" — and on deviance v3 improves from 0.363 at 2,000
policies to 0.343 at the full fold, still behind the GLM's 0.296. "Give it more context" is not
the remedy at these sizes.

## The mechanisms it names — the useful part

> TabPFN does not yet incorporate all aspects of **exposure**, **sparse claim counts**,
> **heterogeneous conditional variance**, and **distribution-specific loss functions**, which
> are crucial for frequency and severity pricing.

That is four mechanisms, and the paper operationalises the first one explicitly:

> TabPFN, however, supports neither an offset nor observation weights, so exposure cannot enter
> the model in the same way.
>
> We include the exposure $e_i$ as an input feature and take the claim count $N_i$ as the
> target
>
> Note that this is not equivalent to an offset: whereas the GLM and XGBoost impose
> proportionality between exposure and the expected claim count, TabPFN learns the effect of
> exposure from the data.

Severity is fitted on `ln(1 + y)` through the model's built-in target transformation, and it is
"trained unweighted, as it does not support observation weights".

This is the published form of what our regime note could only infer: the GLM and the trees get a
*structural* offset and per-row weights; TabPFN gets exposure as one more column and no weights.

## How it differs from our runs — do not compare levels

- **Versions:** v2.6 and v3. No v3.5, so our §16/§24 v3.5 findings are not what this tests.
- **Metric:** exposure-weighted Poisson deviance on claim **rates** (`y_i = N_i / e_i`).
  Our frequency verdicts are on counts. The levels are therefore not comparable — their GLM
  reads 0.296 on `freMTPL2` where our frontier records 0.3211 for a Poisson GLM. Only the
  **ordering** carries across.
- **Baselines:** XGBoost at fixed hyperparameters (depth 3, 500 trees, learning rate 0.01,
  subsample 0.75, after Henckaerts et al.), TabPFN at defaults, no tuning on either side.
- **Cost:** it reports inference time and finds TabPFN's "substantially longer".
- **Exposure handling is the same on both sides.** Its workaround — exposure as an input column,
  claim count as the target — is what our frontier harness already does: it replaces the
  `Exposure` column with `log(Exposure)` and keeps counts as the target
  (`scripts/eval/insurance_benchmark_v1/run_frontier_benchmark.py`, module docstring). So the
  one thing a TFM without offsets or weights can do, both studies already do. There is no
  "handle exposure properly" experiment left to run on this model version.

## What it does not say

No v3.5, no Thinking mode, no target decomposition, no fusion with trees, no ensembling. Two
motor third-party-liability datasets; nothing on lapse, reserving, or severity tails. It
establishes the *existence* of the gap on our data, not its cure.
