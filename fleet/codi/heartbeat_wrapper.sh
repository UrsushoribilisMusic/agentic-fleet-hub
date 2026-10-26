#!/bin/bash
# Codi heartbeat wrapper — pre-fetches PocketBase context, launches Codex,
# then flushes any staged PB writes after the session exits.

PYTHON="/usr/bin/python3"
FLEET="/Users/miguelrodriguez/fleet"
CODI="$FLEET/codi"
PROMPT="$CODI/heartbeat_prompt.txt"
PB_URL="http://localhost:8090/api"
LOG_PREFIX="[wrapper] $(date '+%Y-%m-%d %H:%M:%S')"

echo "$LOG_PREFIX: starting Codi heartbeat"

# Finish a previously verified transition before starting another model review.
if ! "$PYTHON" "$CODI/pb_flush.py"; then
  echo "$LOG_PREFIX: pending writes need attention; skipping model."
  exit 1
fi
if ! "$PYTHON" "$FLEET/scheduler_policy.py" --agent codi; then exit 0; fi

# Phase 0.0: usage-limit cooldown gate.
# Prevents the 2026-08-04 runaway (~9k Codex invocations / 2.3k usage-limit
# errors that drained the weekly Codex limit): if a prior run reported a usage
# limit, back off instead of re-invoking Codex on every heartbeat.
COOLDOWN_FILE="$FLEET/.fleet_cache/codi_usage_cooldown"
NOW_EPOCH=$(date +%s)
if [ -f "$COOLDOWN_FILE" ]; then
  UNTIL=$(cat "$COOLDOWN_FILE" 2>/dev/null)
  if [ -n "$UNTIL" ] && [ "$UNTIL" -gt "$NOW_EPOCH" ] 2>/dev/null; then
    echo "$LOG_PREFIX: usage-limit cooldown active (until $(date -r "$UNTIL" '+%Y-%m-%d %H:%M')). Skipping session."
    curl -s -X POST "$PB_URL/collections/heartbeats/records" -H "Content-Type: application/json" \
      -d '{"agent":"codi","status":"idle","note":"Codex usage-limit cooldown active; skipping run."}' > /dev/null || true
    exit 0
  fi
fi

# Phase 0: checksum gate — skip only on autonomous heartbeat runs.
if [ -z "$1" ]; then
  REPO="/Users/miguelrodriguez/projects/agentic-fleet-hub"
  /usr/bin/python3 "$FLEET/heartbeat_check.py" --agent codi --repo "$REPO"
  if [ $? -ne 0 ]; then
      curl -s -X POST "$PB_URL/collections/heartbeats/records" \
        -H "Content-Type: application/json" \
        -d '{"agent":"codi","status":"idle","note":"Heartbeat gate returned exit 1: no relevant changes."}' > /dev/null || true
      echo "$LOG_PREFIX: No changes detected. Skipping session."
      exit 0
  fi
else
  echo "$LOG_PREFIX: task dispatch detected; bypassing checksum gate."
fi

# Phase 1: fetch PB snapshot (retry up to 3x to handle launchd early startup)
echo "$LOG_PREFIX: fetching PocketBase snapshot..."
for i in 1 2 3; do
  $PYTHON "$CODI/pb_fetch.py" && break
  echo "$LOG_PREFIX: pb_fetch attempt $i failed, retrying in 5s..."
  sleep 5
done

# Phase 2: launch Codex with prompt from file
echo "$LOG_PREFIX: launching Codex..."
if [ -n "$1" ]; then
  CODEX_PROMPT="$1"
else
  CODEX_PROMPT=$(cat "$PROMPT")
fi
CODEX_OUT="$CODI/last_codex_output.log"
/opt/homebrew/bin/codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  -C /Users/miguelrodriguez/projects/private-core/PrivateCore \
  --add-dir /Users/miguelrodriguez/projects/private-core \
  --add-dir /Users/miguelrodriguez/projects/agentic-fleet-hub \
  --add-dir /Users/miguelrodriguez/projects/sovereign-mind \
  --add-dir /Users/miguelrodriguez/projects/agentic-fleet-hub/.fleet_cache \
  --add-dir "$FLEET" \
  "$CODEX_PROMPT" 2>&1 | tee "$CODEX_OUT"
CODEX_EXIT=${PIPESTATUS[0]}
echo "$LOG_PREFIX: Codex exited with code $CODEX_EXIT"

# Usage-limit backoff: if Codex reported a usage/rate limit, set a cooldown so we
# stop re-invoking it every heartbeat until it recovers (weekly limit self-clears
# via periodic retries). Prevents the 2026-08-04 hammering incident.
if grep -qiE "usage limit|rate limit|try again at" "$CODEX_OUT" 2>/dev/null; then
  COOLDOWN_SECS=21600   # 6h
  echo "$(( NOW_EPOCH + COOLDOWN_SECS ))" > "$COOLDOWN_FILE"
  echo "$LOG_PREFIX: ⚠ Codex usage limit detected — cooldown set for ${COOLDOWN_SECS}s."
  curl -s -X POST "$PB_URL/collections/heartbeats/records" -H "Content-Type: application/json" \
    -d '{"agent":"codi","status":"blocked","note":"Codex usage limit hit; 6h cooldown set (see 2026-08-04 incident)."}' > /dev/null || true
fi

# Phase 3: flush any staged PB writes
echo "$LOG_PREFIX: flushing staged PocketBase writes..."
$PYTHON "$CODI/pb_flush.py"
FLUSH_EXIT=$?

# Phase 4: branch hygiene — delete task/<pb_id> branches whose ticket is approved
"$FLEET/cleanup_task_branches.sh" --repo /Users/miguelrodriguez/projects/agentic-fleet-hub
"$FLEET/cleanup_task_branches.sh" --repo /Users/miguelrodriguez/projects/private-core/PrivateCore

echo "$LOG_PREFIX: Codi heartbeat complete"
if [ "$FLUSH_EXIT" -ne 0 ]; then exit "$FLUSH_EXIT"; fi
exit "$CODEX_EXIT"
