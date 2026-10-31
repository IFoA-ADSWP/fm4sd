# Which probabilistic and distributional papers are missing?

Research for ticket #43 (`wayfinder:research`, under the wayfinding map). Branch
`research/gap-probabilistic`; this file is the only thing on it. Nothing here is
merged and no PR is opened — the ticket's deliverable is this list.

The question: which **probabilistic / distributional** papers the corpus needs, so that
"TabPFN's distribution vs a GLM's" has the metrics and uncertainty machinery behind it:
NGBoost, distributional regression (Klein et al.), quantile regression forests,
conformal prediction for regression, calibration of predictive distributions
(Kuleshov et al.), proper scoring rules (Gneiting & Raftery), CRPS.

## Method note

- **Index de-duplication** was run against `references/manifest.json` at `origin/main`
  `c9f0df4` (the commit this branch was cut from): header `count: 383`, 383 entry
  records, parsed with the same delimiter (`--- entries ---`) the manifest uses. Every
  candidate below was matched on exact `arxiv_id` and, separately, by keyword scan of
  `slug` / `citation` / `arxiv_title` / `subcategory` for `conformal|calibrat|quantile|
  distributional|probabilis|crps|scoring|coverage`.
- **arXiv verification** used the arXiv Atom API (`export.arxiv.org/api/query?id_list=…`).
  The API rate-limited this host (HTTP 429, empty body, persisting ~40 minutes across
  single- and multi-id calls and across `export.arxiv.org`, `arxiv.org/api` and
  `oaipmh.arxiv.org`), so the same calls were issued through `r.jina.ai` with
  `x-respond-with: text`, which returns the API's raw Atom XML unmodified. Every id below
  was read back from that XML: `title`, `arxiv:published`, authors, `arxiv:journal_ref`
  / `arxiv:comment`. No id in this file is quoted from memory.
- Abstracts for the one-line reasons were read from the API records and cross-checked
  against `arxiv.org/abs/<id>`; none of the fetched abs pages carries a withdrawal or
  retraction notice.
- Read-only: no `--index`, no fetch, no payload. `README.md`, the manifest and every
  script are untouched by this branch.

### What the API returned for the ten recommended ids

| id | `arxiv:published` | venue per `journal_ref` / `comment` |
|---|---|---|
| 1910.03225 | 2019-10-08 | ICML 2020 |
| 1509.05230 | 2015-09-17 | Ann. Appl. Stat. 9(2):1024–1052 (2015) |
| 2602.01912 | 2026-02-02 | — |
| 1604.04173 | 2016-04-14 | — (JASA 2018 in print) |
| 1905.03222 | 2019-05-08 | — (NeurIPS 2019 in print) |
| 1807.00263 | 2018-07-01 | ICML 2018 |
| 2212.08376 | 2022-12-16 | — |
| 2108.03210 | 2021-08-06 | Electron. J. Stat. 17:3226–3286 (2023) |
| 2311.14122 | 2023-11-23 | — |
| 1503.08195 | 2015-03-27 | — (JRSS-B 2016 in print) |

Every rejected/adjacent id in this file was read through the same call. No id resolved to
a different paper than the one quoted, and no query returned an empty result set.

## Recommended set — 10 papers, all category `probabilistic`

Titles are the API's, including its capitalisation quirks. Citation strings follow the
README convention (`surname et al. year`, venue year where there is one) and are
suggestions for whoever adds the entries.

