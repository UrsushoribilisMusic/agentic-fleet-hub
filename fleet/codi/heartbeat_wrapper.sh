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
/opt/homebrew/bin/codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  -C /Users/miguelrodriguez/projects/agentic-fleet-hub \
  --add-dir /Users/miguelrodriguez/projects \
  --add-dir "$FLEET" \
  "$CODEX_PROMPT"
CODEX_EXIT=$?
echo "$LOG_PREFIX: Codex exited with code $CODEX_EXIT"

# Phase 3: flush any staged PB writes
echo "$LOG_PREFIX: flushing staged PocketBase writes..."
$PYTHON "$CODI/pb_flush.py"

# Phase 4: branch hygiene — delete task/<pb_id> branches whose ticket is approved
"$FLEET/cleanup_task_branches.sh" --repo /Users/miguelrodriguez/projects/agentic-fleet-hub
"$FLEET/cleanup_task_branches.sh" --repo /Users/miguelrodriguez/projects/private-core/PrivateCore

echo "$LOG_PREFIX: Codi heartbeat complete"
