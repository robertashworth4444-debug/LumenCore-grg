#!/usr/bin/env bash
set -euo pipefail
NATS_URL="nats://whitehole:lumenpower@127.0.0.1:4222"
# Pull 100 incident messages and republish to events if desired
nats --server "$NATS_URL" consumer next WH_INCIDENTS WHI_DURABLE --count=100 --raw | while read -r line; do
  echo "INCIDENT>> $line"
done
