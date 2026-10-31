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

**Why:** a carried number looks verified. Nothing downstream re-derives it.

**Scope:** corpus figures in tracked documents are already checked by
`scripts/check_reproducibility.py` (#55/#56). This rule covers the places that check cannot
read: plan files' prose, PR bodies, and digests.

**Earned by:** #51 review (PR body said 38 arXiv entries as 36 LaTeX + 2 PDF; the manifest had
37 + 1) and #54 review (a plan headed "nine corrections" over a seventeen-row table).

## Not yet promoted

Raised once each; they stay review comments until a second finding gives them a citation.

- **A cited paper is described as its own abstract states.** #54 review: `2106.03253` was cited
  as evidence that a tuned XGBoost is easy to beat, when its abstract says XGBoost *outperforms*
  the deep models and needs less tuning. That review also found
  `bayesian-structured-additive-distributional-regression` (1509.05230) described as
  "distributional-boosting" (it is distributional regression; the boosting arm is NGBoost,
  `1910.03225`).
- **One correction-marker vocabulary per document.** #54: seven one-off labels in one file.

## Not standards

- Stale corpus figures in tracked documents: checked by `scripts/check_reproducibility.py`
  (#55/#56). Do not restate the check as a rule.
- Plan files, worktrees and the reproducibility gate are `AGENTS.md` steering.
