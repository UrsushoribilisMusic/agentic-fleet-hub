#!/bin/bash
# Muse heartbeat wrapper — checks gate, runs Meta Muse Code CLI, posts heartbeat to PocketBase.

PYTHON="/usr/bin/python3"
FLEET="/Users/miguelrodriguez/fleet"
REPO="/Users/miguelrodriguez/projects/agentic-fleet-hub"
PB_URL="http://localhost:8090/api"
LOG_PREFIX="[muse-wrapper] $(date '+%Y-%m-%d %H:%M:%S')"

post_hb() {
    local status="$1"
    local note="$2"
    curl -s -X POST "$PB_URL/collections/heartbeats/records" \
      -H "Content-Type: application/json" \
      -d "{\"agent\":\"muse\",\"status\":\"$status\",\"note\":\"$note\"}" > /dev/null || true
}

echo "$LOG_PREFIX: starting Muse heartbeat"

# Phase 0: checksum gate — skip only on autonomous heartbeat runs.
if [ -z "$1" ]; then
    "$PYTHON" "$FLEET/heartbeat_check.py" --agent muse --repo "$REPO"
    HB_EXIT=$?
    if [ $HB_EXIT -ne 0 ]; then
        post_hb "idle" "Heartbeat gate returned exit 1: no relevant changes."
        echo "$LOG_PREFIX: No changes detected. Skipping session."
        exit 0
    fi
else
    echo "$LOG_PREFIX: task dispatch detected; bypassing checksum gate."
fi

# Phase 1: post working heartbeat
post_hb "working" "Starting Muse Code CLI session"

# Phase 2: build prompt
if [ -n "$1" ]; then
    PROMPT_TEXT="$1"
else
    PROMPT_TEXT="The heartbeat gate has confirmed action is needed for you. Read ~/projects/agentic-fleet-hub/MUSE.md and ~/projects/agentic-fleet-hub/MISSION_CONTROL.md first, then follow AGENTS/RULES.md (using agent='muse') through all 6 phases. Do NOT re-run heartbeat_check.py."
fi

# Phase 3: launch Muse Code CLI headlessly
echo "$LOG_PREFIX: launching Muse Code CLI..."
/Users/miguelrodriguez/.local/bin/muse exec --yolo --workspace "$REPO" "$PROMPT_TEXT"
MUSE_EXIT=$?

echo "$LOG_PREFIX: Muse exited with code $MUSE_EXIT"

# Phase 4: post idle heartbeat
post_hb "idle" "Session complete (exit $MUSE_EXIT)"

# Phase 5: branch hygiene
"$FLEET/cleanup_task_branches.sh" --repo "$REPO"

echo "$LOG_PREFIX: Muse heartbeat complete"
exit $MUSE_EXIT
