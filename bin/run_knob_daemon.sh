#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/opt/lumen-core"
source "${APP_DIR}/.venv/bin/activate"
cd "${APP_DIR}"
if [ -f "knob_daemon.py" ]; then
  exec python3 knob_daemon.py --live "${APP_DIR}/knobs/live.json"
elif [ -f "knob_daemon.py" ]; then
  exec python3 knob_daemon.py --live "${APP_DIR}/knobs/live.json"
else
  echo "knob_daemon.py not found"; exit 2
fi