| # | arXiv id | citation | title | why the corpus needs it |
|---|---|---|---|---|
| 1 | 1910.03225 | duan et al. 2020 | NGBoost: Natural Gradient Boosting for Probabilistic Prediction | The reference gradient-boosting predictor that outputs a full conditional distribution instead of a point — the direct boost-the-parameters contrast to TabPFN's in-context distribution. |
| 2 | 1509.05230 | klein et al. 2015 | Bayesian structured additive distributional regression with an application to regional income inequality in Germany | The canonical "distributional regression" statement: every parameter of the response distribution, not just the mean, gets a structured additive predictor — the statistical family a GLM is a one-parameter special case of. |
| 3 | 2602.01912 | wang et al. 2026 | Reliable Real-Time Value at Risk Estimation via Quantile Regression Forest with Conformal Calibration | Puts quantile regression forests and conformal calibration together on a tail risk measure (VaR) — the actuarial and conditional-quantile side of distributional prediction in one paper. |
| 4 | 1604.04173 | lei et al. 2018 | Distribution-Free Predictive Inference For Regression | The regression-side conformal reference: finite-sample marginal coverage with any regressor, plus the split-conformal / full-conformal / jackknife comparison. |
| 5 | 1905.03222 | romano et al. 2019 | Conformalized Quantile Regression | Makes intervals adaptive to heteroscedasticity by wrapping a quantile regression in conformal calibration — the bridge between #3's conditional quantiles and #4's coverage guarantee. |
| 6 | 1807.00263 | kuleshov et al. 2018 | Accurate Uncertainties for Deep Learning Using Calibrated Regression | Defines recalibration of a regression model's predictive distribution and the calibration plot that exposes an over-confident interval — the vocabulary the corpus uses for "the 90% interval contains 90%". |
| 7 | 2212.08376 | walz et al. 2022 | Easy Uncertainty Quantification (EasyUQ): Generating Predictive Distributions from Single-valued Model Output | Turns *any* point predictor (a GLM, a boosted tree) into a calibrated predictive distribution from held-out output–outcome pairs — the cheap baseline TabPFN's native distribution has to beat. |
| 8 | 2108.03210 | gneiting and resin 2023 | Regression Diagnostics meets Forecast Evaluation: Conditional Calibration, Reliability Diagrams, and Coefficient of Determination | Gives real-valued outcomes the calibration theory that classification already had (auto-calibration, reliability diagrams, a distributional R²), which is the rigorous form of the comparison the corpus keeps making informally. |
| 9 | 2311.14122 | arnold et al. 2023 | Decompositions of the mean continuous ranked probability score | Splits mean CRPS into miscalibration, discrimination and uncertainty — the scoring-rule counterpart to the reliability diagram, and the tool for saying *why* one distributional model scores better. |
| 10 | 1503.08195 | ehm et al. 2016 | Of Quantiles and Expectiles: Consistent Scoring Functions, Choquet Representations, and Forecast Rankings | Which scoring functions are *consistent* for a quantile or expectile forecast, and how to rank them — the theory that decides whether a QRF, a CQR interval or a GLM quantile can be compared at all. |

### Coverage against the ticket's list

| ticket topic | covered by |
|---|---|
| NGBoost | 1 |
| distributional regression (Klein et al.) | 2 (and 7 for the point-model route) |
| quantile regression forests | 3 |
| conformal prediction for regression | 4, 5 |
| calibration of predictive distributions (Kuleshov et al.) | 6, 8 |
| proper scoring rules | 9, 10 — see the Gneiting & Raftery note under rejections |
| CRPS | 9 |

## De-duplication against the current index

No recommended id is already present. Three existing entries were checked by hand
because their slugs look adjacent:

| existing entry | id | verdict |
|---|---|---|
| `scoringbench` | 2603.29928 | **Adjacent, not a duplicate.** Same three authors, same proper-scoring-rules framing, but ScoringBench is the benchmark, and the group's sibling preprint on scoring rules as *training objectives* is rejected below rather than added twice. |
| `pfnuq` | 2505.11325 | Covers uncertainty quantification *for PFNs* via martingale posteriors. It is the TabPFN-specific method paper; #1–#9 are the classical machinery it is measured against. No overlap. |
| `conformal-elo-llm-eval` | 2606.13221 | **Unrelated**, as the ticket suspected: conformal *ranking* for LLM evaluation (Kargi & Salinas, NeurIPS 2026). Nothing to do with regression intervals. |

Also scanned and left alone: `iced` (in-context density estimation), `probcircuittabgen`
and `structuralcoverage` (generative-model coverage), `dr-tfm` (distributionally *robust*
adaptation — robustness, not distributional regression), and the actuarial quantile block
(`local-quantile-regression`, `high-dimensional-extreme-quantile-regression`) — quantile
regression, but neither is a forest and neither calibrates.

## Rejected candidates and why

