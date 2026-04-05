#!/bin/bash
# Gem heartbeat wrapper
# Checksum gate: skip session entirely if nothing changed (zero LLM tokens).
# Launches Gemini CLI when changes are detected.

FLEET="/Users/miguelrodriguez/fleet"
LOG_PREFIX="[gem-wrapper] $(date '+%Y-%m-%d %H:%M:%S')"

echo "$LOG_PREFIX: starting Gem heartbeat"

# Phase 0: checksum gate — skip if nothing changed (zero LLM tokens)
REPO="/Users/miguelrodriguez/projects/agentic-fleet-hub"
/usr/bin/python3 "$FLEET/heartbeat_check.py" --agent gem --repo "$REPO"
if [ $? -ne 0 ]; then
    echo "$LOG_PREFIX: No changes detected. Skipping session."
    exit 0
fi

# Phase 1: launch Gemini CLI
echo "$LOG_PREFIX: launching Gemini CLI..."
/opt/homebrew/bin/node /opt/homebrew/bin/gemini \
    --yolo \
    -p "Run your heartbeat protocol. Read ~/fleet/MISSION_CONTROL.md first."
GEM_EXIT=$?
echo "$LOG_PREFIX: Gemini exited with code $GEM_EXIT"

echo "$LOG_PREFIX: Gem heartbeat complete"
