# Sweep findings

Targeted `fm4sd_search.py grep` sweeps run 2026-10-07 over the 225-paper local corpus, aimed
at questions the digests raised. Recorded because a negative sweep result is evidence too:
it says the literature does *not* address something, which is a reason to believe a finding is
novel rather than a reason to have not looked.

Reproduce any of these with the command shown.

---

## Q1. Has anyone published on TFMs exploiting *feature-linked zeros* / zero-inflated targets?

```bash
python3 scripts/fm4sd_search.py grep "zero-inflation|hurdle model" --min-hits 3
```

**Result: 1 paper, 2068 hits total — and it is off-target.**

`foundcause` (2606.17516) mentions zero-inflation only as one item in a list of *post-processing
artefacts injected into synthetic data*:

> post-processing pipeline injects real-world artefacts: MCAR / MNAR / MAR missingness (15% of
> tasks), measurement noise, **zero-inflation**, discretization, rounding, heteroscedasticity,
> and log-uniform scale

That is a data-generator detail, not a treatment of zero-inflated *targets* as an ICL problem.

**Conclusion.** Nothing in this index addresses a TFM using an indicator of feature-linked
zeros as part of the prediction. The zero-exploitation result appears to be genuinely
unclaimed. Related but distinct: `iced` (In-Context Density Estimation for Tabular Data) targets
the zero problem as *density estimation*, not as a two-part predictive decomposition.

---

## Q2. What is published on TabPFN/TFM failure at high dimension and many categories?

```bash
python3 scripts/fm4sd_search.py grep "high-dimensional" --category tabular --min-hits 4
```

Five papers, in rough order of relevance:

| Paper | Hits | Angle |
|---|---|---|
| `gotabpfn` (2606.05441) | 33 | From feature ordering to **compact tokenization** for high-dimensional tabular FM. Most directly on point. |
| `tabpfnv2closerlook` (2502.17361) | 17 | Documents the limitation; test-time divide-and-conquer. [Digest](tabpfnv2closerlook.md) |
| `contextadaptiveinference` (2607.23304) | 16 | Adaptive inference under distribution shift. |
| `tabflex` (2506.05584) | 13 | In-context learning, Microsoft TICLE line. |
| `tabpfn-3` (2605.13986) | 10 | TabPFN v3; may have addressed the limitation directly. |

**Next step:** read `gotabpfn` and `tabpfn-3` before assuming the limitation is still open —
both postdate the closer-look analysis.

---

## Q3. Do the speedrun gains actually *stack*?

