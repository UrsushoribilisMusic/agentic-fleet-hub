#!/bin/bash
# Serve the Disposition Lens prototype locally.
# Run from any directory — finds its own path.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8765}"
echo "Serving prototype at http://localhost:${PORT}/"
echo "Open that URL in Chrome, hit '▶ Demo reel', then record."
echo "Ctrl-C to stop."
python3 -m http.server "$PORT" --directory "$DIR"
