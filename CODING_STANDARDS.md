# Coding standards

The judgement calls `code-review`'s Standards axis enforces in this repo. Mechanical rules live
in the check that enforces them, not here; `AGENTS.md` carries workflow steering.

A rule earns its place only after review raised the same call more than once. Each one cites
the findings that did.

## 1. Numbers in prose are derived from the artefact, in the same change

Every count, size, split or ratio stated in a plan, PR body or digest is recomputed from the
file it describes at the moment it is written — not carried from an earlier draft, a sibling
document, or memory. If the number comes from a script, run the script; if it comes from a
manifest, read the manifest.

**Why:** a carried number looks verified. It is the one class of error a reader cannot detect
without redoing the work.

**Earned by:** #51 review (PR body said 38 arXiv entries as 36 LaTeX + 2 PDF; the manifest had
37 + 1) and #54 review (a plan headed "nine corrections" over a seventeen-row table).

## 2. A cited paper is described as its own abstract states, and identified by slug or id

When a document leans on a paper, the characterisation must match what that paper says — check
the direction of the claim (which side of a comparison it supports), not just the topic. Identify
the work by its manifest slug or arXiv id; never match a citation by substring, which finds
`activa` inside "activation".

**Why:** a citation with the argument reversed reads as support and is worse than no citation.
Substring matching manufactures citations that do not exist.

**Earned by:** #54 review (cited `2106.03253` as evidence that a tuned XGBoost is easy to beat,
when it is the paper whose deep baselines were tuned far less; called BAMLSS
"distributional-boosting"; matched `activa` inside "activation").

## Not standards

- Stale corpus figures are checked by `scripts/check_reproducibility.py` (#55/#56). Do not
  restate the check as a rule.
- Plan files, worktrees and the reproducibility gate are `AGENTS.md` steering.
