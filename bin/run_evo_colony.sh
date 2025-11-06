#!/usr/bin/env bash
set -euo pipefail
IDX="${1:-1}"                       # colony index from systemd template
APP_DIR="/opt/lumen-core"
ENV_FILE="${APP_DIR}/.env"

# shell env
source "${APP_DIR}/.venv/bin/activate"
[ -f "${ENV_FILE}" ] && set -a && source "${ENV_FILE}" && set +a

OUT="${APP_DIR}/storage/colony-${IDX}"
mkdir -p "${OUT}"

SEED_BASE="${EVO_SEED:-4444}"
SEED=$(( SEED_BASE + IDX ))
SAFE="${SAFE_MODE:-0}"
TPH="${TRIALS_PER_HOUR:-120}"

cd "${APP_DIR}"
if [ -f "evo/runner.py" ]; then
  exec python3 evo/runner.py --safe "${SAFE}" --tph "${TPH}" --out "${OUT}"
else
  echo "evo/runner.py not found" >&2
  exit 2
fi
