#!/bin/bash
# run_with_secrets.sh: start an engine script with secrets injected from Infisical.
#
#   scripts/run_with_secrets.sh dispatcher.py [args...]
#
# If FLOTILLA_INFISICAL_PROJECT_ID is set (in your shell or in scripts/flotilla.env),
# the script runs under `infisical run`, so TELEGRAM_TOKEN and other secrets reach
# it as environment variables and never touch disk. Without it, the script runs
# with the current environment.
set -euo pipefail
RUNTIME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$RUNTIME_DIR/flotilla.env" ] && set -a && . "$RUNTIME_DIR/flotilla.env" && set +a
mkdir -p "$RUNTIME_DIR/logs"

SCRIPT="$1"; shift
PYTHON="${FLOTILLA_PYTHON:-}"
if [ -z "$PYTHON" ]; then
  if [ -x "$RUNTIME_DIR/.venv/bin/python3" ]; then PYTHON="$RUNTIME_DIR/.venv/bin/python3"; else PYTHON="$(command -v python3)"; fi
fi

if [ -n "${FLOTILLA_INFISICAL_PROJECT_ID:-}" ]; then
  exec infisical run \
    --projectId "$FLOTILLA_INFISICAL_PROJECT_ID" \
    --env "${INFISICAL_ENV:-dev}" \
    ${INFISICAL_API_URL:+--domain "$INFISICAL_API_URL"} \
    -- "$PYTHON" "$RUNTIME_DIR/$SCRIPT" "$@"
fi
exec "$PYTHON" "$RUNTIME_DIR/$SCRIPT" "$@"
