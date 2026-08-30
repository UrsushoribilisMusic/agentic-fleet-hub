#!/usr/bin/env bash
# Deploy CE-09 w=0 discriminant seeds to the live disposition server.
# Backs up the current seeds, swaps in the CE-09 vectors, restarts the server, verifies.
# Reversible: run with `--rollback` to restore the pre-CE-09 seeds and restart.
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS=(apertus ministral qwen)
PORT="${PORT:-8000}"

restart_server() {
  echo "-- stopping current server on :$PORT"
  PIDS="$(lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null || true)"
  [ -n "$PIDS" ] && kill $PIDS && echo "   killed: $PIDS" || echo "   (none listening)"
  for i in $(seq 1 10); do lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1 && sleep 1 || break; done
  echo "-- relaunching via run_server.sh (loads default model; ~1 min)"
  nohup bash run_server.sh > server_ce09_deploy.log 2>&1 &
  echo "   launched pid $!  (log: server_ce09_deploy.log)"
  echo "-- waiting for /health ..."
  for i in $(seq 1 60); do
    if curl -sf --max-time 3 "http://localhost:$PORT/health" >/dev/null 2>&1; then
      curl -s "http://localhost:$PORT/health" | python3 -c "import sys,json;d=json.load(sys.stdin);print('   HEALTHY — active_model:',d.get('active_model'))"
      return 0
    fi
    sleep 3
  done
  echo "   !! server did not become healthy in 180s — check server_ce09_deploy.log"
  return 1
}

if [ "${1:-}" = "--rollback" ]; then
  echo "== ROLLBACK: restoring pre-CE-09 seeds =="
  for m in "${MODELS[@]}"; do
    cp -v "seed_vectors_${m}_3q4.npz.bak-preCE09" "seed_vectors_${m}_3q4.npz"
  done
  restart_server
  echo "== rollback complete =="
  exit 0
fi

echo "== DEPLOY CE-09 w=0 discriminant seeds =="
for m in "${MODELS[@]}"; do
  [ -f "seed_vectors_${m}_ce09.npz" ] || { echo "missing seed_vectors_${m}_ce09.npz — run eval/ce09_save_w0.py first"; exit 1; }
  [ -f "seed_vectors_${m}_3q4.npz.bak-preCE09" ] || cp -v "seed_vectors_${m}_3q4.npz" "seed_vectors_${m}_3q4.npz.bak-preCE09"
  cp -v "seed_vectors_${m}_ce09.npz" "seed_vectors_${m}_3q4.npz"
done
restart_server
echo "== deploy complete (rollback: bash deploy_ce09_seeds.sh --rollback) =="