⚠️ **CORRECTION — an earlier version of this file said "no evidence". That was wrong.** The
sweep searched paper text and found nothing, which I over-read as a gap in the literature. The
definite answer is in the **speedrun repo, not the paper** — and the paper is also out of date.
See [the correction below](#q3-correction-read-the-repo-not-just-the-paper).

### Q3 correction: read the repo, not just the paper

The records are **explicitly cumulative**, and each one is verified against the previous with
many repeated runs.

Evidence from `records/20260826widthsort/README.md`:

> Comparison — 31 runs each of the previous record (**pr19**) and this one (**pr19+pr20**)

The `pr19+pr20` notation is the point: a new record is *previous + one change*, not a parallel
alternative. And the record itself states the change is narrow — "the model and optimizer are
unchanged, only the order of the datasets within an epoch." So record 11 is record 10 plus a
dataloader sort, measured over 31 runs each with bootstrap 95% CIs.

Verified in the live `train_nano.py` (898 lines, single script): markers for Muon (14 hits),
zeropower/Newton–Schulz (6), SDPA (2), `compile` (3), bf16 (5), `float32_matmul_precision` (1),
residual decay `0.95` (2), RMSNorm (4), thinking rows (11), feature grouping (10) — all present
in one file. The gains do compose.

### The paper's numbers are stale

The paper reports record 9 at **0.92 min**. The live repo has two records since:

| # | Record | Date | Change | Contributor |
|---|---|---|---|---|
| 10 | **0.79 min** | 2026-08-15 | Shape-grouped Newton–Schulz, producer-thread dataloader, single datapoint SDPA | @tjeong117 |
| 11 | **0.76 min** | 2026-08-26 | Feature-width sorted batching | @shounakb1 |

Current: **0.76 min vs the 74.32 min baseline ≈ 98×**, on 4,096 synthetic datasets vs 80,576.

**Quote 0.76 min / ~98×, not 0.92 min / 81×**, unless specifically discussing the paper.

### Two caveats on record 11 worth knowing

1. **Its margin is thin.** Record 10 median is 0.79 min, record 11 median 0.76 min, and record
   11's own std is **0.06 min**. The improvement is roughly half a standard deviation — it may
   not be a real separation. Record 11's own numbers also show the trade-off honestly: epochs got
   *faster* per epoch (0.84s → 0.72s) but it needs *more* of them (57 → 64).

   *Named 2026-10-31 (#53):* "roughly half a standard deviation — it may not be a real
   separation" is the right doubt, and the instrument for it is a mixed-effects model over
   per-task results, not two medians — `lmem-for-post-hoc-analysis-of-hpo-benchmarking`
   (2408.02533). Comparing medians of aggregated runs is the weaker test the paper exists to
   replace.
2. **Sub-minute timings assume a warm `torch.compile` cache** — the record's README says so
   explicitly. First-run wallclock will not match.

### The exact target and eval, for reproduction

Target: **≤ 0.8068462330697953** validation average ROC AUC — chosen to match Random Forest on the
same subsampled TabArena evaluation. Evaluation: 38 TabArena **classification** tasks;
subsample to 100 features and 1,000 rows (stratified by class); 5-fold shuffled
`StratifiedKFold`; constant columns dropped, numeric mean-imputed, categorical ordinal-encoded;
binary or one-vs-rest ROC AUC averaged over tasks.

Two qualifiers on that target, added 2026-10-31 (#53): it is **Random-Forest parity, not GBDT
parity**, and a single-suite RF-matched bar is a benchmark-lottery draw
(`the-benchmark-lottery`, 2107.07002). The tuned-model comparison to check it against is
`tabrepo-a-large-scale-repository-of-tabular-model-evaluations` (2311.02971).

Note the paper itself is inconsistent on thinking-row count — the record-6 text says 16, the
architecture caption says 24, and the live repo README lists **24**.

For a clean starting point the repo recommends commit **`b0f29b7`**; `train_nano.py` on `main`
has "gotten a bit crowded".

---

## Original sweep (superseded by the correction above)

```bash
python3 scripts/fm4sd_search.py grep "catastrophic forgetting" --min-hits 3
```

Returned 2 papers, neither tabular: `continual-learning-compose` (6 hits), `nora` (4 hits).

The corpus sweep was simply the wrong instrument here — a speedrun leaderboard's live state
lives in its repo, and a 2026-06 paper cannot describe records set in 2026-08.

---

## Q4. Which papers define the TabArena evaluation protocol?

```bash
python3 scripts/fm4sd_search.py grep "TabArena" --min-hits 3
```

`tabarena` (199 hits) is canonical. `tabpfn-3` (89), `tabprep` (107), `onelayerenough` (123),
`beyondarena` (157), `agentic-search-spaces` (90) all build on it.

Relevant caveat: the speedrun evaluates on **subsampled** TabArena. `beyondarena`
(2606.30410) exists because TabArena itself was found to saturate — worth checking before
treating a TabArena AUC as a meaningful target.

*Cited 2026-10-31 (#53):* that saturation caution is the **benchmark lottery**
(`the-benchmark-lottery`, 2107.07002) — a leaderboard position on one suite need not survive a
resample of tasks and metrics. The comparison that is not a lottery draw is a tuned evaluation
across many suites, which is what `tabrepo-a-large-scale-repository-of-tabular-model-evaluations`
(2311.02971) holds.

---

## Q5. Compression / quantization of TFMs — for the inference-cost side

```bash
python3 scripts/fm4sd_search.py list --category tabular --has-code | grep -iE "quant|compress|distill"
```

| Paper | Title |
|---|---|
| `tacticl` (2608.10837) | **TACTICL: Task-Aware Compression of Tabular ICL Models** |
| `attention-quantization-tfm` (2609.13031) | Attention Quantization for Tabular Foundation Models |
| `local-distillation` (2608.23538) | Local distillation (repo: `erincr/local-distillation-benchmark`) |
| `memoryefficienttfms` (2607.27546) | Memory-efficient TFMs |
| `loopicl` (2609.36108) | Loop ICL |

⚠️ **Correction to an earlier note in the private repo's docs:** `iced` was listed there as a
"compression" paper. It is **not** — `iced` is *In-Context Density Estimation for Tabular Data*.
The compression paper is `tacticl`. Fixed in this fork's docs; the private repo's copy still
carries the wrong label.

Upstream's own `todos` file independently flags "quantization in the TFM world … applied to
TabPFN", so this axis is already on the maintainer's radar.
---

# Sweep round 2 — targeted at this project's open questions (2026-10-08)

Four sweeps run against the four live sub-questions in the private repo: (A) is the ~5%
conditional-severity ceiling fundamental, (B) can anything unblock the hardware wall, (C) does
the indicator/magnitude decomposition hold up, (D) is p99 the right metric.

---

## A2. Is the ceiling fundamental or a feature-engineering gap?

```bash
python3 scripts/fm4sd_search.py grep "irreducible|aleatoric|feature.set ceiling|explainable variance|epistemic" \
  --category tabular --min-hits 3
```

**2 papers.** Only one is on point:

- `temporal-tabular-shift` (2609.12136) — a **formal, sample-size-invariant lower bound**: the
  identified-set diameter, the "wall", is "irreducible from unlabeled data uniformly in sample
  size". Also an orthogonal "$L^2$ projection wall" for what a frozen representation cannot
  express. [Digest](temporal-tabular-shift.md)

**Conclusion:** the *shape* of the claim ("the limit is not a sample-size problem") has formal
precedent, which is useful when the p99 ceiling is challenged. But it is a **different
obstruction** — unlabeled-data identifiability, not information the covariates do not carry.
Do not cite it as proof F30's ceiling is fundamental.

`tabpfn` matched only on a commented-out line, not a result.

---

## B2. Can anything unblock the hardware wall?

```bash
python3 scripts/fm4sd_search.py grep "compress|distill|quantiz|memory efficient|inference cost|kv cache" \
  --category tabular --min-hits 3
```

**8 papers. This is where the sweep paid off.**

| Paper | Approach | Reduction | Verdict |
|---|---|---|---|
| **`baps`** (2608.12989) | information-preserving **context** construction | **~1,953:1** context, **512 prototypes**, **CPU-only, no GPU** | **[Digest](baps.md) — the actionable one** |
| `tacticl` (2608.10837) | prune layers + task adapters | up to **85%** of layers, retains ICL | [Digest](tacticl.md) — task-specific |
| `memoryefficienttfms` (2607.27546) | **INT4 quantization** | **7.6×** memory footprint | weights, not context |
| `attention-quantization-tfm` (2609.13031) | attention quantization | — | argues *attention calculation* is the target, not weights/KV |
| `tfm-distillation` (2610.01435) | distillation supervision | — | teacher-query construction |
| `gotabpfn` (2606.05441) | compact tokenization, HDLSS | — | high-dim/low-sample, no retraining |
| `localdistillation` (2608.23538) | local distillation | — | benchmark + theory |
| `tdcoler` (2501.13905) | dataset distillation for pre-training | — | per-dataset level |

**Conclusion:** `baps` is the only paper that speaks **directly** to a live blocker rather than
confirming something known. It suggests compressing the *context* instead of shrinking the
dataset — CPU-only, training-free — which is the only route found that could make the
hardware-blocked replication runnable on the existing machine. Four material caveats (TabPFN not
TabICL, classification-only, context not test rows, ECE not tail calibration) are in the digest.

---

## C2. Does the indicator/magnitude decomposition hold up?

```bash
python3 scripts/fm4sd_search.py grep "two.part|hurdle|zero.inflated|two.stage|compound poisson|zero inflated" --min-hits 3
```

**8 papers, none on target for the decomposition.** Every "two-stage" hit is an unrelated
two-stage *training* or *search* procedure (time-series encoders, prior selection, GRPO code
training, graph sampling). **No paper in this corpus models a zero-inflated or hurdle target as
an ICL decomposition problem.**

**Conclusion:** reinforces the earlier negative result. The two-part framing this project
arrived at from first principles (F30/F31) has **no published counterpart** in this index, which
is either novelty or a sign it is not considered an interesting angle. The sweep cannot
distinguish those.

*Narrowed 2026-10-31 (#53):* read "no published counterpart" as **no _ICL_ counterpart**. The
canonical hurdle and zero-inflated models are now indexed, citation-only because both are
paywalled: `zero-inflated-poisson-regression-with-an-application-to-defects` (Lambert 1992) and
`specification-and-testing-of-some-modified-count-data-models` (Mullahy 1986). What is still
absent is a paper that treats the decomposition as a *foundation-model / in-context* problem —
which is the claim this sweep actually supports.

`tabicl` matched on its large-data motivation (4 hits), not on decomposition.

**But the sweep found something else, and it is the biggest conceptual result of the round:**

### C2-bonus. Prior injection: a three-condition regularity that corroborates F32

`closedloop-priorselect` (2609.06941) surfaced via "two-stage", not any prior-related query. It is
the closest published precedent to the question the roadmap asked, for a different PFN family,
and it reaches the same answer by construction:

> prior injection yields significant gains **only when** the base is **underfit**, the prior
> domain **matches** the task domain, and the task lies **within the base's training-prior
> support**.

This project fails **all three**: F32 puts the stock checkpoint at **98.7% of the Bayes
ceiling** (not underfit), the prior is binary/≤5-feature vs insurance's 19–130 continuous
features (domain mismatch), and the task dimensionality far exceeds the prior support. The paper
also states the failure mode directly — "injecting the same recipe into an **already-strong base
degrades it 4–9×** with a complete ranking reversal."

[Digest](closedloop-priorselect.md), including the pushback: the paper's support-boundary theorem
says out-of-support tasks are repairable only by *expanding the support* (retraining), which
reads as an argument for the full pretraining this project declined. The digest records why it
is not: closedloop's wall is a **representation** limit, F30's ceiling is an **information**
limit, and only the first is fixable by retraining.

---

## D2. Tail calibration / capital / reserving

```bash
python3 scripts/fm4sd_search.py grep "tail calibration|capital|reserving|p99|quantile regression|tail risk" \
  --category tabular --min-hits 3
```

**6 papers, essentially all noise.** "capital" matches `\usepackage[capitalize]` and "Figure
reference, capital." Most hits are formatting artefacts, not the concept.

The only substantive match is `baps` again (calibration, via ECE). `gotabpfn`, `tabpfn-3`,
`tabgenfm`, `architecturealignment`, `numstretch` matched on formatting or unrelated text.

**Conclusion:** there is **no actuarial / reserving / tail-calibration literature in this
corpus at all.** The p99-for-reserving decision cannot be informed from these 225 papers. That
is a scope limit of the index (it is an ML-methods index, not an actuarial one), and it means
the metric question stays a business decision rather than a literature question.

> **PARTLY SUPERSEDED 2026-10-08.** The sweep result above is correct — the query really did
> find nothing, for the reason given: *the index was ML-methods only.* What no longer holds is
> the reading. Instead of accepting the void, **28 actuarial papers were added to the index**
> under `actuarial / loss modelling`, and the corpus went 275 → 303 entries / 225 → 253 fetched.
>
> So: **the metric question is still a business decision** (nothing published evaluates a TFM
> on tail accuracy — Audit 2), but it is no longer *uninformed* by literature. The actuarial
> side now says what a tail estimate requires: a specified loss family and enough data
> ([actuarial.md](actuarial.md)).
>
> The general lesson: **a null result that is really a scope limit is a reason to widen the
> scope, not to stop.** Recorded alongside the two earlier sweeps whose nulls were query
> artefacts.

> **NARROWED AGAIN 2026-10-31 (#53), on the #47 block.** Two sentences of the 2026-10-08 note
> above are overtaken by the 48 comparison entries added in #47 — the `probabilistic` block and
> the nine new `actuarial / loss modelling` entries. The sweep result itself still stands; what
> follows is what the reading no longer covers.
>
> - "there is **no actuarial / reserving / tail-calibration literature in this corpus at all**"
>   — **false as written**, and it is the tail-calibration half that moved. Reserving now has
>   the chain-ladder standard-error and stochastic-reserving references indexed,
>   `distribution-free-calculation-of-the-standard-error-of-chain-ladder-reserve` (Mack 1993) and
>   `stochastic-claims-reserving-in-general-insurance` (England and Verrall 2002) — citation-only,
>   both paywalled. Tail calibration now has `quantile-regression-forests` (Meinshausen 2006),
>   `conformalized-quantile-regression` (1905.03222) and
>   `reliable-real-time-value-at-risk-estimation-via-quantile-regression-forest` (2602.01912),
>   plus the scoring and calibration theory in
>   `of-quantiles-and-expectiles-consistent-scoring-functions` (1503.08195),
>   `regression-diagnostics-meets-forecast-evaluation` (2108.03210) and
>   `decompositions-of-the-mean-continuous-ranked-probability-score` (2311.14122).
> - "the actuarial side now says what a tail estimate requires: **a specified loss family and
>   enough data**" — a specified family is *one* route, not the requirement. QRF (Meinshausen
>   2006) estimates conditional quantiles without assuming a family, conformalized quantile
>   regression (1905.03222) adds finite-sample coverage, and the 2026 VaR paper runs VaR by QRF
>   with conformal calibration. What survives from the original: **no TFM paper evaluates tail
>   accuracy**, so Audit 2's negative result is untouched.
> - "the metric question is still a business decision" narrows to **which functional** the
>   business wants priced. The quantile score (1503.08195) and T-calibration with reliability
>   diagrams (2108.03210) make the *evaluation* a literature question; the choice of functional
>   stays a decision.
>
> See [actuarial.md](actuarial.md) and the `probabilistic` block in `../README.md`.

---

# Sweep round 2 — summary of what changes

| Sub-question | Result |
|---|---|
| **A** ceiling fundamental? | Formal precedent exists but for a *different* obstruction. Do not overclaim. |
| **B** unblock hardware? | **`baps` — actionable.** CPU-only context compression; only route found that could unblock the replication on existing hardware. |
| **C** decomposition holds up? | No published counterpart — confirms novelty. **Bonus: `closedloop-priorselect` independently corroborates the closed prior line.** |
| **D** p99 right metric? | **Nothing found in the ML index** — but that was a scope limit, and 28 actuarial papers were added on 2026-10-08 to fill it. The metric question stays a business decision (no TFM paper evaluates tail accuracy) while the modelling question now has references. |

---

# CORRECTION (2026-10-08): the "zero-inflation is unclaimed" result was a bad sweep

The round-1 conclusion above — "**Nothing** in this index treats feature-linked zeros /
zero-inflated targets as an ICL decomposition problem" — is **WRONG**, and the way it was
wrong is worth recording because it will recur.

## The two errors

**1. `--min-hits 3` discarded every relevant paper.** A concept mentioned once or twice does not
survive a threshold of 3. The files that mention zero-inflation contain **1–2** hits each:

| paper | hits for `zero.inflat` |
|---|---:|
| `foundcause` | 2 |
| `tabcausal` | 1 |
| `avici` | 1 |
| `tabpfn-2-5` | 1 |
| `tabpfn-3` | 1 |

Re-running the identical round-1 command with the tool's **default** `--min-hits 1`:

```bash
python3 scripts/fm4sd_search.py grep "zero.?inflation" --min-hits 1 --max-results 10
```

...immediately surfaces papers the threshold had hidden.

**2. A morphological variant escaped the pattern entirely.** `zero.?inflation` requires the
string "…inflatio**n**". The TabPFN papers write **`zero_inflated`** (past participle), which does
not match. So the two papers most likely to be directly on topic were invisible to *both* the
threshold and the regex.

## What is actually in the corpus

Zero-inflation **is** present in tabular and causal FM *generator* designs:

- **`tabcausal`** (2605.31156) — its generator has an explicit rendering called
  **`zero_inflated_positive`**: "positive rendering with zero inflation (e.g., ≈10%)", alongside
  `censored_positive` and `missing_to_zero_identity`. This is a prior/generator that emits
  zero-inflated positive targets — the same *mechanism class* as this project's F19/F20 generator.
- **`foundcause`** (2606.17516) — post-processing "adds **zero-inflation or censoring** with
  probability 4%", listed among anti-shortcut perturbations applied to synthetic tasks.
- **`avici`** (2205.12934) — simulates "highly zero-inflated count matrices" for single-cell RNA
  (causal discovery; different domain).
- **`tabpfn-2-5` / `tabpfn-3`** — their use-case lists cite a paper that "modified TabPFN … in
  metagenomics, matching species abundance patterns with **synthetic priors**"
  ([OpenReview 3I0bVvUj25](https://openreview.net/forum?id=3I0bVvUj25)). Species abundance is
  canonically zero-inflated, and the modification is to the **synthetic prior** — the closest
  published analogue to this project's prior hypothesis.

## What this changes, and what it does not

**It does not** resurrect the prior line. None of the four does what this project did:

- none tests whether zero-inflation is **learnable** (F20's random-mask null: AUC 0.494 vs 0.491)
- none **calibrates the zero mask to a measured real zero-AUC** (F20/F30: 0.681–0.708)
- none asks whether **feature-linked** vs random zeros matter
- none measures whether a trained model is already **at the Bayes ceiling** (F32: 98.7%)
- `tabcausal`'s rate is ~10% zeros; the Spanish severity table is **88.9%**

So the project's contribution is narrower than "unclaimed", but it is still distinct: it is the
**calibration and the learnability test**, not the mere presence of zero-inflation in a prior.

**It does** mean the honest phrasing is:

> Zero-inflated targets appear in several tabular/causal FM generators, but no paper in this
> index studies whether zero-inflation is *learnable*, or calibrates the zero mask to real data.
> The F19/F20/F32 contribution is the calibration and the ceiling test, not the mechanism.

## Rules recorded

1. **Do not set `--min-hits` above the tool default for a first pass.** A null result from a
   thresholded search is a statement about the threshold, not about the literature. Round 1's
   headline negative result was entirely an artefact of `--min-hits 3`.
2. **Search morphological variants.** `zero-inflation` / `zero inflat*` / `zero_inflated` are the
   same concept; a single inflection misses papers. Prefer stems with `--pattern 'zero.?inflat'`.
3. **A negative sweep result must be re-run with a looser threshold before it is published.**
   Both errors above were caught only because the key negative result was double-checked against
   a direct `grep -rl`.
