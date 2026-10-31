# Which non-life actuarial methods papers extend the block?

Research for ticket #44 (child of #41, blocks #47). Branch
`research/gap-actuarial-methods`; this file is the only thing on it. Read-only: no
change to `README.md`, `references/manifest.json` or `scripts/`.

## Answer

Nine papers fill the gap. Four go under `tail metrics, quantiles, reserving`, four under
`frequency and count models`, one under `severity`. Eight of the nine are **not on
arXiv** — for this literature that is structural, not a search failure (see "arXiv
availability" below).

The shape of the finding: the block's existing 28 entries are almost all *modern
regression work on loss distributions* (Poudyal, Bladt, Aradhye/Fung on severity; Tweedie
boosting and zero-inflation variants on counts). What is missing is the **canonical
non-life methodology that the ML work is a re-derivation of** — chain-ladder and its
stochastic error, GLM reserving, the compound-Poisson/Tweedie pure-premium GLM, and the
zero-inflated/hurdle origins. Those are the entries below.

## Method note

- **De-duplication.** Parsed the block (`README.md` lines 202–243: 28 entries, three
  sub-headings) and grepped case-insensitively for every candidate's author and title
  token against both `README.md` and `references/manifest.json`: zero hits for `mack`,
  `bornhuetter`, `ferguson`, `england`, `verrall`, `jørgensen`, `lambert`, `mullahy`,
  `frees`, `blier`. `tweedie` does hit (6 README lines, 13 manifest lines), but every hit
  is an ML-Tweedie *application* (1508.06378, 1811.10192, 0904.1483, 1912.12356,
  2311.03222) — the canonical Tweedie GLM is absent, so Jørgensen is an addition, not a
  duplicate.
- **Verification.** Each DOI was resolved through `doi.org` and the redirect target
  checked: 200/301/302 at the publisher. Two publishers (Taylor & Francis, MDPI) return
  403 to a non-browser client — bot-blocking, the DOI itself resolves. arXiv metadata was
  read off the abs page; the Bornhuetter–Ferguson PDF was downloaded and its embedded
  `/Title` and `/Author` metadata read back to confirm it is the 1972 paper and not the
  proceedings volume.
- **arXiv availability.** Probed arXiv title *and* author search for every non-arXiv
  candidate (`Blier-Wong` returns 18 records, none of them the 2021 review; the Wüthrich
  & Merz book title returns zero). Pre-arXiv publication (Mack 1993, BF 1972, Lambert
  1992, Mullahy 1986, Jørgensen 1994), or journal-only with no preprint (England &
  Verrall 2002, Frees/Shi/Valdez 2009, Blier-Wong et al. 2021). The block's arXiv-first
  preference cannot be honoured here without substituting weaker papers for the canonical
  ones.

## The list

| # | placement | link | title | why it is load-bearing |
|---|---|---|---|---|
| 1 | tail metrics, quantiles, reserving | [doi](https://doi.org/10.2143/AST.23.2.2005092) | Mack — *Distribution-free Calculation of the Standard Error of Chain Ladder Reserve Estimates* (ASTIN Bulletin 23(2):213–225, 1993) | The distribution-free chain-ladder MSEP; every reserving comparison, ML or not, is scored against this variance. |
| 2 | tail metrics, quantiles, reserving | [pdf](https://www.casact.org/sites/default/files/database/proceed_proceed72_72181.pdf) | Bornhuetter & Ferguson — *The Actuary and IBNR* (PCAS LIX:181–195, 1972) | The prior-plus-data reserve estimator: the original "blend an external prior with thin data" move, which is structurally what a tabular foundation model claims to do. |
| 3 | tail metrics, quantiles, reserving | [doi](https://doi.org/10.1017/S1357321700003809) | England & Verrall — *Stochastic Claims Reserving in General Insurance* (British Actuarial Journal 8(3):443–518, 2002) | Turns reserving into a GLM (over-dispersed Poisson) with bootstrap prediction error — the regression framing the block otherwise lacks entirely. |
| 4 | tail metrics, quantiles, reserving | [doi](https://doi.org/10.3390/risks9010004) | Blier-Wong, Cossette, Lamontagne & Marceau — *Machine Learning in P&C Insurance: A Review for Pricing and Reserving* (Risks 9(1):4, 2021) | The standard actuarial-side survey of ML in non-life, split pricing/reserving; the map of where neural methods sit against GLMs. Review 1 of 2. |
| 5 | frequency and count models | [doi](https://doi.org/10.2143/AST.39.1.2038061) | Frees, Shi & Valdez — *Actuarial Applications of a Hierarchical Insurance Claims Model* (ASTIN Bulletin 39(1):165–197, 2009) | Joint frequency–severity with policyholder random effects; the canonical statement that the two components must be modelled together, not separately. |
| 6 | frequency and count models | [doi](https://doi.org/10.1080/03461238.1994.10413930) | Jørgensen & de Souza — *Fitting Tweedie's Compound Poisson Model to Insurance Claims Data* (Scandinavian Actuarial Journal 1994(1):69–93) | The canonical Tweedie GLM for pure premium. The distributional assumption under *every* Tweedie-boosting paper already in the block, cited but never sourced there. |
| 7 | frequency and count models | [doi](https://doi.org/10.2307/1269547) | Lambert — *Zero-Inflated Poisson Regression, with an Application to Defects in Manufacturing* (Technometrics 34(1):1–14, 1992) | Origin of zero-inflated regression; the three ZIP/ZINB insurance entries in the block (2307.07771, 2212.00985, 1701.05452) all descend from it. |
| 8 | frequency and count models | [doi](https://doi.org/10.1016/0304-4076(86)90002-3) | Mullahy — *Specification and Testing of Some Modified Count Data Models* (Journal of Econometrics 33(3):341–365, 1986) | The hurdle model — the two-part structure the block already compares against (2608.09725) but never grounds. The structural alternative to zero-inflation, not a variant of it. |
| 9 | severity | [arxiv](https://arxiv.org/abs/2609.14576) | Blier-Wong — *Towards foundation models for insurance risk modelling* (arXiv:2609.14576 [q-fin.RM], 2026) | The one review written from the actuarial side about foundation models on insurance loss data — this project's own thesis, stated by the field it is aimed at. Review 2 of 2. |

## Placement by sub-heading

### tail metrics, quantiles, reserving — 4

Mack (1) gives the estimator's variance, Bornhuetter–Ferguson (2) the prior-blended
estimator, England–Verrall (3) the regression formulation of both. Read as a set they are
the reserving canon: estimate, blend, quantify error. The block currently holds only the
ML descendants (`deeptriangle`, micro-level reserving) with none of the parents.

The Blier-Wong et al. review (4) goes here rather than under frequency because the
reserving half is the half the block lacks — its pricing half is already represented by
the Tweedie and zero-inflation entries.

### frequency and count models — 4

Frees/Shi/Valdez (5) is the joint model; Jørgensen (6) the pure-premium GLM link and
variance function; Lambert (7) and Mullahy (8) the two competing answers to excess zeros.
Together they cover the modelling decisions the block's boosting papers make silently.

### severity — 1, and a judgement call

Entry 9 is a review that spans all three sub-headings; it is placed under `severity`
because its worked examples are loss-cost (severity and reserving) estimation from
unstructured claim data, and `severity` is where the block anchors loss-cost modelling.
If the parent prefers, it moves to `tail metrics, quantiles, reserving` with no change of
argument — that is a presentation choice, not a finding.

No other `severity` additions are proposed. That sub-heading is the best-covered of the
three (10 entries, all modern loss-distribution regression), and the canonical severity
texts it is missing are books, not papers. The gap is genuinely on the frequency and
reserving side.

## Non-arXiv accounting

| entry | link type | why no arXiv id |
|---|---|---|
| Mack 1993 | DOI (Cambridge/ASTIN) | published 1993, pre-arXiv |
| Bornhuetter–Ferguson 1972 | publisher PDF (CAS proceedings) | 1972, PCAS has no DOI at all |
| England & Verrall 2002 | DOI (Cambridge/BAJ) | journal-only, no preprint |
| Blier-Wong et al. 2021 | DOI (MDPI, open access) | journal-only; arXiv author search finds 18 other records, not this one |
| Frees, Shi & Valdez 2009 | DOI (Cambridge/ASTIN) | journal-only |
| Jørgensen & de Souza 1994 | DOI (Taylor & Francis) | pre-arXiv |
| Lambert 1992 | DOI (JSTOR) | pre-arXiv; the T&F DOI for this article is not registered, JSTOR's is |
| Mullahy 1986 | DOI (Elsevier) | pre-arXiv |

Retrievability: entries 4 and 9 are open access; 1, 3, 5, 6, 7, 8 resolve to a paywall;
2 is a free scan.

## Integration notes (deliberately not actioned here)

- **The parser tolerates DOI-only entries, but the fetcher does not route them.**
  `parse_index()` leaves `arxiv=""` for an entry with no arXiv link and keeps it in the
  manifest so the count stays honest (`scripts/fm4sd_fetch.py:548–551`). `fetch_one()`
  then sends id-less entries to `fetch_route()`, and `route_candidates()` only produces a
  route from a `[pdf]` / `[springer]` / `[nature]` / `[pmlr]` / `[neurips]` link. A bare
  `[doi]` link is therefore **citation-only** — no payload, no licence record, no text for
  `fm4sd_search.py --text`. Giving entry 2 a `[pdf]` link is what makes it fetchable via
  the `direct-pdf` family; the other DOI-only entries need an explicit `[pdf]` if a free
  one exists (4 and 9 are open access). `[doi]` as link text is already precedented in the
  README (the `martingale` queue entry). I ran no `--fetch`, so none of these routes were
  exercised.
- **Counts move in the same commit.** `PROVENANCE.md` states 28 in five places (lines 26,
  31, 46, 89, 134) and `docs/RESEARCH.md` in two (18, 26); the entries-parsed figure
  becomes 383 + N. `check_reproducibility.py` check 3 derives those figures from the
  manifest and compares them against the prose, so README, manifest and prose must change
  together or the gate goes red.
- **Real cost of the DOI route:** entries left with a bare `[doi]` get no payload, so no
  licence record and no searchable text — `fm4sd_search.py --text` will never match them.
  If the block is meant to support corpus sweeps, that is an argument for adding `[pdf]`
  links to the ones that are free (2, 4, 9) and accepting that 1, 3, 5–8 are
  citation-only.
- **Subcategory vocabulary is unchanged.** All three target headings already exist and
  are truncation-stable in `parse_index()` (`severity`, `frequency and count models`,
  `tail metrics, quantiles, reserving`), so no parser change is needed.

## Considered and not included

- **Wüthrich & Merz, *Statistical Foundations of Actuarial Learning and its Applications***
  (Springer Actuarial, 2023, [doi](https://doi.org/10.1007/978-3-031-12409-9), open access;
  SSRN 3822407). The strongest single text on the exact question, but it is a book, and the
  ticket caps reviews at two. It is the natural next addition if a book is acceptable.
- **England & Verrall 1999**, *Analytic and bootstrap estimates of prediction errors in
  claims reserving* ([doi](https://doi.org/10.1016/S0167-6687(99)00016-5)) — subsumed by
  the 2002 paper.
- **Frees & Valdez 2008**, *Hierarchical Insurance Claims Modeling*
  ([doi](https://doi.org/10.1198/016214508000000823)) — the JASA version; the 2009 ASTIN
  paper is the same model stated for actuaries and shorter.
- **Smyth & Jørgensen 2002**, *Fitting Tweedie's Compound Poisson Model … Dispersion
  Modelling* ([doi](https://doi.org/10.2143/AST.32.1.1020)) — a refinement of entry 6, not
  the canonical statement.
- **Klugman, Panjer & Willmot, *Loss Models*** — textbook; `severity` is already
  saturated with modern regression work.

## Risks

- **Link rot on entry 2.** The CAS scan lives under `/sites/default/files/database/`; the
  older `casact.org/pubs/proceed/…` path already 404s, and two other historical CAS paths
  I tried did too. Fallback citation is PCAS LIX:181–195, reproduced in every reserving
  text, so the entry survives a dead link even though the URL does not.
- **Entry 9 is eight weeks old and unrefereed** (arXiv v1, 13 Sep 2026). Load-bearing for
  framing, not for results.
- **Paywalls** on five of the nine mean the corpus can cite but not read them; that is
  acceptable for a reading index but should be recorded rather than discovered later.
