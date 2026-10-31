# Digests

Close readings of the papers that matter most, plus the output of targeted corpus sweeps.
Each digest cites the extracted text it was written from, so claims are traceable to
`papers/<slug>/text.txt`.

## Round 2 digests — aimed at this project's open questions

Found by sweeping for (A) the severity ceiling, (B) the hardware wall, (C) the
indicator/magnitude decomposition, (D) tail metrics.

| Paper | Why it is here |
|---|---|
| [baps](baps.md) | **The actionable one.** 512 prototypes, ~1,953:1 context compression, **CPU-only, no GPU**. The only route found that could unblock the hardware-blocked replication on the current machine |
| [closedloop-priorselect](closedloop-priorselect.md) | **Independently corroborates the closed prior line.** A three-condition regularity where prior injection helps only if the base is *underfit* — and F32 put the checkpoint at 98.7% of the Bayes ceiling |
| [temporal-tabular-shift](temporal-tabular-shift.md) | A formal lower bound on what a frozen TFM cannot recover, invariant in sample size. Same *shape* of claim as the p99 ceiling — but a different obstruction |
| [tacticl](tacticl.md) | Up to 85% of layers replaceable, ICL retained. Also the corpus's clearest statement of why distillation ≠ free win |

## Actuarial digest — added 2026-10-08

| | |
|---|---|
| [actuarial](actuarial.md) | 28 papers added to the index to fill a void: the original corpus is **ML-methods only** and a sweep for `Tweedie|compound Poisson|loss ratio|actuarial|claim frequency` across 225 papers returned **two incidental hits**. Four extracts that bear on the tail seam — and three of them *narrow* existing claims in this repo rather than confirming them. |

## Round 1 digests

| Paper | Why it is here |
|---|---|
| [modded-nanotabpfn](modded-nanotabpfn.md) | The speedrun protocol and the full technique ledger — 74.32 → 0.76 min, with per-record attribution |
| [tabdpt](tabdpt.md) | Real data + SSL beats synthetic pretraining at every epoch. Strongest published argument against the synthetic-only recipe |
| [tabicl](tabicl.md) | Column-then-row factorization as the structural answer to quadratic cost; prior-sampling detail as an untried lever |
| [nanotabpfn](nanotabpfn.md) | The architecture being optimised, and the hard cap (binary, ≤5 features, 150 rows) inherited from the prior dump |
| [tabpfnv2closerlook](tabpfnv2closerlook.md) | Documents the high-dim/many-category/large-scale failure modes; training-free scaling path |
| [finetuningtfm](finetuningtfm.md) | Full finetuning best, via improved query–key retrieval — but unstable exactly on temporal-shift + wide tables |
| [tabpack](tabpack.md) | Attacks tuning cost by sampling ranges rather than searching. Not a TFM, but composable with one |

## Sweeps

[SWEEPS.md](SWEEPS.md) — two rounds of `grep` sweeps, round 2 targeted at this project's open
questions. **Three of four sub-questions produced a useful negative; one produced an actionable
positive.**

| Sub-question | Result |
|---|---|
| Ceiling fundamental? | Formal precedent exists, but for a *different* obstruction. Do not overclaim. |
| Unblock hardware? | **baps — actionable**, CPU-only, training-free |
| Decomposition holds up? | No published counterpart; novelty confirmed. Bonus: corroboration of the closed prior line. |
| p99 the right metric? | **Nothing in the ML index.** That was a scope limit, so **28 actuarial papers were added 2026-10-08** (see above). The metric question stays a business decision — no TFM paper evaluates tail accuracy — but the *modelling* question now has references. |

## Two corrections — both from trusting a sweep too quickly

1. **The speedrun ledger does stack.** A round-1 sweep found nothing about composability and I
   reported that as a gap. Wrong on two counts: the records are explicitly cumulative
   (`pr19` vs `pr19+pr20`, 31 runs each), and the paper is two records out of date. **A
   leaderboard's live state lives in its repo, not its paper.** Ledger now at **0.76 min / ~98×**.

2. **"Zero-inflation is unclaimed" was a bad sweep.** The round-1 headline negative result came
   from `--min-hits 3`, which discarded every relevant paper (they contain 1–2 hits each), and
   from a pattern that missed the morphological variant `zero_inflated`. Zero-inflation *does*
   appear in tabular/causal FM generators (`tabcausal`, `foundcause`, `avici`, and a cited
   TabPFN microbiome use-case). The project's contribution is narrower than "unclaimed" — it is
   the **calibration and the learnability test**, not the mechanism. Full correction, and three
   rules for avoiding a repeat, in
   [SWEEPS.md](SWEEPS.md#correction-2026-10-08-the-zero-inflation-is-unclaimed-result-was-a-bad-sweep).

## Coverage

12 digest documents covering ~35 papers, of the manifest's fetched set (updated 2026-10-31:
431 entries, 381 fetched — `python3 scripts/fm4sd_search.py stats` is the record). The rest
are corpus for sweeping — see `../manifest.json` and `../README.md`.

Not yet digested but high-value on the current question set: `gotabpfn` (high-dim tokenization),
`tabpfn-3` (may close the high-dim limitation), `tabiclv2` (next generation), `tabfm`, `tabh2o`,
`tabcausal` (zero-inflated generator — now on the list after the correction above).