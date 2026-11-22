# Index the credit-risk TFM review, as the counterweight (2026-11-22)

## What

One entry under `other`, one per-paper digest, a round-4 row in the digests index, one
cross-reference from `tabpfn-insurance-pricing.md`, and the published counts that follow.

- `tabular-foundation-models-for-credit-risk-prediction-a-dedicated-review-and-empi` — arXiv:2605.18147, Baesens et al. 2026

## Why

The sweep behind this addition surfaced four papers. Three were already indexed by the time this
branch caught up with `main`: `beyondarena`, `tabpfn-3.5`, and — added in #86 —
`tabpfn-insurance-pricing` (2605.22892), itself a better digest than the one this branch first
carried. Only 2605.18147 was absent.

It is the counterweight to that paper. A review plus empirical comparison of TFMs on credit
risk, whose conjecture is that pretraining pays off **where the target data is small**. Read
alone, `tabpfn-insurance-pricing` invites "TFMs do not work on risk problems"; with this one the
defensible reading is narrower — *TFMs lose where rows are plentiful and a strong offset GLM or
GBDT exists*, which is exactly the regime our `freMTPL2` / `bemTPL97` runs occupy.

## Placement

`- other`, following #86's precedent of filing the companion paper by subject inside an existing
sub-category rather than creating a foundation-model ghetto. Discoverability is handled by the
cross-reference from `tabpfn-insurance-pricing.md` (the place a reader would start) and by the
round-4 row in the digests index, rather than by a new heading for a single paper.

## Gate

`check_reproducibility.py` 3/3 — 440 entries, 28 published figures agree, pair sweep read 25
tracked documents.
