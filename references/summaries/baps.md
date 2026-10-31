# baps — Balanced Adaptive Prototype Selection

arXiv [2608.12989](https://arxiv.org/abs/2608.12989) · TabPFN, context compression
Source: `papers/baps/text.txt`

## Why this one matters

**This is the only paper found in the corpus that speaks directly to a live blocker rather
than confirming something already known.** It is also the most actionable find of the sweep.

The claim: **512 prototypes retain strong predictive performance and reliable calibration** on
million-row datasets, at ~**1,953:1 context compression**, on an **Intel Core i7 with 16 GB RAM
and no GPU**.

## What it does

Constructs a compact inference context by jointly preserving five things, rather than just
subsampling:

- representative structure (class-wise budget allocation)
- **informative decision boundaries** (samples near the boundary)
- local density / reliable neighbourhoods
- **class balance**
- feature-space diversity

The stated framing: "scalability ... is primarily constrained by **context quality rather than
model capacity**." No retraining, no architecture change — the pretrained TabPFN is untouched.

Headline numbers on HIGGS (512-prototype budget, i.e. 0.0512% of a million-row training set):

| Method | Bal. Acc. | Macro-F1 | ROC-AUC | ECE | Time (s) |
|---|---|---|---|---|---|
| Stratified Random | 0.670 | 0.670 | 0.735 | **0.030** | 479.9 |
| KMeans Medoid | 0.690 | 0.687 | 0.758 | 0.085 | **479.7** |
| BAPS-Density | 0.688 | 0.683 | 0.755 | 0.106 | 481.2 |
| BAPS Ensemble | **0.697** | **0.692** | **0.769** | 0.093 | 1511.8 |

BAPS beats every single-context baseline and wins outright on SUSY (0.782 balanced accuracy).
Ensembling over multiple contexts improves calibration at ~proportional inference cost.
Paired Wilcoxon with Holm correction: **p = 0.031** vs the strongest single-context baseline.

## Relevance — and the honest limits

The blocker it might unblock: freMTPL2 needs ~678k rows for a learnable signal, TabICL is
usable to ~12k on an 8-core CPU, and every subsample in between is unstable (p99 ratio swinging
0.04 → 2.47). The reported workaround so far is "wait for a GPU". BAPS suggests a different
workaround: **compress the context instead of shrinking the dataset**, and run on CPU.

Four caveats, all material:

1. **TabPFN, not TabICL.** The two have different architectures and different context
   handling. Nothing here establishes that prototype selection transfers to TabICL, and the
   paper's own future work says only that it hopes to "extend the proposed framework to broader
   foundation models."
2. **Classification only.** HIGGS/SUSY/Covertype are classification benchmarks. The metric is
   balanced accuracy / ROC-AUC / ECE. There is **no regression and no tail calibration** — and
   the open question in this project is a p99 *severity* tail, which requires calibrated
   magnitude, not class discrimination.

   *Named 2026-10-31 (#53):* what is missing has references in this corpus, so say it rather
   than only asserting the absence. Calibrated distributional regression is
   `accurate-uncertainties-for-deep-learning-using-calibrated-regression` (1807.00263); the
   regression/quantile calibration theory — T-calibration, reliability diagrams, the R\*
   coefficient — is `regression-diagnostics-meets-forecast-evaluation` (2108.03210); and the
   CRPS decomposition into miscalibration / discrimination / uncertainty is
   `decompositions-of-the-mean-continuous-ranked-probability-score` (2311.14122).
3. **It compresses training context, not test rows.** The project's other memory issue —
   TabICL's ~2.6 MB per test row — is a different axis and is already handled by `--test-cap`.
   BAPS addresses compute/latency for a large *training* set.
4. **"Reliable calibration" is ECE on balanced-ish classification**, not tail calibration. ECE
   on a 50/50 binary target says little about whether the top 1% of a heavy-tailed continuous
   outcome is priced correctly.

   *Made actionable 2026-10-31 (#53):* report a quantile reliability diagram or pinball loss
   instead of ECE when the question is the tail. The instrument is
   `regression-diagnostics-meets-forecast-evaluation` (2108.03210) for T-calibration and
   reliability diagrams, `of-quantiles-and-expectiles-consistent-scoring-functions` (1503.08195)
   for the quantile score, and `decompositions-of-the-mean-continuous-ranked-probability-score`
   (2311.14122) for reading a CRPS into its parts. ECE is the wrong number for this target, not
   a weak one.

## What is worth doing with it

The one transferable idea is **boundary-aware + class-balanced context construction for a
zero-inflated target**. An 89%-zero severity table is an extreme class-imbalance problem at the
indicator level, and BAPS explicitly preserves "minority-class evidence" — which is precisely
the zero part that carries the signal. Whether a prototype-selected context preserves the
*indicator* signal (AUC 0.708) at 50k+ rows is a testable, cheap question on existing data.

That is a **CPU-only experiment with a clear falsifier**, and it is the only route found that
could turn the hardware-blocked replication into something runnable on the current machine.

## Caveats

- Single venue-style paper; no independent replication in this corpus.
- Five "publicly available benchmarks" named but only two (HIGGS, SUSY) reported, by page limit.
- No released code link in the index entry.
- The 1,953:1 figure is against a *million*-row training set; the relevant ratio at 50k rows
  would be much smaller and is not reported.