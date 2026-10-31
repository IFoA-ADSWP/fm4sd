#!/usr/bin/env bash
# new-worktree.sh — give one dispatched writer its own working copy.
#
# Usage: scripts/new-worktree.sh <branch> [base]
#   <branch>  branch to create, e.g. enhancement/57-dispatch-worktree
#   [base]    commit to start from (default: origin/main)
#
# Prints the worktree path, a dispatch line naming it, and the workload check.
# Refuses a branch or path that already exists, so two writers cannot be sent
# to one copy by accident (#57).

set -euo pipefail

die() { printf 'new-worktree: %s\n' "$*" >&2; exit 1; }

[[ $# -ge 1 && $# -le 2 ]] || die "usage: scripts/new-worktree.sh <branch> [base]"
branch="$1"
base="${2:-origin/main}"

[[ "$branch" =~ ^[A-Za-z0-9._/-]+$ ]] || die "branch '$branch' has characters git will not accept"
[[ "$branch" == -* ]] && die "branch '$branch' must not start with '-'"
[[ "$branch" != */ && "$branch" != *//* ]] || die "branch '$branch' has an empty path segment"
[[ "$branch" != "main" ]] || die "refusing to branch off 'main' for a writer: pass a feature branch name"

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || die "not inside a git repository"
# Anchor on the main working tree, not the worktree this happens to run from, so a
# writer dispatched from inside another worktree still lands beside the main clone.
main_root=$(git -C "$repo_root" worktree list --porcelain | awk 'NR==1{sub(/^worktree /,""); print}')
[[ -n "$main_root" ]] || die "could not resolve the main working tree"

git -C "$repo_root" fetch origin --quiet 2>/dev/null || true
git -C "$repo_root" rev-parse --verify --quiet "$base" >/dev/null \
  || die "base '$base' does not exist; fetch it first"

git -C "$repo_root" show-ref --verify --quiet "refs/heads/$branch" \
  && die "branch '$branch' already exists — pick another, or reuse its worktree"

slug=${branch//\//-}
parent="$(dirname "$main_root")/$(basename "$main_root")-wt"
path="$parent/$slug"

[[ -e "$path" ]] && die "worktree path already exists: $path"

mkdir -p "$parent"
if ! out=$(git -C "$repo_root" worktree add -b "$branch" "$path" "$base" 2>&1); then
  printf '%s\n' "$out" >&2
  die "git worktree add failed"
fi

printf '\nworktree: %s\n' "$path"
printf 'branch:   %s (from %s)\n\n' "$branch" "$base"
printf 'dispatch line:\n'
printf '  Work ONLY in %s. Do not read or write %s.\n\n' "$path" "$main_root"
printf 'verify:\n  ~/.config/opencode/scripts/workload.sh %s\n\n' "$main_root"
