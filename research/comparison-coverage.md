# Which comparison entries need digests, in what order?

Research for ticket #79 (child of #78). Branch `research/comparison-coverage`; this file is
the only thing on it. Read-only elsewhere: no change to `README.md`, the manifest, the 12
digests, or `scripts/`.

The question: of the 48 entries added by #47 to serve the paper's **comparison-results**
section, which need a digest, ranked by what the section cannot argue without — and which
deliberately get none.

## Answer

**None of the 48 has a digest today, and 12 of them should.** Eight are load-bearing in the
strict sense — without a close reading, a claim the section has to make is either unsupported
or overclaimed. Four more are the best available support for a claim that has no other
citation in the block. The other 36 get no digest, and the reasons sort into six kinds, not
one: seven cannot be digested (no payload), ten are time-series models the section does not
compare, and nineteen are papers whose claim the section cites but does not argue.

The ranking is not by topic completeness. It follows the order in which a reviewer would take
the section apart: *is the comparison fair* → *is the metric valid* → *is the difference real*
→ *why* → *what it does not prove*. The first digest is therefore the baseline-fairness paper,
not the calibration paper, because a comparison whose GBDT arm is a straw man is not repaired
by a better metric.

## Inventory of the block

48 entries, from `docs/plans/add-comparison-literature-2026-10-31.md` (the plan that landed
#47) and confirmed against `references/manifest.json`:

| block | entries | payload | note |
|---|---|---|---|
| `baselines` | 9 | 9 | 8 arXiv; LightGBM via the NeurIPS 2017 PDF |
| `probabilistic` | 11 | 11 | 10 arXiv; Meinshausen QRF via the JMLR PDF |
| `benchmark methodology` | 9 | 9 | all arXiv |
| `time series` → `forecasting` | 10 | 10 | all arXiv |
| `actuarial / loss modelling` | 9 | 2 | 7 payload-less (6 `skipped:unreachable:paywall`, 1 `unknown`) |
| **total** | **48** | **41** | |

**Digest coverage of the block: 0 of 48.** No digest takes any of these entries as its
subject. The 12 digests are about the tabular-model corpus (TabPFN, TabICL, TabDPT, TabPack,
nanoTabPFN, tacticl, finetuning, drift) and the 28-paper actuarial block added 2026-10-08 —
a different 28 from the 9 added here.

That "0" is worth stating carefully, because a slug search appears to contradict it. After
**#53** applied the #52 impact review, **21 of the 48 are now named inside an existing
digest**, as pointers (`references/summaries/actuarial.md:69,111,155`,
`baps.md:62–79`, `SWEEPS.md:106–159,343–357`, `tabicl.md:56`,
`modded-nanotabpfn.md`, `nanotabpfn.md`). Those mentions are citation rows written from
**arXiv abstracts** — #52 says so in its method note. They are not close readings of
`papers/<slug>/text.txt`, and they carry no quoted sentence, no section reference and no
table. So:

- **21 of 48** are *cited* in a digest; none is *digested*.
- **27 of 48** appear in no digest at all.
- **7 of 48** cannot be digested at all: `frees-2009`, `jørgensen-1994`, `lambert-1992`,
  `mullahy-1986`, `mack-1993`, `england-verrall-2002` (paywall) and `blier-wong-2021`
  (`unknown`, MDPI 403s a plain client). The digests already cite four of these by presence,
  which is the correct and only use.

De-duplication against the existing digests is therefore not "is this slug already
mentioned?" It is "does any digest contain a close reading of this paper?" The answer is no
for all 48, so the ranking is free to be about the section's argument, not about avoiding
overlap.

## The section's claims, as this repo records them

The paper itself is not in this repo, so the claim set is taken from what the research layer
already asserts. Each claim below is a sentence the comparison-results section has to defend,
with the place the repo states it.

| id | claim | recorded at |
|---|---|---|
| C1 | the TFM is competitive with / beats a GBDT on insurance severity-frequency data | `SWEEPS.md:240–260`; `actuarial.md:86–88` (baseline is depth-3, `n_estimators=4`) |
| C2 | the failure is at the **tail**: p99 error ratio swings 0.04 → 2.47 across subsamples | `baps.md:45–46` |
| C3 | the failure is **informational**, not a modelling miss — the checkpoint sits at 98.7% of the calibrated Bayes ceiling (F30/F32) | `closedloop-priorselect.md:39–51` |
| C4 | the distribution family is not the lever (F18) | `actuarial.md:48–61` |
| C5 | the two-part indicator + magnitude framing is contested, not established (F31) | `actuarial.md:92–94,144` |
| C6 | no published work evaluates a TFM on tail accuracy in insurance | `actuarial.md:149`; `SWEEPS.md:298` |
| C7 | the comparison protocol is defensible: tuning parity, no leakage, a stated decision rule, significance | `SWEEPS.md:98–121`; `modded-nanotabpfn.md:54` |

Two things follow immediately, and they shape the ranking:

- **The block is heaviest exactly where C1, C2 and C7 are.** Baselines, probabilistic and
  benchmark methodology are 29 of the 48 entries, and those three blocks map one-to-one onto
  the first three things a reviewer attacks.
- **C3 has no support in the block at all.** No entry among the 48 supplies a ceiling, a
  Bayes-error estimator, or a learnability test. If the section's central mechanistic claim is
  C3, no digest in this list will carry it; that claim rests on the project's own measurement
  and the existing `closedloop-priorselect` digest. Stated here so a digester does not go
  looking for it.

## The ranked list — 12 digests

Ranked by what the section cannot argue without. `text` is the extracted size in bytes
(`references/manifest.json`), given as a cost signal: it is what the reader must get through,
not a quality measure.

### Tier 1 — cannot argue the section without these (8)

| # | slug (id) | text | claim it supports | what breaks without it |
|---|---|---|---|---|
| 1 | `when-do-neural-nets-outperform-boosted-trees-on-tabular-data` (2305.02997) | 173 KB | **C1 + C7.** Does three jobs: TabPFN "outperforms all other algorithms on average" up to 3,000 training rows (external support for the headline); light GBDT tuning matters more than the NN-vs-GBDT family choice (the fairness standard); and GBDTs "are much better than NNs at handling skewed or heavy-tailed feature distributions" (the caution that makes our insurance result non-obvious rather than trivial). | "TFM beats GBDT" is a claim about an undertuned baseline, and the section has no answer to the heavy-tail objection that its own setting invites. |
| 2 | `of-quantiles-and-expectiles-consistent-scoring-functions` (1503.08195) | 101 KB | **C2.** A scoring function must be *consistent* for the functional being predicted; gives the mixture representation, the dominance check and Murphy diagrams. This is what makes a quantile score a ranking rather than an arbitrary ratio. | The p99 ratio (0.04 → 2.47) is an unvalidated statistic. The section cannot say a model is worse at p99, only that one number is bigger. |
| 3 | `regression-diagnostics-meets-forecast-evaluation` (2108.03210) | 3.8 MB | **C2 + C3.** The calibration theory for real-valued outcomes: conditional T-calibration, T-reliability diagrams, and `R* = (DSC − MCB)/UNC` that nests R². This is the definition behind "the model is miscalibrated at p99", and the instrument for a ceiling claim that is about calibration rather than accuracy. | "Miscalibrated" is an assertion with no definition, and the calibration contribution (F19/F20/F32) has no formal counterpart. Scope the digest to the calibration hierarchy and the diagram; the 3.8 MB is largely appendix. |
| 4 | `the-benchmark-lottery` (2107.07002) | 113 KB | **C1 + C7.** Relative algorithm rankings change when the task set changes. Any ordering the section reports is conditional on this claim sample, not a property of the models. | The section reports a general ranking from one dataset family, which is the exact overclaim the map's credibility lens is meant to prevent. |
| 5 | `lmem-for-post-hoc-analysis-of-hpo-benchmarking` (2408.02533) | 61 KB | **C7.** A mixed-effects model over benchmark runs as the significance test for a pairwise gap, with dataset meta-features as covariates. | The section cannot distinguish a real gap from noise. `SWEEPS.md:98` already flags a ~half-SD difference as possibly not a separation; without this the section repeats that error at the level of the headline. |
| 6 | `revisiting-deep-learning-models-for-tabular-data` (2106.11959) | 136 KB | **C7.** The comparison-protocol paper: prior work used different benchmarks and protocols, so models were not compared to each other; fixes a shared protocol and raises the baseline bar (a ResNet-like model that prior work omitted). | The GBDT arm is a straw man by construction. This is the paper a reviewer cites when they say "same tuning budget, please". |
| 7 | `decompositions-of-the-mean-continuous-ranked-probability-score` (2311.14122) | 140 KB | **C2 + C3.** Splits mean CRPS into miscalibration (MSC), discrimination (DSC) and uncertainty (UNC), isotonically, with non-negative components. This is the only tool in the block that attributes a *difference* to a cause. | The section can say one distributional model scores worse but not **why** — which is the difference between a result and a mechanism sentence. |
| 8 | `towards-foundation-models-for-insurance-risk-modelling` (2609.14576) | 118 KB | **C6 + framing.** The actuarial side's own review of FMs on insurance data (language, vision, geospatial, time series, tabular, scientific), which states the evaluation difficulty directly: final claim costs arrive late, large losses are rare, patterns may not transfer. | C6 ("no published work evaluates a TFM on tail accuracy") is a negative claim with no record of having looked, and the section has no citation that the field it addresses considers the question open. |

### Tier 2 — the best available support, no substitute in the block (4)

| # | slug (id) | text | claim it supports | why it is tier 2 |
|---|---|---|---|---|
| 9 | `the-actuary-and-ibnr` (Bornhuetter & Ferguson 1972) | 32 KB | **C1 + C4, as a mechanism.** The canonical prior-plus-data reserve estimator: blend an external prior with thin data and let the data move it. That is structurally what a foundation model does in context, with the prior learned instead of specified. | Not needed to *run* the comparison, but it is the cheapest way to say what the TFM's in-context behaviour *is* in actuarial vocabulary — and it is the only readable paper in the actuarial canon (the other eight are paywalled or meta). Uncited by any digest today. |
| 10 | `ngboost-natural-gradient-boosting-for-probabilistic-prediction` (1910.03225) | 69 KB | **C4.** The literature's distributional boosting arm: the parameters of the conditional distribution are the boosting targets, for any family and any scoring rule. F18's "the family is not the lever" was established on a *linear* Tweedie GLM; this is the nonlinear version, and it is runnable. | Needed only if the section defends C4 rather than asserting it. It is the comparator that closes the obvious hole in F18. |
| 11 | `conformalized-quantile-regression` (1905.03222) | 78 KB | **C2.** Valid finite-sample coverage with intervals adaptive to heteroscedasticity, without a distributional assumption. Turns "the tail is hard" into "we did not get coverage where a wrapper would". | The block's distribution-free existence proof. If the section only reports its own ratio, CQR is a citation; if it claims the tail is *unrecoverable*, CQR is the counterexample and the digest is mandatory. |
| 12 | `leakage-and-the-reproducibility-crisis-in-ml-based-science` (2207.07048) | 122 KB | **C7.** An 8-type leakage taxonomy from 329 papers in 17 fields, plus model info sheets for reporting. | The insurance split — temporal, target-encoded rating factors, postcode — is exactly where leakage hides. A digest that applies the taxonomy to our own pipeline is the one item here that makes the section *checkable* rather than better cited, which is the map's stated lens. |

**If only 8 can be done**, it is tier 1. If the two-week window allows 12, the order inside
tier 2 is 9 → 12 → 10 → 11: the BF framing and the leakage check change how the section is
*written*, NGBoost and CQR only change what it can *claim*.

## No digest needed — 36 entries

Six kinds of reason. Each bucket says what would have to change for it to move.

**A. No payload — a digest would be fabricated (7).**
`actuarial-applications-of-a-hierarchical-insurance-claims-model` (Frees 2009),
`fitting-tweedies-compound-poisson-model-to-insurance-claims-data` (Jørgensen 1994),
`zero-inflated-poisson-regression-with-an-application-to-defects` (Lambert 1992),
`specification-and-testing-of-some-modified-count-data-models` (Mullahy 1986),
`distribution-free-calculation-of-the-standard-error-of-chain-ladder-reserve` (Mack 1993),
`stochastic-claims-reserving-in-general-insurance` (England & Verrall 2002),
`machine-learning-in-p-and-c-insurance-a-review-for-pricing-and-reserving` (Blier-Wong 2021).
Six are `skipped:unreachable:paywall`; the seventh is `unknown` (MDPI 403s a plain client).
A digest of any of these would rest on an abstract and a title — the exact failure the
evidence standard (#80) exists to prevent. Cite by presence and title, as #52 already
requires. **Move if** a route opens (library access to ASTIN/BAJ/T&F, or an author preprint):
then Mack (the variance every reserving comparison is scored against) and England–Verrall
(the GLM/bootstrapped formulation) are the first two, and both would enter tier 1.

**B. The model, not the evidence (3).**
`xgboost`, `catboost`, `lightgbm`. These are the arms the section *runs*; their claim is
"this is the implementation", settled by the citation. A close reading of the CatBoost paper
does not tell the section anything about whether its CatBoost was tuned. **Move if** the
section reports a CatBoost hyperparameter choice that needs justifying from the paper
(ordered target statistics for high-cardinality rating factors is the plausible one).

**C. Subsumed by a stronger study already in the list (4).**
`why-do-tree-based-models-still-outperform-deep-learning` (Grinsztajn) — the canonical
tree-vs-DL result with three named mechanisms, but 2305.02997 is the larger, later and more
balanced statement and names the same inductive-bias mechanism; reading both would produce
one digest's worth of claim. `tabular-data-deep-learning-is-not-all-you-need` (Shwartz-Ziv) —
11 datasets, the weakest of the tree-vs-DL set, and already cited where it matters.
`well-tuned-simple-nets-excel-on-tabular-datasets` (Kadra) — the sharpest statement of the
tuning-artefact argument; carried for now by 2106.11959 (protocol) and 2305.02997 (tuning
beats family). **This is the first promotion** if a reviewer presses on baseline tuning, and
it is the one substitution I would defend least strongly.
`deep-neural-networks-and-tabular-data-a-survey` (Borisov) — orientation; a survey of a
debate the section settles with two primary papers.

**D. Numbers, not claims (3).**
`tabrepo-a-large-scale-repository-of-tabular-model-evaluations`,
`pmlb-a-large-benchmark-suite-for-machine-learning-evaluation-and-comparison`,
`openml-benchmarking-suites`. The section uses these to *check* a number, not to argue a
proposition: TabRepo's tuned evaluations are the cross-check for the GBDT arm, PMLB and
OpenML define the suite. A digest of an evaluation store is a data-extraction job, not a
close reading. **Move if** the section re-ranks TabRepo's precomputed predictions itself —
then TabRepo's protocol (folds, budgets, which 200 datasets) becomes a claim.

**E. Reporting mechanics, cited not argued (3).**
`show-your-work-improved-reporting-of-experimental-results` (tuning-budget curves),
`improving-reproducibility-in-machine-learning-research` (the checklist),
`amlb-an-automl-benchmark` (the worked whole-pipeline protocol). AMLB is the closest to
load-bearing: fixed folds, a shared time budget, framework-failure accounting and
Bradley–Terry analysis are exactly what a two-model comparison needs. It is out because the
section compares two named models, not a pipeline search. **Move AMLB if** the section adds
an ensemble or AutoML arm; move Show-Your-Work if it makes a tuning-budget claim rather than
a tuning-parity claim.

**F. Recipe or family statement, not a comparison result (4).**
`accurate-uncertainties-for-deep-learning-using-calibrated-regression` (Kuleshov) — the
recalibration procedure; 2108.03210 supplies the definition and the diagram, which is the
claim, so the procedure is a citation.
`easy-uncertainty-quantification-easyuq` — turns any point predictor into a calibrated
distribution; it is a *method to run* (the fair distributional arm on a GBDT), not a claim to
argue. NGBoost already supplies the distributional-competitor arm.
`bayesian-structured-additive-distributional-regression` (Klein) — "every parameter gets a
predictor" is the statistical family the two-part framing sits in, but it is a modelling
choice, and C5's contest is already carried by in-corpus actuarial papers
(`actuarial.md:92–94`).
`distribution-free-predictive-inference-for-regression` (Lei 2018) — the regression-conformal
reference, subsumed by CQR's guarantee for the claim the section makes.
**Move EasyUQ if** the section keeps a point-estimate GBDT arm after review criticism, or
Klein if the section states the distributional-regression family as its own contribution.

**G. Estimator and application, not the claim (2).**
`quantile-regression-forests` (Meinshausen 2006) — the canonical distribution-free conditional
quantile estimator, but its content for this section is textbook and CQR carries the coverage
claim. `reliable-real-time-value-at-risk-estimation-via-quantile-regression-forest` (2026) —
QRF + conformal on a tail risk measure, the nearest thing in the block to the section's own
move, and the newest and least-reviewed paper here. **Move it the moment** the section adopts
a VaR / tail-capital framing rather than a p99-error framing; at that point it is a stronger
citation than CQR alone.

**H. Time series — the whole 10 (10).**
`moirai`, `moirai-2`, `lag-llama`, `timegpt-1`, `timesfm`, `toto`, `moment`, `time-moe`,
`sundial`, `ts-fm-survey`.
These are forecasting foundation models evaluated on time-series corpora. None tests a frozen
**tabular** TFM under drift, which is the only temporal claim the section has — and that claim
is already carried by the `temporal-tabular-shift` digest, whose conclusion is explicit: use
it as a different obstruction, not as proof that the ceiling is fundamental. A digest of
Moirai or TimesFM would support a comparison the section does not make, and the block's own
research note says its job was to answer "what did `tirex-2` beat?" — ancestry, not argument.
**Move `ts-fm-survey` first** if the section grows a forecasting subsection (it defines the
taxonomy and evaluation protocol the nine are scored under); then the three models a
zero-shot table cannot omit — `moirai`, `timesfm`, `timegpt-1`.

## Order of work, in four sittings

The ranking is by claim, but a digester spends a session per sitting, so the batches are
grouped by the question they answer, not by category:

1. **Fairness** — 2305.02997, 2106.11959, 2107.07002, 2408.02533. One sitting, because the
   four together are the section's method paragraph, and they argue with each other
   (parity standard vs lottery vs significance). 483 KB.
2. **Instrument** — 1503.08195, 2108.03210, 2311.14122. The quantile score, the calibration
   definition, the decomposition. 4.0 MB, of which ~3.7 MB is one appendix; scope 2108.03210
   to its calibration hierarchy and reliability diagrams.
3. **Framing** — 2609.14576, BF 1972. What the TFM is, in actuarial terms, and what the field
   it addresses already says. 150 KB, and the cheapest pair in the list.
4. **Arms and checkability** — 1910.03225, 1905.03222, 2207.07048. The two comparators and
   the leakage checklist. 270 KB.

Batches 1 and 3 are the ones that change sentences. Batch 2 is the one that changes numbers.

## What this does not decide

- **Per-paper vs per-claim digests.** The 12 above are papers; the load-bearing claims are 7.
  Several papers serve one claim (2, 3 and 7 all serve C2) and one paper serves three (1).
  Whether that becomes three per-claim digests or one per-paper digest with a claim index is
  #80's call, not this ticket's. If per-claim wins, the first three digests are C1, C2 and
  C7 and the paper list above is just their source set.
- **Whether a digest is worth its cost.** This ranks need, not value for money. 2108.03210 is
  3.8 MB for a claim that may be one sentence; BF 1972 is 32 KB for the paper's central
  analogy. A digester with one session should take #1 and #9 before #3.
- **Retrieval.** None of this assumes grep stops working. Every claim above is a targeted
  read of a named paper, which is the case #81 should find grep sufficient for; the queries
  that would need more ("who evaluates p99") are sweeps, not digests.
- **New literature.** Nothing here proposes an entry. Where the block has a hole — C3, the
  ceiling — the answer is the project's own measurement, not another paper.

## Method

Read: the #47 plan (`docs/plans/add-comparison-literature-2026-10-31.md`) for the block's
composition; the #47 commit (`8a03b4a`) for the 48 rows; the five gap research files
(`research/gap-baselines`, `-probabilistic`, `-benchmark`, `-time-series-fm`,
`-actuarial-methods`) for why each entry was approved; the #52 impact review
(`research/digest-impact-2026-10-31.md`) and #53 (`94be6e2`) for which entries the digests now
cite and in what form; all 14 files in `references/summaries/` for the claim set and for
de-duplication; `references/manifest.json` for `fetch_status` and `text_bytes` of all 48.

Claims about what the 12 proposed digests would support were checked against the papers'
**arXiv abstracts**, read back through the arXiv Atom API on 2026-10-31 in one batch
(`export.arxiv.org/api/query?id_list=…`), not from memory or titles: 2305.02997 (the 176-dataset
/ 19-algorithm result, the TabPFN "outperforms all other algorithms on average" sentence, and
the heavy-tailed-feature finding), 1503.08195 (consistency, dominance, Murphy diagrams),
2108.03210 (T-calibration, T-reliability diagrams, `R*`), 2311.14122 (MSC/DSC/UNC),
1905.03222 (finite-sample coverage, heteroscedasticity), 1910.03225 (parameters as boosting
targets, any family, any scoring rule), 2106.11959 (protocol heterogeneity, raised baseline
bar), 2107.07002 (rankings change with the task set), 2408.02533 (LMEM significance over
benchmark runs), 2207.07048 (8 leakage types, 329 papers, 17 fields), 2609.14576 (the
insurance FM review and its stated evaluation difficulties). BF 1972 is **not** arXiv; its
description is taken from `research/gap-actuarial-methods.md`, which verified the DOI/PDF and
read the embedded metadata, and from `the-actuary-and-ibnr`'s fetched 15-page CAS scan
(`fetch_status: ok`, 31,649 bytes). No quote in this file is attributed to a paper whose text
was not available.

Nothing here is a digest, a manifest change, a README edit, or a script change.
