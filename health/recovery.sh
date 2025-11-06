#!/usr/bin/env bash
set -euo pipefail

echo "[RECOVERY] running remediation steps..."

echo 3 > /proc/sys/vm/drop_caches || true

if mount | grep -q ' / .*ro,'; then
  logger -t recovery "Root FS read-only detected"
fi

systemctl restart node-exporter || true
systemctl restart prometheus || true
systemctl restart grafana-server || true

curl -m 3 -s http://127.0.0.1:8000/healthz >/dev/null || true

echo "[RECOVERY] complete."
