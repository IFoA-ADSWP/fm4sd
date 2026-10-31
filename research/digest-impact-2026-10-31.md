# Digest impact review — the 48 comparison entries (#47)

Ticket: #52. Branch: `research/digest-impact` (never merged). Date: 2026-10-31.
Subject: `references/summaries/` (12 digests + `SWEEPS.md` + `README.md`) against the 48
entries added by #47 — `baselines` (9), `probabilistic` (11), `benchmark methodology` (9),
`time series / forecasting` (10), `actuarial / loss modelling` (9). Manifest: 431 entries,
381 fetched.

**No digest is edited here.** The table is the change set.

## How to read this

Each row is one claim in one digest, with the line it sits on, the entry that bears on it,
and a verdict:

- **cite it** — the claim stands, and an entry now supplies the reference it lacked.
- **narrow it** — the claim is still true in a shrunken form, and the current wording
  overstates it.
- **no change** — checked; nothing in the 48 moves it. Listed in the second half, on purpose.

Eighteen claims move; the rest do not. The distribution is the honest answer: this block was
chosen to support comparisons the repo already makes, so most of its work is *supplying
citations*, and the claims that actually shift are the ones about **gap** and about
**baselines**, which are the two things the block is strongest on.

## The table

| # | digest file:line | quoted claim | verdict | entry that bears on it | proposed edit |
|---|---|---|---|---|---|
| 1 | `actuarial.md:70` | "it is determined that **CatBoost is the best** for developing auto claim frequency models based on predictive performance" | **cite it** | `catboost` (1706.09516) in `baselines` | Append the CatBoost library citation; it is now in the index rather than named-only. |
| 2 | `actuarial.md:86` | "an independent finding that **CatBoost** is the right frequency model … the actuarial ML literature picks CatBoost" | **narrow it** | `catboost`; `when-do-neural-nets-outperform-boosted-trees…` (2305.02997); `why-do-tree-based-models-still-outperform…` (2207.08815) | "the actuarial ML literature" → "one paper, two datasets, three libraries"; add that light GBDT tuning outweighs library choice at tuning parity. |
| 3 | `actuarial.md:88` | "our baseline is depth-3/`n_estimators=4` and the actuarial ML literature picks CatBoost" | **narrow it** | `when-do-neural-nets-outperform…`; `why-do-tree-based-models-still-outperform…` | Say plainly that a depth-3, 4-tree GBDT is far below the tuning-parity standard those benchmarks use, so "beats the GBDT" needs that qualifier. |
| 4 | `actuarial.md:62` | "it is the cheapest untested variant in the repo: a Tweedie *objective inside a GBDT*" | **narrow it** | `ngboost-…` (1910.03225); `bayesian-structured-additive-distributional-regression` (1509.05230); *(also `insurance-premium-prediction-via-gradient-tree-boosted-tweed`, in-corpus since 2026-10-08)* | "untested" is true only for us: name Yang et al. 2015 (GBDT-Tweedie, in this corpus) and NGBoost as the published distributional-boosting arm. |
| 5 | `actuarial.md:125` | "None of these papers study a **tabular foundation model** … the actuarial literature does not evaluate TFMs" | **narrow it** | `towards-foundation-models-for-insurance-risk-modelling` (2609.14576, fetched) | Split the two clauses: the actuarial literature now *reviews* TFMs for insurance; it still publishes no tail-accuracy evaluation. |
| 6 | `tabicl.md:30` | "beats both TabPFN v2 and **CatBoost**" | **cite it** | `catboost` (1706.09516) | Cite the CatBoost entry at the comparator. |
| 7 | `tabicl.md:51` | "the closest published support for the observation that TFMs beat GBDT once data is not scarce" | **narrow it** | `when-do-neural-nets-outperform…` (2305.02997, 176 datasets / 19 algorithms) | "closest published support" is now false: cite the larger study and keep only TabICL's own >10K result. |
| 8 | `nanotabpfn.md:43` | "Matches k-NN / decision tree / random forest (default scikit-learn config)" | **cite it** | `why-do-tree-based-models-still-outperform…`; `tabular-data-deep-learning-is-not-all-you-need` (2106.03253) | Mark the comparison as tuning-unaware: default-config baselines are not the literature's standard. |
| 9 | `modded-nanotabpfn.md:54` | "Target: **≤ 0.8068462330697953** val avg ROC AUC (RF-matched)" | **narrow it** | `when-do-neural-nets-outperform…`; `tabrepo-…` (2311.02971) | Say the target is RF-parity, not GBDT-parity — ~98× to a bar a tuned GBDT clears — and point at TabRepo's tuned evaluations. |
| 10 | `SWEEPS.md:98` | "Record 10 median is 0.79 min, record 11 median 0.76 min … roughly half a standard deviation — it may not be a real separation" | **cite it** | `lmem-for-post-hoc-analysis-of-hpo-benchmarking` (2408.02533) | Name the instrument: compare per-task results with a mixed-effects model, not two medians. |
| 11 | `SWEEPS.md:107` | "Target … chosen to match Random Forest on the same subsampled TabArena evaluation" | **cite it** | `the-benchmark-lottery` (2107.07002); `tabrepo-…` | Add that a single-suite target is a benchmark-lottery draw, and that TabRepo holds the tuned-model comparison. |
| 12 | `SWEEPS.md:143` | "`beyondarena` … exists because TabArena itself was found to saturate — worth checking before treating a TabArena AUC as a meaningful target" | **cite it** | `the-benchmark-lottery`; `tabrepo-…` | The caution now has a citation; add it rather than leaving the claim unsupported. |
| 13 | `SWEEPS.md:242` | "the two-part framing … has **no published counterpart** in this index" | **narrow it** | `zero-inflated-poisson-regression-…` (Lambert 1992); `specification-and-testing-of-some-modified-count-data-models` (Mullahy 1986) | "no published counterpart" → "no **ICL** counterpart"; the canonical hurdle/ZI models are now in the index (citation-only). |
| 14 | `SWEEPS.md:288` | "there is **no actuarial / reserving / tail-calibration literature in this corpus at all**" | **narrow it** | `quantile-regression-forests`; `conformalized-quantile-regression`; `of-quantiles-and-expectiles…`; `regression-diagnostics-meets-forecast-evaluation`; `mack`; `england-and-verrall` | Falsified as written: extend the in-file "partly superseded" note to cover the calibration and scoring-rule half, which is new in #47. |
| 15 | `SWEEPS.md:299` | "the actuarial side now says what a tail estimate requires: a specified loss family and enough data" | **narrow it** | `quantile-regression-forests` (2006); `conformalized-quantile-regression` (1905.03222); `reliable-real-time-value-at-risk…` (2602.01912) | A specified family is *one* route: QRF and conformal quantile regression give distribution-free tail estimates with coverage guarantees. |
| 16 | `SWEEPS.md:298` | "the metric question is still a business decision (nothing published evaluates a TFM on tail accuracy)" | **narrow it** | `of-quantiles-and-expectiles…` (1503.08195); `regression-diagnostics-meets-forecast-evaluation` (2108.03210); `decompositions-of-the-mean-crps` (2311.14122) | Keep "no TFM evaluates tail accuracy"; drop "business decision" for *evaluation* — the quantile score and T-calibration give a standard instrument, and only the choice of functional stays a decision. |
| 17 | `baps.md:56` | "There is **no regression and no tail calibration**" | **cite it** | `accurate-uncertainties-for-deep-learning-using-calibrated-regression` (1807.00263); `regression-diagnostics-meets-forecast-evaluation` | Name what is missing — calibrated distributional regression and T-reliability — rather than only asserting its absence. |
| 18 | `baps.md:62` | "'Reliable calibration' is ECE on balanced-ish classification, not tail calibration" | **cite it** | `accurate-uncertainties-…`; `regression-diagnostics-meets-forecast-evaluation`; `decompositions-of-the-mean-crps` | Make the caveat actionable: the project should report a quantile reliability diagram or pinball loss, not ECE. |

