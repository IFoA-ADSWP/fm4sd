# Plan — bootstrap CODING_STANDARDS.md (2026-10-31)

Ticket #59, retro candidate #3. `code-review`'s Standards axis currently falls back to the Fowler
smell baseline plus `AGENTS.md`, so each judgement call is re-argued per review.

## What

One small `CODING_STANDARDS.md` at the repo root, containing only judgement calls that review
raised **more than once** in this repo — the `standards` skill's promotion threshold. Each rule
carries the finding that earned it.

Two rules qualify; one candidate does not (recorded in the ticket, not the file). Mechanical
candidates go to checks: the stale-figure class already became #55/#56 and is not restated here.

## Why

A rule that appeared once may be a reviewer's taste. Writing it down anyway turns the standards
file into a parking lot and teaches reviewers to enforce opinions. Two recurrences is the
cheapest evidence a repo can offer that a call is its call.

## Verification

- Every rule names its evidence (PR numbers, both sides of each finding).
- No rule restates `AGENTS.md` (plans, worktrees, gate) — those are steering.
- No mechanical rule is written as prose; the stale-figure check is pointed at, not duplicated.
- File stays judgement-only; well under the 1,000-line split threshold.

## Out of scope

- Promoting single-occurrence findings (marker vocabulary; see #59's body).
- Moving `AGENTS.md` steering into standards, or the reverse.
- Any new CI check.
