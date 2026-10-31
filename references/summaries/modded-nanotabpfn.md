# modded-nanotabpfn — Speedrunning Tabular Foundation Model Pretraining

arXiv [2606.03681](https://arxiv.org/abs/2606.03681) · [code](https://github.com/borawhocodess/modded-nanotabpfn) · [OpenReview](https://openreview.net/forum?id=QT1ySCPeW3)
Öztürk, Pfefferle, Hutter. 2026-06-02. Source: `papers/modded-nanotabpfn/text.txt`

## What it is

A **speedrun protocol**, not a model. Directly adapted from
[modded-nanogpt](https://github.com/KellerJordan/modded-nanogpt): contributors modify a
single training script and compete to reach a fixed metric target in the shortest wallclock
time. The stated contribution is "not a new tabular model family, rather it is a fixed and
reproducible speedrun protocol and a public sequence of records that isolates which practical
pretraining optimizations transfer to TFMs."

## The target

Beat the average validation ROC AUC of a **Random Forest** baseline on **subsampled
TabArena**, on **1× NVIDIA L40S**, minimum wallclock. The target is derived from the same
evaluation pipeline as the speedrun model, so it cannot be gamed by changing evaluation.

## Rules (deliberately minimal, only to keep records comparable)

- Must not change the evaluation pipeline
- Must not load pretrained weights
- Must be faster than the prior record when re-run on the verifier's hardware at the same seed
- Reported wallclock is the **median** of multiple verification runs (suppresses cluster noise)
- Each run logs its own source, config, software versions, GPU metadata, peak memory, timing

## Records — the actual ledger

⚠️ **The paper's record 9 (0.92 min) is no longer current.** The live repo has two records
since, at **0.79** and **0.76 min** — see [SWEEPS.md](SWEEPS.md) for the full current ledger,
the exact eval protocol, and caveats. Cite **0.76 min / ~98×** for the state of the art, not
0.92 / 81×.

Records are **cumulative**, not alternatives: each new record is the previous plus one change,
verified over many repeated runs with bootstrap CIs (record 11 compares `pr19` vs `pr19+pr20`,
31 runs each).

| # | Wallclock (min) | Synthetic datasets | Change |
|---|---|---|---|
| 1 | 74.32 | 80,576 | Baseline |
| 2 | 54.41 | 45,824 | Muon optimizer |
| 3 | 10.10 | 13,184 | SDPA, bf16, LR, width |
| 4 | 9.26 | 13,184 | Batched Muon, compile |
| 5 | 7.57 | — | Exponential decay of residual stream |
| 6 | 3.88 | 9,664 | RMSNorm, thinking rows |
| 7 | 3.48 | — | LAWA (latest weight averaging), AdamW weight decay |
| 8 | 2.15 | — | Repeated feature grouping |
| 9 | **0.92** | 3,648 | Autoresearch HPO, Muon weight decay, mean-pool decoder |
| 10 | **0.79** | — | Shape-grouped Newton–Schulz, producer-thread dataloader, single datapoint SDPA |
| 11 | **0.76** | 4,096 | Feature-width sorted batching |

Target: **≤ 0.8068462330697953** val avg ROC AUC (RF-matched). Paper-era figure: 81× wallclock,
22× fewer datasets. Current: ~98×, 20× fewer datasets.

**Note 2026-10-31 (#53): RF-matched is Random-Forest parity, not GBDT parity.** The bar was
set against a Random Forest on a subsampled suite, so clearing it is a claim about a tree
baseline, not about gradient boosting. `why-do-tree-based-models-still-outperform-deep-learning`
(2207.08815) is the benchmark that compares at tuning parity — models "accounting for both fitting
models and finding good hyperparameters"; `tabular-data-deep-learning-is-not-all-you-need`
(2106.03253) is the often-cited XGBoost-beats-deep-learning result whose deep baselines were
tuned far less — which is why a tuning-parity bar matters; and
`tabrepo-a-large-scale-repository-of-tabular-model-evaluations` (2311.02971) holds the tuned-model
evaluations to check a target against. A GBDT-matched target would be a harder bar.

The exact number of thinking rows is inconsistent *within the paper* — record-6 text says 16,
the architecture figure caption says 24, and the live repo lists **24**.

## Technique notes, from the paper

- **Muon optimizer** on the 2D weight matrices of the encoder, keeping schedule-free AdamW for
  the rest. Muon LR set to 0.1× the AdamW LR. Same hyperparameters as modded-nanogpt — transfers
  without tuning.
- **SDPA rewrite + pre-Norm + bf16 + LR 1e-3 + width 192→256, heads 6→4.** The paper's own
  ablation isolates the **LR increase and the SDPA rewrite as dominant**; bf16 and TF32 matmul
  contribute the remainder. *Do not credit the precision switch for this record.*
- **Batched Newton–Schulz** across QKV matrices + `compile` on the encoder layer forward.
- **Residual stream scaled by 0.95^i** entering block i — exponentially down-weighting earlier
  layers in the final output.
- **RMSNorm** instead of LayerNorm, + **16 learnable thinking rows** prepended along the data
  axis. The paper states the thinking rows account for most of that record's improvement, and
  that trained attention maps confirm they are actively attended to. (Note: the architecture
  figure caption says 24 thinking rows — text says 16. Minor inconsistency in the paper.)
- **Record 9** was found by adapting [autoresearch](https://github.com/karpathy/autoresearch),
  an **LLM-driven** HPO/architecture search loop with human intervention — not hand-derived.

## Why this matters here

This is the closest published precedent to a nanoTabPFN pretraining speedrun, and the
techniques in records 2–6 are directly transferable. Two observations worth carrying forward:

1. **The two biggest wins are unglamorous.** SDPA + LR schedule accounted for 54.41 → 10.10 min
   (≈5×) on its own. Precision cuts were secondary. Anyone starting a speedrun should do these
   first rather than reaching for architecture changes.
2. **Record 9 leans on LLM-driven HPO**, not a single insight. It is the weakest link in terms
   of transferable knowledge — and took 31 runs.

## Caveats

- Subsampled TabArena is the eval. Nothing here establishes behaviour on high-dimensional,
  many-category, regression, or temporally-shifted tables — the regimes where TFMs are weakest.
- Records 2–6 target *matching* baseline predictive performance, not improving it.
- **Record 11's margin is thin**: 0.79 → 0.76 min against a stated std of 0.06 min, i.e. about
  half a sigma. It may not be a real separation. Record 11 also shows its own trade-off honestly
  — epochs got faster (0.84s → 0.72s) but it needs more of them (57 → 64).
- **Sub-minute timings assume a warm `torch.compile` cache** (stated in the record's README).
- The repo recommends commit `b0f29b7` as a clean starting point; `train_nano.py` on `main`
  (898 lines) has gotten crowded.
- The speedrun target is a RF-beating ROC AUC on **classification**. A continuous or
  two-part objective is a different target, and nothing here validates transfer to one.