# Apply the digest corrections from #52 (#53)

Plan written 2026-10-31, before the first edit to `references/summaries/`.

## What this lands

Nine corrections to six digests, taken from the research review
`research/digest-impact-2026-10-31.md` on `research/digest-impact` (#52, never merged). The #47
block of 48 comparison entries is now indexed; this change makes the digests read it.

Files touched, and nothing else:

| File | Edits |
|---|---|
| `references/summaries/tabicl.md` | narrow the "closest published support" claim (`:51`); cite CatBoost (`:30`) |
| `references/summaries/SWEEPS.md` | "no published counterpart" → no *ICL* counterpart (`:242`); supersession note for the D2 claim (`:288`); narrow "a specified loss family and enough data" (`:299`); name the instrument for record 11's half-sigma margin (`:98`); benchmark-lottery citation at the TabArena saturation caveat and at the RF-matched target (`:143`, `:107`) |
| `references/summaries/actuarial.md` | Tweedie-in-a-GBDT is untested *by us*, not unpublished (`:62`); CatBoost library citation (`:70`); "the actuarial ML literature picks CatBoost" → one paper, two datasets, three libraries (`:86`); the baseline is a depth-3/4-tree GBDT, so "beats the GBDT" carries that qualifier (`:88`); the actuarial literature now *reviews* TFMs but still publishes no tail evaluation (`:125`) |
| `references/summaries/modded-nanotabpfn.md` | RF-matched target is RF parity, not GBDT parity (`:54`) |
| `references/summaries/nanotabpfn.md` | the k-NN/DT/RF comparison is against default-config baselines (`:43`) |
| `references/summaries/baps.md` | name what is missing — calibrated distributional regression, T-reliability (`:56`); make the ECE caveat actionable (`:62`) |

`README.md`, `references/manifest.json`, `PROVENANCE.md` and `scripts/` are untouched. No entry is
added or removed, so no published count moves and `PROVENANCE.md` needs no edit.

## How each edit is written

- **Quote first, then correct.** Where a sentence is narrowed, the original wording is kept and
  the correction is stated next to it, dated, with the reason. Nothing is silently rewritten to
  mean something else, and no claim disappears without a note saying why it moved.
- **Cite the entry that bears on it** — slug plus identifier, e.g. `catboost` (1706.09516).
  Where an entry has no arXiv id (QRF, Lambert 1992, Mullahy 1986, Mack 1993, England & Verrall
  2002), the citation is slug plus author-year, taken from the manifest.
- **`SWEEPS.md` keeps its history.** It already carries a dated `⚠️ CORRECTION` block and a
  `> **PARTLY SUPERSEDED 2026-10-08**` blockquote. The D2 and record-11 corrections are added as
  a new dated note under the existing one, in the same style; the superseded sentences stay.
- **Seven of the nine new actuarial entries are payload-less** (`skipped:unreachable:paywall`,
  one `skipped:unreachable:unknown`): `frees-2009`, `jørgensen-1994`, `lambert-1992`,
  `mullahy-1986`, `mack-1993`, `england-and-verrall-2002`, `blier-wong-2021`. They are cited by
  presence and title only — **no text of theirs is quoted anywhere in this change**. Only
  `towards-foundation-models-for-insurance-risk-modelling` (2609.14576) and `the-actuary-and-ibnr`
  have payload, and this change quotes neither.

## Why these nine

The #47 block mostly *supplies citations*; what it actually shifts is (a) the "TFMs beat GBDT
once data is not scarce" generalisation and (b) what the project's GBDT baseline is. Those are
the two places where a digest sentence would now mislead a reader, and the rest are stale claims
that #47 (or the 2026-10-08 actuarial block) has overtaken. Corrections that would only decorate
a sentence were left alone by #52 and are left alone here — the review's "checked and left alone"
table is the record of that judgement.

## Verification

1. `python3 scripts/check_reproducibility.py` → 3/3. Digests are not gated (they are manual
   prose, per `AGENTS.md`); the run proves the index, manifest and published counts were not
   disturbed.
2. `git diff --stat` confined to `references/summaries/` plus this plan.
3. Re-read each edited line in context for factual agreement with
   `research/digest-impact-2026-10-31.md`.
