#!/bin/bash
# AgentFleet Kanban Bridge — shell wrapper
# Usage: ./scripts/kanban.sh <command> [args...]
#
# Commands:
#   fetch [--status "In Progress"] [--format json|table]
#   update --ticket N --status "Done"
#   standup [--repo owner/repo] [--days 1] [--agent "Clau"]
#
# Required env vars:
#   GITHUB_TOKEN, KANBAN_ORG, KANBAN_PROJECT_NUMBER

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "[kanban] ERROR: GITHUB_TOKEN not set." >&2
    exit 1
fi
if [ -z "$KANBAN_ORG" ] || [ -z "$KANBAN_PROJECT_NUMBER" ]; then
    echo "[kanban] ERROR: KANBAN_ORG and KANBAN_PROJECT_NUMBER must be set." >&2
    exit 1
fi

CMD=$1
shift

case "$CMD" in
    fetch)
        python3 "$SCRIPT_DIR/kanban_fetch.py" "$@"
        ;;
    update)
        python3 "$SCRIPT_DIR/kanban_update.py" "$@"
        ;;
    standup)
        python3 "$SCRIPT_DIR/kanban_standup.py" "$@"
        ;;
    *)
        echo "Usage: kanban.sh {fetch|update|standup} [options]"
        echo ""
        echo "  fetch    --status 'In Progress' --format table|json"
        echo "  update   --ticket 14 --status Done"
        echo "  standup  --repo owner/repo --days 1 --agent 'Clau' --output standups/today.md"
        exit 1
        ;;
esac
