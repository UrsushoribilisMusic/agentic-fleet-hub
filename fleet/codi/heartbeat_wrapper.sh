#!/bin/bash
# Codi heartbeat wrapper — pre-fetches PocketBase context, launches Codex,
# then flushes any staged PB writes after the session exits.

PYTHON="/usr/bin/python3"
FLEET="/Users/miguelrodriguez/fleet"
CODI="$FLEET/codi"
PROMPT="$CODI/heartbeat_prompt.txt"
LOG_PREFIX="[wrapper] $(date '+%Y-%m-%d %H:%M:%S')"

echo "$LOG_PREFIX: starting Codi heartbeat"

# Phase 0: checksum gate — skip if nothing changed (zero LLM tokens)
REPO="/Users/miguelrodriguez/projects/agentic-fleet-hub"
/usr/bin/python3 "$FLEET/heartbeat_check.py" --agent codi --repo "$REPO"
if [ $? -ne 0 ]; then
    echo "$LOG_PREFIX: No changes detected. Skipping session."
    exit 0
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
CODEX_PROMPT=$(cat "$PROMPT")
/opt/homebrew/bin/node /opt/homebrew/bin/codex exec \
  -s workspace-write \
  --skip-git-repo-check \
  -C /Users/miguelrodriguez/projects/agentic-fleet-hub \
  --add-dir "$FLEET" \
  "$CODEX_PROMPT"
CODEX_EXIT=$?
echo "$LOG_PREFIX: Codex exited with code $CODEX_EXIT"

# Phase 3: flush any staged PB writes
echo "$LOG_PREFIX: flushing staged PocketBase writes..."
$PYTHON "$CODI/pb_flush.py"

echo "$LOG_PREFIX: Codi heartbeat complete"
exit $CODEX_EXIT
