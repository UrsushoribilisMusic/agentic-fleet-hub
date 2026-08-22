#!/bin/bash
# Wrapper for the launchd-scheduled TS-5 X cross-post.
# Idempotent (marker file prevents double-post) + self-removes the agent once posted.
HERE="$HOME/projects/agentic-fleet-hub/tech-shorts"
LOG="$HERE/ts5_run.log"
MARKER="$HERE/.ts5_posted"
LABEL="cc.flotilla.ts5-edge"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') TS-5 fire ===" >> "$LOG"

selfremove() {
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
  rm -f "$PLIST"
  echo "  agent removed" >> "$LOG"
}

if [ -f "$MARKER" ]; then
  echo "  marker present — already posted; removing agent" >> "$LOG"
  selfremove
  exit 0
fi

/usr/bin/python3 "$HERE/ts5_scheduled_post.py" >> "$LOG" 2>&1
RC=$?
if [ "$RC" -eq 0 ]; then
  touch "$MARKER"
  echo "  POSTED (rc=0) — self-removing" >> "$LOG"
  selfremove
else
  echo "  not posted (rc=$RC) — will retry at next scheduled time" >> "$LOG"
fi
exit 0
