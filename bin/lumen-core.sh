#!/usr/bin/env bash
set -euo pipefail
echo "[LUMEN-CORE] starting heartbeat loop"
while true; do
  date +"[LUMEN-CORE] alive: %F %T"
  printf "lumencore_tasks_ok 1\n" > /var/lib/node_exporter/textfile/lumencore.prom
  sleep 10
done
