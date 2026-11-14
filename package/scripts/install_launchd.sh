#!/bin/bash
# install_launchd.sh: install the Flotilla background services on macOS.
#
#   scripts/install_launchd.sh            # core: pocketbase + dispatcher
#   scripts/install_launchd.sh bridge push standup github   # add optional services
#   scripts/install_launchd.sh --uninstall
#
# Templates live next to this script (fleet.*.plist). This fills in the paths of
# this workspace, copies them to ~/Library/LaunchAgents and loads them.
# Note: the dispatcher already runs GitHub sync once per cycle when
# FLOTILLA_GITHUB_REPO is set; install `github` only if you want a separate
# always-on sync process instead (do not run both).
set -euo pipefail
RUNTIME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${FLOTILLA_WORKSPACE:-$(cd "$RUNTIME_DIR/.." && pwd)}"
AGENTS_DIR="$HOME/Library/LaunchAgents"
DOMAIN="gui/$(id -u)"
mkdir -p "$AGENTS_DIR" "$RUNTIME_DIR/logs"

if [ "${1:-}" = "--uninstall" ]; then
  for p in "$RUNTIME_DIR"/fleet.*.plist; do
    label="$(basename "$p" .plist)"
    launchctl bootout "$DOMAIN/$label" 2>/dev/null || true
    rm -f "$AGENTS_DIR/$label.plist"
    echo "removed $label"
  done
  exit 0
fi

services=(pocketbase dispatcher "$@")
for svc in "${services[@]}"; do
  tpl="$RUNTIME_DIR/fleet.$svc.plist"
  [ -f "$tpl" ] || { echo "unknown service: $svc" >&2; exit 1; }
  dest="$AGENTS_DIR/fleet.$svc.plist"
  sed -e "s#__WORKSPACE__#$WORKSPACE_DIR#g" -e "s#__RUNTIME__#$RUNTIME_DIR#g" "$tpl" > "$dest"
  plutil -lint "$dest" >/dev/null
  launchctl bootout "$DOMAIN/fleet.$svc" 2>/dev/null || true
  launchctl bootstrap "$DOMAIN" "$dest"
  echo "loaded fleet.$svc"
done
