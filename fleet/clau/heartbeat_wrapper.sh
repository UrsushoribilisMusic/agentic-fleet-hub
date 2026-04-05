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
LOG_PREFIX="[clau-wrapper] $(date '+%Y-%m-%d %H:%M:%S')"

echo "$LOG_PREFIX: starting Clau heartbeat"

# Phase 0: checksum gate — skip if nothing changed (zero LLM tokens)
REPO="/Users/miguelrodriguez/projects/agentic-fleet-hub"
/usr/bin/python3 "$FLEET/heartbeat_check.py" --agent clau --repo "$REPO"
if [ $? -ne 0 ]; then
    echo "$LOG_PREFIX: No changes detected. Skipping session."
    exit 0
fi

# Phase 1: refresh active_lessons.txt (pre-session)
echo "$LOG_PREFIX: refreshing active lessons..."
$PYTHON "$SUMMARIZE" --pre
PRE_EXIT=$?
if [ $PRE_EXIT -ne 0 ]; then
    echo "$LOG_PREFIX: WARN summarize_session --pre exited $PRE_EXIT (continuing)"
fi

# Phase 2: build prompt — base + injected lessons
BASE_PROMPT="Run your heartbeat protocol. Read ~/fleet/MISSION_CONTROL.md first."

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
    -p "$FULL_PROMPT"
CLAUDE_EXIT=$?
echo "$LOG_PREFIX: Claude exited with code $CLAUDE_EXIT"

# Phase 4: post-session lesson extraction
echo "$LOG_PREFIX: running post-session summarizer..."
$PYTHON "$SUMMARIZE" --post
POST_EXIT=$?
if [ $POST_EXIT -ne 0 ]; then
    echo "$LOG_PREFIX: WARN summarize_session --post exited $POST_EXIT"
fi

echo "$LOG_PREFIX: Clau heartbeat complete"
