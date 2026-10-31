# Which benchmark methodology papers are missing?

Research for ticket #45 (child of #41, blocks #47). Branch `research/gap-benchmark`;
this file is the only thing on it. Read-only: no change to `README.md`,
`references/manifest.json` or `scripts/`.

## Answer

Nine papers, all category **`benchmark methodology`**. They cover the layer the index
currently lacks: how tabular models are *compared*, as opposed to individual benchmarks
and individual results.

| theme from the ticket | closed by |
|---|---|
| benchmark infrastructure | TabRepo, AMLB |
| benchmark protocols | AMLB, OpenML Benchmarking Suites |
| dataset / suite curation | PMLB, OpenML Benchmarking Suites |
| leaderboard critique | The Benchmark Lottery |
| evaluation pitfall: leakage | Leakage and the Reproducibility Crisis in ML-based Science |
| evaluation pitfall: tuning parity | Show Your Work, AMLB |
| evaluation pitfall: statistical comparison | LMEMs for post-hoc analysis of HPO Benchmarking |
| OpenML-style reproducibility | OpenML Benchmarking Suites, Improving Reproducibility in ML Research |

The shape of the finding: the index has **383 entries and many benchmarks, but no methodology
of benchmarking**. Of the 383, 15 are benchmarks or benchmark-adjacent evaluations
(`tabarena`, `tabattnbench`, `tabbench-bio`, `multabench`, `strable`, `scoringbench`,
`retabad`, `seq2synth`, `gift-eval`, `fev-bench`, `impermanent`, `relarena-alpha`,
`enterprisetabgap`, `oodtabfm`, `tabprep`). Every one of them *is* a benchmark or an
evaluation result. None says how to run, report or compare one. Searching the manifest's
titles and categories for the vocabulary of the layer finds almost nothing: `protocol` 0 hits,
`leaderboard` 0, `OpenML` 0, `significance` 0, `mixed-effect` 0, `reproduc*` 1
(`relarena-alpha`, a relational benchmark), `leak*` 1 (`supportsetleakage`, the defect not the
method), `tuning` 2 (`finetuningtfm`, `localpfn` — both about tuning a model, not about tuning
parity).

That absence matters for the actuarial comparison this fork exists for. The 28-entry
actuarial block compares Tweedie boosting, zero-inflated models and frequency/severity
specifications on a handful of company datasets. Without a protocol paper and a statistical
comparison paper, "CatBoost is the reference frequency model" (digest `actuarial.md:120`) is
a ranking with no stated decision rule behind it.

## The list

Titles are as the arXiv abs page returns them on 2026-10-31, with the current revision.

