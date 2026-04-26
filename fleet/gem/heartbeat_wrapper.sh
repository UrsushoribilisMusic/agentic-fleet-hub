#!/bin/bash
# Gem heartbeat wrapper
# Checksum gate: skip session entirely if nothing changed (zero LLM tokens).
# Launches Gemini CLI when changes are detected.

FLEET="/Users/miguelrodriguez/fleet"
PB_URL="http://localhost:8090/api"
LOG_PREFIX="[gem-wrapper] $(date '+%Y-%m-%d %H:%M:%S')"

echo "$LOG_PREFIX: starting Gem heartbeat"

# Phase 0: checksum gate — skip only on autonomous heartbeat runs.
if [ -z "$1" ]; then
    REPO="/Users/miguelrodriguez/projects/agentic-fleet-hub"
    /usr/bin/python3 "$FLEET/heartbeat_check.py" --agent gem --repo "$REPO"
    if [ $? -ne 0 ]; then
        curl -s -X POST "$PB_URL/collections/heartbeats/records" \
            -H "Content-Type: application/json" \
            -d '{"agent":"gem","status":"idle","note":"Heartbeat gate returned exit 1: no relevant changes."}' > /dev/null || true
        echo "$LOG_PREFIX: No changes detected. Skipping session."
        exit 0
    fi
else
    echo "$LOG_PREFIX: task dispatch detected; bypassing checksum gate."
fi

# Phase 1: launch Gemini CLI
echo "$LOG_PREFIX: launching Gemini CLI..."
if [ -n "$1" ]; then
    GEM_PROMPT="$1"
else
    GEM_PROMPT="Run your heartbeat protocol. Read ~/projects/agentic-fleet-hub/GEMINI.md first, then MISSION_CONTROL.md, then AGENTS/RULES.md, then AGENTS/MESSAGES/inbox.json. Follow all 6 phases."
fi
/opt/homebrew/bin/node /opt/homebrew/bin/gemini \
    --yolo \
    -p "$GEM_PROMPT"
GEM_EXIT=$?
echo "$LOG_PREFIX: Gemini exited with code $GEM_EXIT"

# Phase 2: branch hygiene — delete task/<pb_id> branches whose ticket is approved
"$FLEET/cleanup_task_branches.sh" --repo /Users/miguelrodriguez/projects/agentic-fleet-hub
"$FLEET/cleanup_task_branches.sh" --repo /Users/miguelrodriguez/projects/private-core/PrivateCore

echo "$LOG_PREFIX: Gem heartbeat complete"
