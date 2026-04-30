#!/usr/bin/env bash
# Sync repo fleet/ scripts to /Users/miguelrodriguez/fleet/ runtime and bounce launchd.
# Run after committing fleet code in agentic-fleet-hub. Without this, launchd keeps
# running stale copies (the bug that hid #225 for hours on 2026-04-28).
#
# Usage:  ./fleet/deploy_runtime.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)/fleet"
RUNTIME="/Users/miguelrodriguez/fleet"

# Files that exist in both repo and runtime — runtime-only scripts (telegram_bridge,
# fleet_push, tcr_*, etc.) are intentionally left alone.
FILES=(
  active_context.py
  dispatcher.py
  fleet_sync.py
  github_sync.py
  heartbeat_check.py
  codi/heartbeat_wrapper.sh
  codi/pb_flush.py
  codi/pb_fetch.py
  codi/heartbeat_prompt.txt
  clau/heartbeat_wrapper.sh
  gem/heartbeat_wrapper.sh
  gemma/GEMMA.md
  gemma/run_heartbeat.sh
)

# launchd services that import the synced files and need a bounce after copy.
SERVICES=(
  fleet.dispatcher
  fleet.github
  fleet.gemma
)

echo "=== sync repo → runtime ==="
ts=$(date +%Y%m%d-%H%M%S)
mkdir -p "$RUNTIME/_backup_$ts"
for f in "${FILES[@]}"; do
  if [ ! -f "$REPO/$f" ]; then
    echo "  WARN: $f not in repo — skipping"
    continue
  fi
  mkdir -p "$(dirname "$RUNTIME/_backup_$ts/$f")"
  if [ -f "$RUNTIME/$f" ]; then
    cp "$RUNTIME/$f" "$RUNTIME/_backup_$ts/$f"
  fi
  mkdir -p "$(dirname "$RUNTIME/$f")"
  cp "$REPO/$f" "$RUNTIME/$f"
  # Runtime shell/Python entrypoints need exec bit.
  case "$f" in *heartbeat_wrapper.sh|*run_heartbeat.sh|*pb_flush.py|*pb_fetch.py) chmod +x "$RUNTIME/$f" ;; esac
  echo "  $f"
done
echo "  backup at $RUNTIME/_backup_$ts"

echo
echo "=== bounce launchd services ==="
for svc in "${SERVICES[@]}"; do
  plist="$HOME/Library/LaunchAgents/${svc}.plist"
  if [ ! -f "$plist" ]; then
    echo "  WARN: $plist missing — skipping"
    continue
  fi
  launchctl unload "$plist" 2>/dev/null || true
  pkill -f "$RUNTIME/${svc#fleet.}.py" 2>/dev/null || true
  sleep 1
  launchctl load "$plist"
  echo "  $svc reloaded"
done

echo
echo "=== verify processes ==="
for svc in "${SERVICES[@]}"; do
  proc_name="${svc#fleet.}"
  pid=$(pgrep -f "$RUNTIME/${proc_name}.py" | head -1)
  if [ -n "$pid" ]; then
    echo "  $svc: pid $pid running"
  else
    echo "  $svc: NOT running (check launchd logs)"
  fi
done

echo
echo "Done. Runtime now matches repo HEAD."
