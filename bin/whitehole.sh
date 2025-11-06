#!/usr/bin/env bash
set -euo pipefail
echo "[WHITEHOLE] starting heartbeat loop"
while true; do
  date +"[WHITEHOLE] alive: %F %T"
  # if you later want a separate metric, add it here
  sleep 12
done
