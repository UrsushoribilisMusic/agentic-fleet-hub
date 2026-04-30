#!/usr/bin/env bash
# sync_to_fleet.sh — mirror fleet Python scripts from the repo checkout to ~/fleet/
#
# Run this after committing any change to fleet/*.py, then restart the dispatcher.
# The launchd services (fleet.dispatcher, fleet.github, etc.) always execute from ~/fleet/,
# so the runtime copy must match the committed repo version before services are restarted.
#
# Usage:
#   bash fleet/sync_to_fleet.sh            # mirror only
#   bash fleet/sync_to_fleet.sh --restart  # mirror + bounce dispatcher + github_sync

set -euo pipefail

REPO_FLEET="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$HOME/fleet"

SCRIPTS=(
    dispatcher.py
    github_sync.py
    fleet_sync.py
    fleet_push.py
    heartbeat_check.py
    active_context.py
    telegram_bridge.py
)

echo "[sync_to_fleet] Mirroring from $REPO_FLEET -> $RUNTIME_DIR"
for f in "${SCRIPTS[@]}"; do
    src="$REPO_FLEET/$f"
    dst="$RUNTIME_DIR/$f"
    if [ ! -f "$src" ]; then
        echo "  SKIP $f (not in repo)"
        continue
    fi
    if diff -q "$src" "$dst" >/dev/null 2>&1; then
        echo "  OK   $f (unchanged)"
    else
        cp "$src" "$dst"
        echo "  COPY $f"
    fi
done

if [[ "${1:-}" == "--restart" ]]; then
    echo "[sync_to_fleet] Restarting fleet.dispatcher..."
    launchctl kickstart -k "gui/$(id -u)/fleet.dispatcher"
    echo "[sync_to_fleet] Restarting fleet.github..."
    launchctl kickstart -k "gui/$(id -u)/fleet.github"
    echo "[sync_to_fleet] Done."
else
    echo "[sync_to_fleet] Done. Run with --restart to also bounce the services."
fi
