# Plan — dispatch helper for one-writer-per-worktree (2026-10-31)

Ticket #57, retro candidate #2. Evidence: on 2026-10-31 five research agents shared one clone; a
commit landed on `main` and another branch's push carried no commit. The rule was written in the
global AGENTS.md and did not fire because dispatch prompts were hand-written prose.

## What

- `scripts/new-worktree.sh <branch> [base]` — refuses an existing branch or path, creates
  `<repo>-wt/<branch-dashed>` from the base (default `origin/main`), prints the worktree path, a
  dispatch line and the `workload.sh` verification command.
- Two lines in `AGENTS.md`: dispatching a writer means running the script and quoting its output;
  one writer per worktree.

## Why

A script is the only part of the dispatch that can refuse. Prose is advisory; a helper that fails
on a duplicate branch turns "remember to isolate writers" into a command whose output the prompt
quotes verbatim.

## Verification

- Run in a scratch clone: creates branch + worktree, prints both paths.
- Second run for the same branch refuses; a run with an existing path refuses.
- `bash -n`; `shellcheck --severity=warning`.

## Out of scope

- Automating the dispatch itself (the harness prompt is not repo state).
- Moving existing worktrees or rewriting branch naming.