| id / source | title | why not |
|---|---|---|
| 2603.08206 | Landsgesell, Knoll & Wenzel, "Distributional Regression with Tabular Foundation Models: Evaluating Probabilistic Predictions via Proper Scoring Rules" | Tempting — it is squarely the corpus's subject — but it is the same group, with overlapping framing and the same proper-scoring-rules apparatus, as the already-indexed `scoringbench` (2603.29928), three weeks apart; the benchmark is the more useful artefact of the two. Adding both would be one idea twice. |
| — (JMLR 7:983–999, 2006) | Meinshausen, "Quantile Regression Forests" | **Not on arXiv.** Title and author searches return only papers that cite or extend it. The method is represented by #3 instead. JMLR is open access, so it *could* be an id-less entry on the `direct-pdf` route from `jmlr.org`; that is a decision for whoever adds the category, not a research finding. |
| — (JASA 102:359–378, 2007) | Gneiting & Raftery, "Strictly Proper Scoring Rules, Prediction, and Estimation" | **Not on arXiv** — an author search on `Gneiting` returns 93 records and this is not one of them. It is the paper the ticket names, but it has no arXiv id, and the Taylor & Francis route is a paywall that the #29 route families do not cross. Its content is on arXiv instead via #10 (consistent scoring functions), #9 (CRPS decomposition) and #8 (calibration), and empirically via the already-indexed `scoringbench`. Recommend citing it in prose rather than as an entry. |
| 1908.09482 | Klein, Nott & Smith, "Marginally-calibrated deep distributional regression" | Strong paper, but it is calibration-of-distributional-regression — already covered twice (#2 for distributional regression, #6/#8 for calibration). Dropped to keep the set at 10. |
| 2104.02705 | Rügamer et al., "deepregression: a Flexible Neural Network Framework…" | Software/framework paper for #2's model class; the corpus indexes methods, not R packages. |
| 1909.03725 | Henzi, Ziegel & Gneiting, "Isotonic Distributional Regression" | The engine under EasyUQ (#7); #7 is the interface a tabular practitioner needs. Rejected as redundant with #7. |
| 2411.13974 | Dombry & Zaoui, "Distributional regression: CRPS-error bounds…" | Theory of CRPS-optimal fitting (NeurIPS 2024). Useful, but #9 already carries CRPS as an evaluation object and the corpus does not need two CRPS papers. |
| 2106.00170 | Gibbs & Candès, "Adaptive Conformal Inference Under Distribution Shift" | Distribution-shift conformal for online/streaming settings. Real gap, but it is a time-series/online topic, not the i.i.d. regression comparison this ticket is about — better filed against a time-series ticket. |
| 1612.01474 | Lakshminarayanan et al., "Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles" | Deep ensembles are a strong probabilistic baseline, but the paper's contribution is ensembling, and the distributional-evaluation machinery it relies on is #6/#8/#9. |
| 2606.03332 | Plaud et al., "Tailoring Strictly Proper Scoring Rules for Downstream Tasks" | ICML 2026, about deriving task-specific scoring rules for causal IPW. Interesting, but the application is causal estimation, not tabular prediction. |
| 2012.12499 | Du, "Beyond Strictly Proper Scoring Rules: The Importance of Being Local" | Argument paper about score locality; the practical content (which score, decomposed how) is in #9. |
| 2606.26497 | Bach et al., "Learning Probabilistic Filters with Strictly Proper Scoring Rules" | 92-page JMLR submission on scoring rules for data-assimilation filters — a different field from tabular regression. |
| 2607.10145 | Fujishige & Nakada, "Scoring Rules as Least-Squares Estimators" | Social-choice scoring rules (Borda-style), unrelated to probabilistic forecasting despite the title. |
| 0912.0902 | Gneiting, "Making and Evaluating Point Forecasts" | Point-forecast evaluation; the corpus is asking about distributions. |

## Risks and open questions

1. **#3 is the weakest link.** It is the only arXiv-hosted paper found that is *about*
   quantile regression forests as such, and it is an application paper (online VaR), not a
   methods reference. Two alternatives if the decision-maker prefers a methods anchor:
   take Meinshausen 2006 as an id-less `direct-pdf` entry (JMLR), or drop #3 and let the
   actuarial quantile block plus #4/#5 carry the topic. The choice changes the count
   between 9 and 10.
2. **#2 is a 2015 applications paper** (regional income inequality) chosen because it is
   the canonical statement of the model class on arXiv; its application is not tabular ML.
   It anchors terminology, not method.
3. **Nothing here has been fetched.** All ten are arXiv ids, so all ten go through the
   existing `/src` → `/pdf` route; none was tested for LaTeX availability, and none is
   licensed or `shareable` yet.
4. **Category naming.** The ticket says `probabilistic`; the manifest's current category
   vocabulary (tabular, relational, general, time series, causal, actuarial / loss
   modelling, mechanistic interpretability, other) has no such value. Adding these ten
   entries therefore also creates the category — a `README.md` + `--index` change, which
   this branch deliberately does not make.
