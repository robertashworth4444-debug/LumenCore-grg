#!/usr/bin/env bash
set -euo pipefail

BASE="/opt/lumen-core"
VENV="$BASE/.venv/bin/activate"
LOG="$BASE/logs"
RUN="$BASE/run"
PORT="${PORT:-8080}"

# components (edit names if you change files later)
declare -A APP=(
  [health]="health_server.py"
  [metrics]="metrics_exporter.py"
  [whitehole]="whitehole.py"
  [luma]="luma_core.py"
)

ensure_dirs() { mkdir -p "$LOG" "$RUN"; }
venv() { source "$VENV" 2>/dev/null || { echo "❌ venv missing: $VENV"; exit 1; }; }
pidfile(){ echo "$RUN/$1.pid"; }
is_running(){ [[ -f "$(pidfile "$1")" ]] && kill -0 "$(cat "$(pidfile "$1")")" 2>/dev/null; }

start_one(){
  local name="$1" py="${APP[$1]}"
  [[ -z "$py" ]] && return
  if is_running "$name"; then echo "↺ $name already running (pid=$(cat "$(pidfile "$name")"))"; return; fi
  echo "▶ starting $name ..."
  nohup python3 "$BASE/$py" > "$LOG/${name}.log" 2>&1 &
  echo $! > "$(pidfile "$name")"
}

stop_one(){
  local name="$1"
  if is_running "$name"; then
    echo "■ stopping $name (pid=$(cat "$(pidfile "$name")"))"
    kill "$(cat "$(pidfile "$name")")" || true
    rm -f "$(pidfile "$name")"
  else
    echo "… $name not running"
  fi
}

start_all(){ ensure_dirs; venv; for k in "${!APP[@]}"; do start_one "$k"; done; }
stop_all(){ for k in "${!APP[@]}"; do stop_one "$k"; done; }
status_all(){
  for k in "${!APP[@]}"; do
    if is_running "$k"; then echo "✓ $k (pid=$(cat "$(pidfile "$k")"))"; else echo "× $k (stopped)"; fi
  done
  echo "Port: $PORT"
  echo "URL:  http://$(curl -s ifconfig.me 2>/dev/null || echo YOUR_IP):$PORT"
}
logs(){ local n="${1:-health}"; tail -n 80 -f "$LOG/${n}.log"; }
url(){ echo "http://$(curl -s ifconfig.me 2>/dev/null || echo YOUR_IP):$PORT"; }
open_port_hint(){ echo "If blocked, allow TCP $PORT in your firewall / security group."; }

case "${1:-help}" in
  start)   start_all; status_all; open_port_hint ;;
  stop)    stop_all ;;
  restart) stop_all; sleep 1; start_all; status_all ;;
  status)  status_all ;;
  logs)    shift; logs "${1:-health}" ;;
  url)     url ;;
  *) echo "Usage: $0 {start|stop|restart|status|logs [health|metrics|whitehole|luma]|url}"; exit 1 ;;
esac
