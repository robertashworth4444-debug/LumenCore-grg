#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/opt/lumen-core"
source "${APP_DIR}/.venv/bin/activate"
cd "${APP_DIR}"
SAFE_MODE="${SAFE_MODE:-1}"
TRIALS_PER_HOUR="${TRIALS_PER_HOUR:-30}"
LOG="${APP_DIR}/logs/evo.log"
if [ -f "evo/runner.py" ]; then
  CMD=(python3 /opt/lumen-core/evo/runner.py --safe "${SAFE_MODE}" --tph "${TRIALS_PER_HOUR}" --out "${APP_DIR}/storage")
else
  echo "evo/runner.py not found"; exit 2
fi
while true; do
  "${CMD[@]}" | tee -a "${LOG}"
  sleep 5
done
