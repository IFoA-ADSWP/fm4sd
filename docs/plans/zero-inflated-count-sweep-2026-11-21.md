# Plan — sweep for remedies to the count / zero-inflated gap (2026-11-21)

The sibling repo `tabular-foundation-model` loses on frequency, severity and zero-inflated
amount targets and wins on classification and lapse. This sweep asks what the literature holds
that could change that verdict, and captures it here.

## What

Six entries in `README.md`, one digest, and one sweep section in
`references/summaries/SWEEPS.md`:

| slug | id | placed in | why |
|---|---|---|---|
| `tabpfn-insurance-pricing` | 2605.22892 | actuarial → frequency and count models | the independent replication on `freMTPL2` / `beMTPL97`; names exposure, weights and distribution-specific losses as the gap |
| `zip-telematics-near-miss` | 2509.02614 | actuarial → frequency and count models | exposure-offset ZIP for sparse weekly counts; "traditional statistical models underfit" |
| `two-fold-zero-inflated` | 2310.08088 | probabilistic | the decomposition hypothesis as a measured method on zero-inflated targets |
| `pfn-boost` | 2502.02672 | tabular | the only published TFM+GBDT fusion; beats both components on intermediate sizes |
| `tfm-vs-tuned-gbdt-churn` | 2611.12942 | tabular | TFM advantage against **tuned** GBDTs, with profit and calibration |
| `v4finbench` | 2605.10896 | tabular | imbalance-aware context construction makes finetuned TabPFN match GBDT at long horizons |

Digest: `references/summaries/tabpfn-insurance-pricing.md`. The other five are recorded in the
sweep section with the quote that carries each claim; a digest for them is not proposed because
none is close enough to our data to change a verdict.

## Why

The frontier's losses (`freMTPL2freq`, `spanish_motor_severity`, `bemt97_amount`) were
re-confirmed on v3.5 and the regime note could only *infer* the mechanism. Two of these papers
supply it or supply a candidate remedy, and one is a direct external replication on the same two
public datasets — which the index did not hold, so the project could not have cited it.

## Verification

- `python3 scripts/fm4sd_fetch.py --index` and `--fetch`, then `--index` again.
- `python3 scripts/check_reproducibility.py` 3/3, with the published counts moved in this commit.
- Every quote in the sweep and the digest is taken from the fetched `text.txt`, not from an
  abstract. Where a number exists only as a LaTeX macro, the macro definition is the source.

## Out of scope

- Choosing any remedy, or running one. This records what the literature says; the sibling repo
  decides what to test.
- Digests for the five supporting papers.
- The licence pass (unrun since #66); these rows carry no licence record, as `gnr` does not.
