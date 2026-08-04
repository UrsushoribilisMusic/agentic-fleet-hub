#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="/Users/miguelrodriguez/gguf-env/bin/python"
PORT="${PORT:-8000}"
MODEL_ID="${MODEL_ID:-swiss-ai/Apertus-v1.1-4B-Instruct}"

echo "Starting Disposition Lens Inference Service..."
echo "Model: $MODEL_ID"
echo "Port: $PORT"

PORT=$PORT MODEL_ID=$MODEL_ID "$PYTHON_BIN" server.py
