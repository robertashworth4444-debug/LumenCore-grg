#!/usr/bin/env bash
set -euo pipefail
echo "[RUNBOOK] Latency hotfix for service=$1 route=$2 ts=$(date -Is)"
# EXAMPLES:
# kubectl -n $1 rollout undo deploy/$1-api
# curl -s -X POST http://localhost:9002/cache/purge -d "{\"route\":\"$2\"}" || true
exit 0