Same-document duplicates, fixed by the row above rather than separately: `actuarial.md:120`
(the "CatBoost is the reference frequency model" row of its summary table — row 2);
`modded-nanotabpfn.md:93` ("Records 2–6 target *matching* baseline predictive performance" —
row 9); `SWEEPS.md:316` (the round-2 summary row "The metric question stays a business
decision" — row 16).

## What actually changes a claim

Three findings are load-bearing enough to restate in prose.

**1. "TFMs beat GBDT once data is not scarce" is now a contested generalisation, not a
supported one.** `tabicl.md:51` calls TabICL's >10K result "the closest published support"
for it. `2305.02997` is a larger published study (19 algorithms, 176 datasets) whose headline
is the opposite framing — the NN/GBDT gap is often negligible, light GBDT tuning matters more
than the family choice, and TabPFN's win is measured at ≤3,000 training rows. TabICL's own
result is untouched; the repo's *inference* from it is not. This matters because the same
paper finds GBDTs are "much better than NNs at handling skewed or heavy-tailed feature
distributions" — which is the insurance severity setting, not an exotic one.

**2. The GBDT the project beats is not the GBDT the literature benchmarks.** `actuarial.md:88`
records the baseline as depth-3 / `n_estimators=4`; `modded-nanotabpfn.md:54` records a
Random-Forest-matched ROC AUC target. Both are below the tuning-parity standard that the new
`baselines` block sets (`2207.08815` benchmarks "accounting for both fitting models and
finding good hyperparameters"; `2106.03253` shows XGBoost "requires much less tuning" than the
deep models it beats; `2106.11189` shows tuned plain MLPs excel). None of this overturns F30
or F32 — a feature-set information ceiling does not care which model is tuned. It does mean
"beats the GBDT" cannot be asserted without saying which GBDT, and the honest unit is
"beats a depth-3 GBDT" until a tuned CatBoost arm is run.

**3. The p99 metric question is no longer only a business decision.** `SWEEPS.md:298–301`
says the tail estimate "requires a specified loss family and enough data" and that the metric
question "stays a business decision". The `probabilistic` block supplies four things that
change the reading: distribution-free tail estimation with coverage (QRF 2006, CQR 2019,
VaR-by-QRF with conformal calibration 2026), the consistent scoring function for a quantile
(`1503.08195`), a calibration theory for regression and quantiles — T-calibration, reliability
diagrams, the R\* coefficient (`2108.03210`) — and a CRPS decomposition into miscalibration /
discrimination / uncertainty (`2311.14122`). "No TFM paper evaluates tail accuracy" survives.
"The question cannot be informed from this literature" does not: the instrument now exists,
and what remains a decision is *which functional* the business wants priced.

## Checked and left alone

Sorted by file. Every one of these was read against the 48; the reason is given so the next
reviewer does not redo the work.

| digest:line | claim | why no change |
|---|---|---|
| `actuarial.md:40` | "The tail is not universally unrecoverable"; line drawn at sample size | QRF/conformal add a nonparametric route but do not move the sample-size line; the 5,950-claimant question is untouched. |
| `actuarial.md:57` | "F18's conclusion is established for the linear family only" | Already correctly narrowed; row 4 only adds the published arms. |
| `actuarial.md:81` | F31 independence vs `corr(count, severity) = +0.348` | Nothing in the 48 tests the $p$–$\mu$ coupling. |
| `actuarial.md:92` | Tobit is a special case of probit-hurdle | The new hurdle entry (Mullahy 1986) is the origin, not a counter-result, and is paywalled. |
| `actuarial.md:107` | "Same shape as F32 … different domain" | Still the right caveat. |
| `baps.md:8`, `baps.md:74` | "the only paper found … that speaks directly to a live blocker" | Still true of the corpus; no entry among the 48 proposes a CPU-only route. |
| `closedloop-priorselect.md` (all) | three-condition regularity; ensemble dilution; support-boundary theorem | No entry in the 48 concerns prior injection, PFN families, or causal-prior transfer. |
| `finetuningtfm.md` (all) | full finetuning wins; unstable on temporal shift + wide tables | The `baselines` block is about pretrained-vs-tree comparisons, not finetuning. |
| `modded-nanotabpfn.md:80` | "closest published precedent to a nanoTabPFN pretraining speedrun" | Still true; TabRepo is a model-evaluation corpus, not a speedrun. |
| `nanotabpfn.md:31` | 80,000 × 150 × 5 hard cap | A property of the prior dump; no entry bears. |
| `nanotabpfn.md:57` | "the eval target is weak evidence about the model being good" | Already the correct read — row 9 sharpens it, it does not correct it. |
| `tabdpt.md:22` | first scaling-law analysis for TFMs | TabRepo/LMEM are evaluation corpora, not scaling laws. |
| `tabdpt.md:43` | "Beats TabPFN v2 on CC18 accuracy; competitive elsewhere" | The digest already separates the win from the "elsewhere"; adding a benchmark-lottery citation is optional, not a change. |
| `tabdpt.md:52` | "Nobody in the ledger seems to have tried this" | Scoped to the speedrun ledger, not the literature. |
| `tabicl.md:48` | prior-sampling lever "nobody in the ledger has tried" | Scoped to the ledger. |
| `tabpack.md:16` | "on par with extensively tuned prior methods at default settings" | Already the *correct* comparison direction (default vs tuned); TabRepo would let a reader check it, but no wording changes. |
| `tabpfnv2closerlook.md` (all) | high-dim / many-category / large-scale failures | `2207.08815` is adjacent on inductive bias but says nothing about TabPFN v2 specifically. |
| `tacticl.md` (all) | ICT→IWL transition; 85% layer substitution | Nothing in the 48 concerns compression or adapters. |
| `temporal-tabular-shift.md` (all) | identifiability wall; L² projection wall | The 10 time-series entries are forecasting FMs on time-series corpora; none tests a frozen tabular TFM under drift. |
| `SWEEPS.md:31` | zero-exploitation "genuinely unclaimed" | Already corrected in-file at `SWEEPS.md:320`; nothing in the 48 reverses the correction. |
| `SWEEPS.md:180` | A2: "formal precedent … but for a *different* obstruction" | Unchanged, and still the right caution. |
| `SWEEPS.md:223` | B2: baps is the only direct answer to the hardware wall | Still true; the 10 time-series entries are not efficiency work. |
| `SWEEPS.md:320` | the zero-inflation correction and its three rules | Stands as written. |
| `summaries/README.md` (all) | round-1/round-2 coverage tables | Derived prose about digests, not a claim about the literature. Edits follow the digests, not this review. |

Two rows I expected to find and did not: **no digest makes a CRPS claim** (so the
`probabilistic` block's CRPS material lands only in `SWEEPS.md:298`), and **no digest makes a
calibration claim about regression** (so Kuleshov 2018 lands only as the name of what BAPS
does not do). The absence is itself the finding: the repo reasons about tail error in
ratios (`p99 ratio 0.04 → 2.47`) and never in a proper scoring rule. If one thing is taken
out of this review beyond the table, it is that the p99 ratio has a citable alternative.

## Constraints on the change set

- **Seven of the nine new actuarial entries are payload-less.** `frees-2009`,
  `jørgensen-1994`, `lambert-1992`, `mullahy-1986`, `mack-1993`, `england-and-verrall-2002`
  are `skipped:unreachable:paywall`; `blier-wong-2021` is `skipped:unreachable:unknown`.
  Only `towards-foundation-models-for-insurance-risk-modelling` (arXiv) and
  `the-actuary-and-ibnr` (CAS scan) can be read. Rows 5, 13 and 14 may therefore cite those
  entries by presence and title — they must **not** quote them. `README.md` already says this
  ("seven are DOI-only and citation-only"), but the distinction is easy to lose in a digest.
- **No quoted line above is a digests' own measurement.** F30/F31/F32/F18/F19/F20 figures are
  the private repo's; this review only touches how the digests read the external literature
  against them.
- **One row (4) is outside the 48.** Yang et al. 2015 (`insurance-premium-prediction-via-
  gradient-tree-boosted-tweed`) has been in the corpus since 2026-10-08 and is exactly the
  "Tweedie objective inside a GBDT" that `actuarial.md:62` calls untested. Flagged rather
  than smuggled in, because it changes the reading of an "untested variant" claim.
- **Verdicts are deliberately conservative.** Where an entry corroborates a claim without a
  digest needing to change (e.g. `tacticl`, `closedloop`), the verdict is "no change", not
  "cite it" — a citation that does not alter a sentence is noise.

## Method

Read: all 14 files in `references/summaries/`; the `baselines`, `probabilistic`, `benchmark
methodology`, `time series / forecasting` and `actuarial / loss modelling` blocks of
`README.md` (`:147–:305`); `references/manifest.json` for `fetch_status` of every entry cited;
the #47 commit (`8a03b4a`) to confirm which 48 entries are new. `papers/` is absent in this
clone, so new-entry content was verified against the arXiv abstract pages for the papers cited
by claim — `2609.14576`, `2602.01912`, `2305.02997`, `2207.08815`, `2106.11189`, `2106.03253`,
`1910.03225`, `1807.00263`, `1905.03222`, `1503.08195`, `2108.03210`, `2311.14122`,
`2311.02971`, `2107.07002`, `2408.02533`, `2207.07048`, `1811.10192`, `2307.07771`,
`1508.06378`, `2608.09725`, `2402.02592` — not from titles alone. Paywalled actuarial entries
are cited by presence only, as above.

No digest, `README.md`, manifest or script is modified on this branch.
