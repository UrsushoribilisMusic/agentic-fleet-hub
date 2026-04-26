#!/bin/bash
# cleanup_task_branches.sh — delete task/<pb_id> branches whose ticket is
# `approved` in PocketBase.
#
# Called from each agent's heartbeat_wrapper.sh as a final cleanup phase.
# Safe to run from any repo: operates on whatever cwd is.
#
# Usage:
#   cleanup_task_branches.sh                      # all approved tickets
#   cleanup_task_branches.sh --dry-run            # report only, no deletes
#   cleanup_task_branches.sh --repo /path/to/repo
#
# Skips branches whose ticket is in (todo, in_progress, peer_review) so
# agents can return to in-flight work.

set -e

DRY_RUN=0
REPO_ARG=""
PB_URL="http://127.0.0.1:8090/api/collections/tasks/records"
LOG_PREFIX="[cleanup-branches]"

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --repo)    REPO_ARG="$2"; shift 2 ;;
    *)         shift ;;
  esac
done

[ -n "$REPO_ARG" ] && cd "$REPO_ARG"

# Bail quietly if not a git repo
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

# Skip if HEAD is currently on a task/ branch (don't delete checked-out branch)
CURRENT="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
if [[ "$CURRENT" == task/* ]]; then
  echo "$LOG_PREFIX: HEAD on $CURRENT — switching to default branch first"
  DEFAULT="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|.*origin/||')"
  [ -z "$DEFAULT" ] && DEFAULT="main"
  git checkout "$DEFAULT" 2>/dev/null || git checkout master 2>/dev/null || true
fi

# Collect candidate task branches (local + origin) — only ones matching
# task/<pb_id> where pb_id looks like a hex string (typical PB record id).
LOCAL_TASKS="$(git branch | sed 's/^[* ] //' | grep -E '^task/[a-z0-9]{8,}$' || true)"
ORIGIN_TASKS="$(git branch -r | sed 's|.*origin/||' | grep -E '^task/[a-z0-9]{8,}$' || true)"

# Also handle non-hex task branches (numeric like task/101 or named like
# task/atf8-local-model-adapter) — these are old, never resolved by PB lookup,
# so we only delete them if they're fully merged into the default branch.
DEFAULT_BRANCH="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|.*origin/||')"
[ -z "$DEFAULT_BRANCH" ] && DEFAULT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

DELETED=0
SKIPPED=0

check_and_delete() {
  local branch="$1"
  local origin="$2"   # 1 if also on origin
  local pb_id="${branch#task/}"

  # Skip if pb_id doesn't look like a PB record id (8+ alnum)
  if ! [[ "$pb_id" =~ ^[a-z0-9]{8,}$ ]]; then
    # Non-PB branch (numeric / named) — only delete if fully merged
    local ahead=$(git rev-list "origin/$DEFAULT_BRANCH..origin/$branch" --count 2>/dev/null || echo 99)
    if [ "$ahead" = "0" ]; then
      do_delete "$branch" "$origin" "fully merged"
    else
      SKIPPED=$((SKIPPED+1))
    fi
    return
  fi

  # Look up PB ticket status
  local status
  status=$(curl -s --max-time 3 "$PB_URL/$pb_id" 2>/dev/null \
            | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("status",""))' 2>/dev/null \
            || echo "")

  case "$status" in
    approved|"")
      # approved → safe; "" (404 / unreachable) → likely deleted ticket, also safe
      do_delete "$branch" "$origin" "PB status: ${status:-unknown/deleted}"
      ;;
    todo|in_progress|peer_review)
      SKIPPED=$((SKIPPED+1))
      [ "$DRY_RUN" = "1" ] && echo "$LOG_PREFIX: skip $branch (in-flight: $status)"
      ;;
    *)
      SKIPPED=$((SKIPPED+1))
      [ "$DRY_RUN" = "1" ] && echo "$LOG_PREFIX: skip $branch (unknown status: $status)"
      ;;
  esac
}

do_delete() {
  local branch="$1"
  local on_origin="$2"
  local reason="$3"
  if [ "$DRY_RUN" = "1" ]; then
    echo "$LOG_PREFIX: WOULD delete $branch ($reason)"
  else
    git branch -D "$branch" >/dev/null 2>&1 || true
    if [ "$on_origin" = "1" ]; then
      git push origin --delete "$branch" >/dev/null 2>&1 || true
    fi
    echo "$LOG_PREFIX: deleted $branch ($reason)"
  fi
  DELETED=$((DELETED+1))
}

# Build set of branches to check (union of local + origin)
ALL_TASKS="$(echo -e "$LOCAL_TASKS\n$ORIGIN_TASKS" | sort -u | grep -v '^$' || true)"

for branch in $ALL_TASKS; do
  on_origin=0
  echo "$ORIGIN_TASKS" | grep -qx "$branch" && on_origin=1
  check_and_delete "$branch" "$on_origin"
done

if [ "$DELETED" -gt 0 ] || [ "$SKIPPED" -gt 0 ]; then
  echo "$LOG_PREFIX: done — deleted=$DELETED skipped=$SKIPPED"
fi
