#!/bin/bash
# Misty heartbeat wrapper
# Pre-session: refresh active_lessons.txt from PocketBase.
# Builds enhanced heartbeat prompt, launches Mistral Vibe CLI.
# Post-session: runs summarize_session.py to extract and store new lessons.

PYTHON="/usr/bin/python3"
FLEET="/Users/miguelrodriguez/fleet"
MISTY="$FLEET/misty"
PB_URL="http://localhost:8090/api"
LOG_PREFIX="[misty-wrapper] $(date '+%Y-%m-%d %H:%M:%S')"

post_hb() {
    local status="$1"
    local note="$2"
    curl -s -X POST "$PB_URL/collections/heartbeats/records" \
      -H "Content-Type: application/json" \
      -d "{\"agent\":\"misty\",\"status\":\"$status\",\"note\":\"$note\"}" > /dev/null || true
}

echo "$LOG_PREFIX: starting Misty heartbeat"
if ! "$PYTHON" "$FLEET/scheduler_policy.py" --agent misty; then exit 0; fi

# Phase 0: checksum gate — skip only on autonomous heartbeat runs.
if [ -z "$1" ]; then
    REPO="/Users/miguelrodriguez/projects/agentic-fleet-hub"
    /usr/bin/python3 "$FLEET/heartbeat_check.py" --agent misty --repo "$REPO"
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
post_hb "working" "Starting Misty session"

# Phase 2: build prompt — base + injected lessons
if [ -n "$1" ]; then
    BASE_PROMPT="$1"
else
    BASE_PROMPT="The heartbeat gate has already confirmed action is needed for you. Start from Phase 1 step 3 of AGENTS/RULES.md: run 'python3 fleet/active_context.py', then continue with all remaining steps through Phase 6. Do NOT re-run heartbeat_check.py — it was already run by the wrapper and would return exit 1 (stale checksum). Read ~/projects/agentic-fleet-hub/MISTRAL.md first for your identity."
fi

# Check for active lessons
ACTIVE_LESSONS="$MISTY/active_lessons.txt"
if [ -s "$ACTIVE_LESSONS" ]; then
    LESSONS_BLOCK=$(cat "$ACTIVE_LESSONS")
    FULL_PROMPT="${BASE_PROMPT}

---
${LESSONS_BLOCK}"
else
    FULL_PROMPT="$BASE_PROMPT"
fi

# Phase 3: launch Mistral Vibe CLI in programmatic mode (-p auto-approves all tools)
echo "$LOG_PREFIX: launching Mistral Vibe CLI..."
vibe -p "$FULL_PROMPT" --trust
VIBE_EXIT=$?

echo "$LOG_PREFIX: Vibe exited with code $VIBE_EXIT"

# Phase 4: post idle heartbeat
post_hb "idle" "Session complete"

# Phase 5: branch hygiene — delete task/<pb_id> branches whose ticket is approved
echo "$LOG_PREFIX: cleaning up task branches..."
"$FLEET/cleanup_task_branches.sh" --repo /Users/miguelrodriguez/projects/agentic-fleet-hub
"$FLEET/cleanup_task_branches.sh" --repo /Users/miguelrodriguez/projects/private-core/PrivateCore

echo "$LOG_PREFIX: Misty heartbeat complete"
exit $VIBE_EXIT
