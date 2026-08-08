#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="/Users/miguelrodriguez/gguf-env/bin/python"
PORT="${PORT:-8000}"
DEFAULT_MODEL="${DEFAULT_MODEL:-apertus}"
APERTUS_MODEL_ID="${APERTUS_MODEL_ID:-${MODEL_ID:-swiss-ai/Apertus-v1.1-4B-Instruct}}"
MINISTRAL_MODEL_ID="${MINISTRAL_MODEL_ID:-mistralai/Ministral-3-3B-Instruct-2512-BF16}"

echo "Starting Disposition Lens Inference Service..."
echo "Default model: $DEFAULT_MODEL"
echo "Apertus: $APERTUS_MODEL_ID"
echo "Ministral: $MINISTRAL_MODEL_ID"
echo "Port: $PORT"

PORT="$PORT" DEFAULT_MODEL="$DEFAULT_MODEL" APERTUS_MODEL_ID="$APERTUS_MODEL_ID" MINISTRAL_MODEL_ID="$MINISTRAL_MODEL_ID" "$PYTHON_BIN" server.py
