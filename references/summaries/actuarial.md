# Actuarial / loss modelling — grounding the "why"

Added to the index 2026-10-08. **28 papers, arXiv-only, all fetched.** See `../README.md`
under *actuarial / loss modelling* for the full list with citations.

## Why this category exists

The original fm4sd index is **ML-methods only and silent on actuarial modelling.** A sweep
across all 225 papers for `Tweedie|compound Poisson|loss ratio|actuarial|claim frequency`
returned **two incidental hits**. That is the wrong shape of silence for a project whose
question is *"why do tabular foundation models fail on severity/frequency?"* — the ML
literature will not discuss loss distributions, tail estimation, or count models, because it
does not study them.

Audit D2 had already recorded this void. These papers exist to fill it.

**Scope limit, stated plainly:** arXiv-only. A large share of actuarial work lives in
paywalled venues (*Insurance: Mathematics and Economics*, *ASTIN Bulletin*) that this fetcher
cannot reach — and `fm4sd_fetch.py` skips anything without an arXiv ID, which is also why 49
pre-existing index entries (`pmlr`, `doi`, `springer`) were never fetched. Classic references
may be absent entirely.

---

## The four extracts that bear on W1

### 1. Tail quantiles *are* estimable — if you fit the right family and have enough data

**`one-family-six-distributions`** (1805.10854, Bølviken & Haff) — a 6-parameter claim-severity
class with log-normal, log-Gamma, Weibull, Gamma and Pareto as special cases.

> "as long as the amount of data is reasonable, the five- and six-parameter versions of our
> model provide very good estimates of both the **quantiles of the claim severity distribution
> and the reserves**, for claim size distributions ranging from medium to very heavy tailed.
> However, **when the sample size is small, our model appears to struggle with heavy-tailed
> data**"

Evaluated on Norwegian motor claims. Two things follow:

- **The tail is not universally unrecoverable.** A properly specified parametric family
  estimates tail quantiles well. That is not obviously in conflict with F30 (which is
  *conditional on covariates*, per-row), but it is in tension with any reading of the p99
  result as "the tail cannot be estimated at all."
- **It draws the line at sample size.** Our conditional population is **5,950 claimants** —
  not large for fitting a heavy tail. Whether that is "small" in this paper's sense is
  untested here.

### 2. F18 tested a *linear* Tweedie. The literature's version is nonlinear.

**`tweedie-gradient-boosting-for-extremely-unbalanced-zero-infl`** (1811.10192) — EMTboost.

> "even traditional Tweedie model may not be satisfactory … We propose a boosting-assisted
> zero-inflated Tweedie model … We make a **nonparametric assumption** on its Tweedie model
> component, that **unlike a linear model, is able to capture nonlinearities, discontinuities,
> and complex higher order interactions** among predictors."

F18's verdict — *"the distribution family is not the lever"* — rests on a **GLM**, and
CONCLUSIONS records it as **"best GLM 0.186"**. A boosted, nonparametric, zero-inflated Tweedie
is a different object, evaluated on synthetic zero-inflated auto-insurance claims.

**So F18's conclusion is established for the linear family only.** That is a narrower claim
than the wording implies, and it is the cheapest untested variant in the repo: a Tweedie
*objective inside a GBDT* rather than a linear fit.

### 3. Direct domain match — boosted zero-inflated claims, and CatBoost wins

**`enhanced-gradient-boosting-for-zero-inflated-insurance-claim`** (2307.07771) — property &
casualty insurance, right-skewed positive claims with excess zeros.

> "it is determined that **CatBoost is the best** for developing auto claim frequency models
> based on predictive performance. Furthermore, we propose a new **zero-inflated Poisson
> boosted tree model**, with variation in the assumption about the relationship between
> inflation probability $p$ and distribution mean $\mu$"

Their identified gap is directly relevant to our two-step construction:

> "The common approach for zero-inflated models usually requires **separate training** of the
> models for the inflation probability $p$ and the distribution mean $\mu$. This division
> presents difficulties for those who want to perform a detailed feature risk analysis"

They build two variants: $p$ as a function of $\mu$, and $p$ uncorrelated with $\mu$. **We never
tested which coupling is right** — our F31 two-step assumes independence between indicator and
magnitude, and F30 measured `corr(count, severity) = +0.348` among claimants. Those are in
tension, and this paper names the choice.

Also: an independent finding that **CatBoost** is the right frequency model, which bears on
Audit 3 — our baseline is depth-3/`n_estimators=4` and the actuarial ML literature picks
CatBoost.

### 4. The two-part family: hurdle is the flexible member

**`comparing-tobit-and-two-part-hurdle-models-for-semi-continuo`** (2608.09725).

> "we derive rigorous mathematical conditions under which the two models are equivalent and
> show that the **Tobit can be viewed as a special case of the hurdle model** when the link
> function for the binary process is probit. … we found that **the hurdle is more flexible and
> robust** than the Tobit model"

Note the *equivalence* result: testing Tobit against a probit-hurdle would be testing a
special case, so it is not a new arm worth running.

Also worth flagging — in their application:

> "Estimates obtained from the Tobit and hurdle models were **broadly consistent with those
> from a standard linear model that ignored zero inflation**"

Same shape as F32 (the model absorbs zero-inflation without being taught it), though in
biomedical longitudinal data, **not** insurance claims. Different domain — use as corroboration
of a pattern, not as evidence about ours.

---

## What this changes

| Claim | Status after these papers |
|---|---|
| "The tail cannot be recovered" | **Narrowed.** A parametric family estimates tail quantiles well on sufficient data; our 5,950-claimant population may not be sufficient. Untested either way. |
| "The distribution family is not the lever" (F18) | **Narrowed to linear GLMs.** A boosted zero-inflated Tweedie (EMTboost) exists and was never run. |
| "Two-step (independent indicator + magnitude) is the right form" | **Contested.** The literature explicitly varies $p$'s coupling to $\mu$; F30 measures `corr = +0.348`, which argues *against* independence. |
| CatBoost is the reference frequency model | Independent support for an external answer to Audit 3's baseline question. |

## What it does *not* establish

None of these papers study a **tabular foundation model**, and none reports a p99 tail ratio
of the kind this repo measures. Audit 2's finding stands: the TFM literature does not publish
tail-accuracy numbers, and the actuarial literature does not evaluate TFMs. **The seam W1
targets sits in the gap between them.**

## Caveats

- arXiv-only; paywalled venue work unreachable (see scope limit above).
- Several are domain-mismatched: EMTboost's simulations are synthetic, the Tobit/hurdle paper
  is biomedical, `one-family-six-distributions` is Norwegian motor reserving. Treat as
  methodological reference, not as measurements on our data.
- Fetched with the same licence handling as the rest of the corpus; arXiv API reports
  `api-omitted` for all of them, so no payload is redistributable.