| # | arXiv id | title | why it is load-bearing here | version to pin |
|---|---|---|---|---|
| 1 | [2311.02971](https://arxiv.org/abs/2311.02971) | *TabRepo: A Large Scale Repository of Tabular Model Evaluations and its AutoML Applications* | Precomputed predictions and metrics for 1,310 models on 200 datasets: lets the corpus re-rank and re-ensemble without re-running anything, and is the evaluation store TabArena (already indexed) is built on. | `@v3` |
| 2 | [2207.12560](https://arxiv.org/abs/2207.12560) | *AMLB: an AutoML Benchmark* | The worked protocol for comparing whole pipelines — fixed folds, a shared time budget, framework-failure accounting, Bradley–Terry analysis of which task subsets change the ranking; the checks a severity/frequency comparison has to pass. | `@v2` |
| 3 | [1708.03731](https://arxiv.org/abs/1708.03731) | *OpenML Benchmarking Suites* | Defines the reproducible unit — task + flow + shared suite (OpenML-CC18) with standardized formats and meta-data — so a tabular benchmark can be re-run by someone else; the OpenML-style reproducibility reference. | `@v3` |
| 4 | [1703.00512](https://arxiv.org/abs/1703.00512) | *PMLB: A Large Benchmark Suite for Machine Learning Evaluation and Comparison* | The argument for a curated, meta-feature-characterized suite over an ad-hoc dataset grab, plus how algorithms cluster by performance across it — the dataset-selection half of benchmark methodology. | `@v1` |
| 5 | [2107.07002](https://arxiv.org/abs/2107.07002) | *The Benchmark Lottery* | Shows relative rankings flip when the task set changes, so any "FM beats GBDT" claim is a claim about a particular lottery; the leaderboard critique the corpus cannot currently make. | `@v1` |
| 6 | [2207.07048](https://arxiv.org/abs/2207.07048) | *Leakage and the Reproducibility Crisis in ML-based Science* | An 8-type leakage taxonomy drawn from 329 papers in 17 fields — generalizes the index's single relational-FM leakage entry into a checklist for splits, feature construction and target encoding on insurance data. | `@v1` |
| 7 | [1909.03004](https://arxiv.org/abs/1909.03004) | *Show Your Work: Improved Reporting of Experimental Results* | Expected validation performance as a function of tuning budget: turns "both models were tuned equally" into an auditable curve rather than an assertion — the tuning-parity pitfall. | `@v1` |
| 8 | [2408.02533](https://arxiv.org/abs/2408.02533) | *LMEMs for post-hoc analysis of HPO Benchmarking* | Linear mixed-effects significance testing over benchmark runs, including dataset meta-features: replaces "mean rank across datasets" with a model that can say whether a gap is real — the statistical-comparison pitfall. | `@v1` |
| 9 | [2003.12206](https://arxiv.org/abs/2003.12206) | *Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program)* | The reproducibility programme and ML Reproducibility Checklist (code, data, seeds, compute) that a benchmark has to satisfy before its numbers count; the reporting standard behind the tooling in #3. | `@v4` |

## Why these, theme by theme

**Infrastructure (1, 2).** TabRepo and AMLB are the two ends of the same idea: TabRepo
publishes *results* so analysis is cheap and reproducible without compute; AMLB publishes a
*harness* so the runs themselves are comparable. TabArena, already in the index, is the
living leaderboard built on TabRepo's store — so TabRepo is the citable object underneath a
paper the corpus already carries.

**Protocol and dataset curation (2, 3, 4).** AMLB states the protocol rules (same folds,
stated budgets, count failures, test subsets for rank stability). OpenML Benchmarking Suites
makes the suite a shareable artefact. PMLB supplies the curation argument and evidence that
dataset choice, not method quality, drives much of the spread. Together they answer "on
what, with which splits, tuned how, reported where".

**Leaderboard critique (5).** The Benchmark Lottery is the general statement of the problem
the tabular literature keeps rediscovering: rank order is a property of the task set. It is
the paper to cite when the corpus wants to say a leaderboard position is not a finding.

**Leakage (6).** The index's `supportsetleakage` (2609.36417) is a specific defect in
in-context relational models. Kapoor & Narayanan is the general taxonomy — the paper that
makes leakage a *category* with named types rather than an incident.

**Tuning parity (2, 7).** Show Your Work is not tabular, but it is the canonical statement of
the pitfall the tabular comparison literature keeps failing: a test score without a tuning-
budget curve is not a comparison. AMLB applies the same discipline to AutoML frameworks.

**Statistical comparison (8).** `tabbarrier` (2606.29091, indexed) argues tabular foundation
models are often statistically indistinguishable; LMEMs is the method that could establish
it. The pair is the reason this entry is worth a slot.

**Reproducibility (3, 9).** One paper for the mechanism (OpenML suites), one for the
reporting standard (NeurIPS checklist). The repo's own gate is a build-time analogue; the
corpus should be able to cite where the norm comes from.

## Considered and not included

| arXiv id | title | why not |
|---|---|---|
| [2506.16791](https://arxiv.org/abs/2506.16791) | *TabArena: A Living Benchmark for Machine Learning on Tabular Data* | **Already indexed** — slug `tabarena`, category `tabular`. Checked as the ticket asked. Its evaluation store is TabRepo (#1), which is not indexed. |
| [2305.02997](https://arxiv.org/abs/2305.02997) | *When Do Neural Nets Outperform Boosted Trees on Tabular Data?* (TabZilla) | Belongs to #42: proposed there as the dataset-property evidence in the tree-vs-DL question, not as methodology. Not repeated. |
| [2207.08815](https://arxiv.org/abs/2207.08815) | *Why do tree-based models still outperform deep learning on typical tabular data?* | #42 (Grinsztajn). Cited there, not here. |
| [2106.11959](https://arxiv.org/abs/2106.11959) | *Revisiting Deep Learning Models for Tabular Data* | #42 (Gorishniy). It fixes a comparison protocol, but its role in this corpus is the baseline evidence, so it stays on the baselines ticket. |
| [2106.11189](https://arxiv.org/abs/2106.11189) | *Well-tuned Simple Nets Excel on Tabular Datasets* | #42 (Kadra). Reads as tuning parity, but #42 already claims it as baseline evidence; proposing it twice would double-count. |
| [2106.03253](https://arxiv.org/abs/2106.03253) | *Tabular Data: Deep Learning is Not All You Need* | #42 (Shwartz-Ziv & Armon). |
| [1407.7722](https://arxiv.org/abs/1407.7722) | *OpenML: networked science in machine learning* | The platform paper; #3 carries the benchmarking-protocol argument and is the one a comparison would cite. Redundant at this depth. |
| [2312.07577](https://arxiv.org/abs/2312.07577) | *Benchmarking Distribution Shift in Tabular Data with TableShift* | A benchmark (distribution shift), not methodology; the index already evaluates OOD tabular performance in `oodtabfm` (2607.26000). |
| [1905.04970](https://arxiv.org/abs/1905.04970) | *Tabular Benchmarks for Joint Architecture and Hyperparameter Optimization* | A surrogate benchmark *for HPO* (tabular by construction), not methodology for comparing tabular predictors. Easy to confuse with #1; it is a different object. |
| [1910.11758](https://arxiv.org/abs/1910.11758) | *Optimizer Benchmarking Needs to Account for Hyperparameter Tuning* | Tuning parity again, but for optimizers rather than predictors, and its title differs across versions (Semantic Scholar still lists the v1 title *On the Tunability of Optimizers in Deep Learning*). Weak fit and a citation hazard. |
| [1909.06674](https://arxiv.org/abs/1909.06674) | *A Step Toward Quantifying Independently Reproducible Machine Learning Research* | Single-author study of reproduction rates; #9 carries the standard-setting role more directly. |
| [2509.08986](https://arxiv.org/abs/2509.08986) | *Time-Fair Benchmarking for Metaheuristics: A Restart-Fair Protocol for Fixed-Time Comparisons* | Fair-budget protocol, but for metaheuristics rather than ML on tables. |

**Deferred, no arXiv id.** Demšar 2006, *Statistical Comparisons of Classifiers over Multiple
Data Sets* (JMLR 7:1–30) is the canonical significance-testing reference and would be the
obvious companion to #8. It has no arXiv id, so the #41 rule (every entry needs a resolvable
arXiv id) excludes it. Worth recording as a known hole rather than silently dropping: if the
scope line ever admits non-arXiv entries for methodology, this is the first one to add.

## Verification and method

**De-duplication.** Read `references/manifest.json` (383 entries) as JSON and tested each
candidate id for set membership: none of the nine proposed ids appear; of the twelve rejects
only `2506.16791` (TabArena) is present, which is why it is a reject. Grepped `README.md` and
the manifest
case-insensitively for `tabrepo`, `pmlb`, `amlb`, `openml`, `benchmark lottery`, `lmem`,
`mixed-effect`, `show your work`: one hit, `supportsetleakage`, which is the leakage entry
discussed above.

**Identity.** Each id was fetched from its arXiv abs page on 2026-10-31 and the returned
title, author list and dateline revision recorded; the table quotes those titles verbatim and
the `@vN` column is the "this version" of that dateline. This is arXiv's own record, not a
secondary index.

**arXiv API.** The `export.arxiv.org/api/query?id_list=…` endpoint returned HTTP 429 with an
empty body for every live query from this host throughout the session (edge-cached queries
such as `all:electron` still returned 200, which is what rules out a network fault). Three
other research tickets (#42, #43, #46) were querying the same endpoint from the same IP at
the same time, which is the likely cause. Consequence: id and title were confirmed from
`arxiv.org/abs/<id>` rather than the API feed. Before #47 adds these entries, re-run
`id_list` and check the returned `<title>`/`<published>` against the table — treat that as an
open verification item, not a completed one.

**What I did not run.** No fetch, index or gate command: the worktree has no payload, and
`scripts/` was not touched. The nine ids are proposals, not additions.
