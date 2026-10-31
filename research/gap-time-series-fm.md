# Which time-series foundation models are missing?

Research for ticket #46 (child of #41). Branch `research/gap-time-series-fm`; this file is
the only thing on it. Read-only: no change to `README.md`, `references/manifest.json` or
`scripts/`.

## Answer

Ten papers fill the gap. Nine are **competing forecasters**; one is a **survey** that earns
its place because it defines the taxonomy and evaluation protocol the nine are scored under.
All ten go under the existing `time series` category, sub-heading `forecasting` — no new
category or sub-category is needed.

The shape of the finding: the index's `forecasting` block is **2025–2026-heavy** —
`chronos-2`, `toto-2`, `tirex`/`tirex-2`, `panda`, `tempopfn`, `ts-icl`, `timersi` — and
has almost no **2023–2024 ancestry**. `chronos` is the only pre-2025 foundation-model paper
in it. The models every 2026 paper benchmarks against (Moirai, Lag-Llama, TimeGPT, TimesFM,
Toto, MOMENT) are absent, so the block cannot answer "what did `tirex-2` beat?".

Two of the ten are **family gaps rather than new families**: the index has `timesfm-3` (a
blog link, no paper) but not the TimesFM paper, and `toto-2` but not Toto. Those are
included because a family anchored only at its newest release has no citable method.

## Method note

- **De-duplication.** Grepped `README.md` and `references/manifest.json`
  case-insensitively for `chronos|timesfm|moirai|lag-llama|lagllama|timegpt|sundial|time-moe|moment|toto|timer|survey`.
  Hits: `chronos`, `chronos-2`, `tabpfn-ts`, `toto-2`, `timesfm-3`, `tirex`, `tirex-2`,
  `panda`, `tempopfn`, `tiny-tsm`, `ts-icl`, `timersi`, `gift-eval`, `fev-bench`,
  `impermanent`, `patch-tst` — i.e. exactly the rows named above. Zero hits for `moirai`,
  `lag-llama`, `timegpt`, `sundial`, `time-moe`, `moment` as a model name (`moment` appears
  only inside the actuarial slug `…payment-type-moments-for-ro`, unrelated). None of the
  ten candidates appears in the `## queue` time-series block either.
- **Verification.** Every id was resolved on arXiv. Seven were verified in one
  `export.arxiv.org/api/query?id_list=…` batch (2402.02592, 2410.10469, 2310.08278,
  2310.03589, 2310.10688, 2407.07874, 2402.03885), returning matching titles and dates.
  The export API then answered every subsequent `id_list` call with HTTP 429 for the rest
  of the session; the remaining ids were verified against their `arxiv.org/abs/<id>` pages
  instead, reading `citation_title` and `citation_date` from the page metadata (all 200,
  all matching). Re-running the batch through the API is the one check left for a session
  with a clean rate-limit budget.
- **GitHub links** were checked with a direct request: all eight return 200.
- **"Strongest remaining zero-shot"** is read off the baseline sets of the post-2025
  evaluations already in the corpus (`gift-eval`, `chronos-2`, `tirex`, `tirex-2`), not off
  a fresh leaderboard run. A model is included if it is (a) a recurring zero-shot baseline
  in that literature and (b) either open-weight or the commercial reference everyone
  compares to.
- **No new benchmark is proposed.** `gift-eval` (2410.10393), `fev-bench` (2509.26468) and
  `impermanent` (2603.08707) already cover zero-shot evaluation, harness and leakage. A
  fourth benchmark would be redundant, so the tenth slot goes to the survey instead.

## The list

