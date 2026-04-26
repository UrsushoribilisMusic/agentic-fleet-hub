#!/bin/bash
# Clau heartbeat wrapper
# Pre-session: refresh active_lessons.txt from PocketBase.
# Builds enhanced heartbeat prompt, launches Claude Code.
# Post-session: runs summarize_session.py to extract and store new lessons.

PYTHON="/usr/bin/python3"
FLEET="/Users/miguelrodriguez/fleet"
CLAU="$FLEET/clau"
SUMMARIZE="$CLAU/summarize_session.py"
ACTIVE_LESSONS="$CLAU/active_lessons.txt"
PB_URL="http://localhost:8090/api"
LOG_PREFIX="[clau-wrapper] $(date '+%Y-%m-%d %H:%M:%S')"
CLAUDE_TMP="$(mktemp -t clau_heartbeat.XXXXXX)"

post_hb() {
    local status="$1"
    local note="$2"
    curl -s -X POST "$PB_URL/collections/heartbeats/records" \
      -H "Content-Type: application/json" \
      -d "{\"agent\":\"clau\",\"status\":\"$status\",\"note\":\"$note\"}" > /dev/null || true
}

echo "$LOG_PREFIX: starting Clau heartbeat"

# Phase 0: checksum gate — skip only on autonomous heartbeat runs.
if [ -z "$1" ]; then
    REPO="/Users/miguelrodriguez/projects/agentic-fleet-hub"
    /usr/bin/python3 "$FLEET/heartbeat_check.py" --agent clau --repo "$REPO"
    if [ $? -ne 0 ]; then
        post_hb "idle" "Heartbeat gate returned exit 1: no relevant changes."
        echo "$LOG_PREFIX: No changes detected. Skipping session."
        exit 0
    fi
else
    echo "$LOG_PREFIX: task dispatch detected; bypassing checksum gate."
fi

# Phase 1: refresh active_lessons.txt (pre-session)
echo "$LOG_PREFIX: refreshing active lessons..."
$PYTHON "$SUMMARIZE" --pre
PRE_EXIT=$?
if [ $PRE_EXIT -ne 0 ]; then
    echo "$LOG_PREFIX: WARN summarize_session --pre exited $PRE_EXIT (continuing)"
fi

# Phase 2: build prompt — base + injected lessons
if [ -n "$1" ]; then
    BASE_PROMPT="$1"
else
    BASE_PROMPT="Run your heartbeat protocol. Read ~/projects/agentic-fleet-hub/CLAUDE.md first, then MISSION_CONTROL.md, then AGENTS/RULES.md, then AGENTS/MESSAGES/inbox.json. Follow all 6 phases."
fi

if [ -s "$ACTIVE_LESSONS" ]; then
    LESSONS_BLOCK=$(cat "$ACTIVE_LESSONS")
    FULL_PROMPT="${BASE_PROMPT}

---
${LESSONS_BLOCK}"
else
    FULL_PROMPT="$BASE_PROMPT"
fi

# Phase 3: launch Claude Code
echo "$LOG_PREFIX: launching Claude Code..."
/Users/miguelrodriguez/.local/bin/claude \
    --dangerously-skip-permissions \
    -p "$FULL_PROMPT" >"$CLAUDE_TMP" 2>&1
CLAUDE_EXIT=$?
cat "$CLAUDE_TMP"

if grep -q "You're out of extra usage" "$CLAUDE_TMP"; then
    post_hb "quota" "Claude reported quota exhaustion; resets at 7pm Europe/Zurich."
fi

echo "$LOG_PREFIX: Claude exited with code $CLAUDE_EXIT"
rm -f "$CLAUDE_TMP"

# Phase 4: post-session lesson extraction
echo "$LOG_PREFIX: running post-session summarizer..."
$PYTHON "$SUMMARIZE" --post
POST_EXIT=$?
if [ $POST_EXIT -ne 0 ]; then
    echo "$LOG_PREFIX: WARN summarize_session --post exited $POST_EXIT"
fi

# Phase 5: branch hygiene — delete task/<pb_id> branches whose ticket is approved
"$FLEET/cleanup_task_branches.sh" --repo /Users/miguelrodriguez/projects/agentic-fleet-hub
"$FLEET/cleanup_task_branches.sh" --repo /Users/miguelrodriguez/projects/private-core/PrivateCore

echo "$LOG_PREFIX: Clau heartbeat complete"
exit $CLAUDE_EXIT
