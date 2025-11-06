#!/usr/bin/env bash
case "$0" in
*restart_service*)  systemctl restart "$1"; echo "[RUNBOOK] Restarted service $1";;
*clear_cache*)      sync; echo 3 > /proc/sys/vm/drop_caches; echo "[RUNBOOK] Cleared FS cache";;
*rotate_logs*)      logrotate -f /etc/logrotate.conf; echo "[RUNBOOK] Logs rotated";;
*scale_k8s*)        kubectl -n "$1" scale deploy/"$2" --replicas="$3"; echo "[RUNBOOK] Scaled $2 to $3 replicas in $1";;
esac