| # | arXiv | title | kind | why it is load-bearing |
|---|---|---|---|---|
| 1 | [2402.02592](https://arxiv.org/abs/2402.02592) | *Unified Training of Universal Time Series Forecasting Transformers* (Moirai, 2024) | competing model | The canonical any-frequency, any-variate, distributional-output forecaster; the reference implementation (`uni2ts`) that defines the "universal" evaluation protocol. |
| 2 | [2511.11698](https://arxiv.org/abs/2511.11698) | *Moirai 2.0: When Less Is More for Time Series Forecasting* (2025) | competing model | The current Salesforce flagship: a small decoder-only model that beats much larger 2025 baselines zero-shot — the scaling-counterpoint to Time-MoE (entry 9). |
| 3 | [2310.08278](https://arxiv.org/abs/2310.08278) | *Lag-Llama: Towards Foundation Models for Probabilistic Time Series Forecasting* (2023) | competing model | The first open probabilistic time-series foundation model; lag-feature tokenisation and the Llama backbone are the design most later work contrasts itself with. |
| 4 | [2310.03589](https://arxiv.org/abs/2310.03589) | *TimeGPT-1* (2023) | competing model | The commercial API forecaster that every zero-shot table includes as a baseline; without it the index cannot explain the numbers it cites. Closed weights — citation-only. |
| 5 | [2310.10688](https://arxiv.org/abs/2310.10688) | *A decoder-only foundation model for time-series forecasting* (TimesFM, 2023) | competing model | The TimesFM paper itself. The index holds only the `timesfm-3` blog link, so the family's method paper is missing; this is the one that defines the decoder-only, patched-input recipe. |
| 6 | [2407.07874](https://arxiv.org/abs/2407.07874) | *Toto: Time Series Optimized Transformer for Observability* (2024) | competing model | Datadog's observability forecaster and the GIFT-Eval-era baseline; `toto-2` is indexed but the original is not, so the scaling story the sequel tells has no baseline in the corpus. |
| 7 | [2402.03885](https://arxiv.org/abs/2402.03885) | *MOMENT: A Family of Open Time-series Foundation Models* (2024) | competing model | The open T5-encoder family with a published benchmark suite; the standard non-forecasting (classification/anomaly/imputation) counterpart to the decoder-only forecasters, and the natural companion to the existing `classification` block. |
| 8 | [2502.00816](https://arxiv.org/abs/2502.00816) | *Sundial: A Family of Highly Capable Time Series Foundation Models* (2025) | competing model | A 2025 zero-shot leader on GIFT-Eval-style suites built on a flow-matching ("TimeFlow") head; the strongest remaining open model not already indexed. |
| 9 | [2409.16040](https://arxiv.org/abs/2409.16040) | *Time-MoE: Billion-Scale Time Series Foundation Models with Mixture of Experts* (2024) | competing model | The scaling-law result for this literature (up to 2.4B parameters, 300B points) — the positive control against Moirai 2.0's "less is more" claim. |
| 10 | [2403.14735](https://arxiv.org/abs/2403.14735) | *Foundation Models for Time Series Analysis: A Tutorial and Survey* (2024) | survey / evaluation resource | The KDD tutorial that fixes the task taxonomy (forecasting, imputation, classification, anomaly) and the zero-shot evaluation protocol the nine above are compared under. Included because the placement decision in this file relies on it; no other time-series survey is in the index. |

## Placement

All ten under `- time series` → `- forecasting`. The sub-category name already exists and
is truncation-stable in `parse_index()`, so no parser change is needed. There is a
defensible alternative for entry 7: MOMENT spans classification and imputation as much as
forecasting, so it could sit under `classification` instead. `forecasting` is preferred
because that is where its baselines (`chronos`, `toto-2`) live and because this ticket is
about forecasters; moving it is presentation, not a finding.

## Considered and not included

- **Moirai-MoE** ([2410.10469](https://arxiv.org/abs/2410.10469)) — the sparse-MoE
  intermediate step in the Moirai line, superseded by Moirai 2.0 (entry 2). Adding both
  would spend two slots on one family's lineage.
- **Timer** ([2402.02368](https://arxiv.org/abs/2402.02368)) and **Timer-XL**
  ([2410.04803](https://arxiv.org/abs/2410.04803)) — long-context unified forecasters, but
  neither is a recurring zero-shot baseline in the 2026 tables; Time-MoE covers the
  scaling argument they would make. (The index already has `timer-m1`, 2026, in the queue.)
- **TimesFM 2.5 / TimesFM 3 papers** — no arXiv paper found for 2.5 in an arXiv title
  search; TimesFM-3 is blog-only and already indexed. Entry 5 is the citable method paper.
- **Chronos-Bolt** — an inference-speed variant inside the Chronos family;
  `chronos`/`chronos-2` already cover it.
- **A second benchmark** (e.g. another GIFT-Eval-style harness) — `gift-eval`,
  `fev-bench` and `impermanent` already cover evaluation, harness and leakage.
- **The two "tfm-survey" extras** (`tfm-survey.com`, `tfm-systematic-survey` on SSRN) —
  both are *tabular* foundation-model surveys, not time-series. Confirmed by reading their
  index rows, so they do not de-duplicate entry 10.
- **Financial/observability niche forecasters** (`kronos`, `fincast`, `t0`, all in the
  queue) — domain models, not the general zero-shot comparators this ticket asks for.

## Risks

- **Entry 4 (TimeGPT) is closed.** The GitHub link is Nixtla's client SDK, not the model.
  The paper is citable and its numbers are quotable, but nothing can be re-run from the
  corpus; it is the one entry here that can never have a payload beyond the PDF.
- **Entry 10 is a 2024 KDD tutorial.** It is the right taxonomy anchor but it predates
  Chronos-2, TiRex and Toto-2; a 2026 survey would supersede it. I did not verify that no
  such survey exists — I only confirmed none is in the index.
- **Rate-limit caveat** in the verification note: three ids (2502.00816, 2409.16040,
  2403.14735) and Moirai 2.0 (2511.11698) were confirmed from abs-page metadata rather
  than the API batch. Same source of truth, different endpoint.
- **"Strongest" is a 2026 snapshot.** Entry 8 (Sundial, Feb 2025) and entry 2 (Moirai 2.0,
  Nov 2025) are the most likely to be overtaken; the 2023–2024 entries are included for
  lineage and will not date.

## Integration notes (deliberately not actioned here)

- **Counts move in the same commit.** Adding ten rows changes the entries-parsed figure in
  `README.md`, `references/README.md` and `PROVENANCE.md`; `check_reproducibility.py`
  check 3 derives those figures from the manifest, so README + manifest + prose must change
  together or the gate goes red.
- **Fetch routes are ordinary.** All ten carry arXiv ids, so they take the existing
  `/src/<id>` → `/pdf/<id>` path; no new route family is needed. Nine are LaTeX-source
  papers; TimeGPT-1 is old enough that it will fetch as PDF only if arXiv has no source
  tarball, which the existing fallback already handles.
- **No new sub-category vocabulary**, so nothing to add to `GLOSSARY.md`.
