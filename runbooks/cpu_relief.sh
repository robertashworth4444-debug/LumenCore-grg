#!/usr/bin/env bash
set -euo pipefail
echo "[RUNBOOK] CPU relief invoked for service=$1 pod=$2 ts=$(date -Is)"
# EXAMPLES (uncomment/apply to your world):
# kubectl -n $1 scale deploy/$2 --replicas=2
# renice +10 -p $(pgrep -f "$2") || true
exit 0
