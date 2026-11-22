# tabular-foundation-models-for-credit-risk-prediction — a review and comparison, and the counterweight

arXiv [2605.18147](https://arxiv.org/abs/2605.18147)
Baesens, Goethals, Lessmann, De Vos et al. 2026.

## Why this is here

It is the counterweight to
[tabpfn-insurance-pricing](tabpfn-insurance-pricing.md). That paper says a tabular foundation
model loses to a GLM on insurance frequency; read alone it invites the conclusion that TFMs do
not work on risk problems. This one reviews and empirically compares them on **credit risk** and
expects the opposite result in the regime where it argues they should win.

## What it says

- Gradient boosting is consolidated by decades of benchmarking as the **strongest ML benchmark**
  for default-probability and loss modelling; linear and logistic models remain the **regulatory
  and industry reference**.
- TFMs replace fitting with in-context learning, integrating the target dataset with knowledge
  from large-scale pretraining on diverse (synthetic) tabular collections.
- The authors' conjecture: access to information **beyond the target data** pays off in
  **small-data settings**.

## Why it matters to this repository

It bounds the negative. If the pricing result holds generally, the programme's conclusion is
"TFMs are not competitive for insurance pricing"; if the small-data conjecture is right, the
correct conclusion is narrower — *TFMs lose where rows are plentiful and a strong offset GLM or
GBDT exists*, which is precisely the regime our `freMTPL2` / `bemTPL97` runs occupy. The two
papers together are the strongest available argument that **regime, not model family, is the
finding**.

## What it does not say

Credit risk is not insurance: different target, different exposure structure, different
regulatory constraints. It is a review plus the authors' own comparison, not a run on our data,
and nothing here reports a tail-accuracy measure. Treat the direction of its result as the
usable part; do not import its numbers.
