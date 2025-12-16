#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PORT=${PORT:-5001}
PID_FILE=".server.pid"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/server.out"

declare -a EXTRA_ARGS=()

ensure_logs() {
  mkdir -p "$LOG_DIR"
}

kill_port() {
  local pids
  pids=$(lsof -ti tcp:"$PORT" || true)
  if [[ -n "$pids" ]]; then
  echo "Killing processes on port $PORT: $pids"
    kill -TERM $pids || true
    sleep 1
    
    pids=$(lsof -ti tcp:"$PORT" || true)
    if [[ -n "$pids" ]]; then
      kill -KILL $pids || true
    fi
  fi
}

run_foreground() {
  kill_port
  echo "Starting server in foreground on port $PORT"
  if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
    exec uv run cli.py "${EXTRA_ARGS[@]}"
  else
    exec uv run cli.py
  fi
}

start_background() {
  kill_port
  ensure_logs
  echo "Starting server in background on port $PORT"
  if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
    nohup uv run cli.py "${EXTRA_ARGS[@]}" >"$LOG_FILE" 2>&1 &
  else
    nohup uv run cli.py >"$LOG_FILE" 2>&1 &
  fi
  echo $! >"$PID_FILE"
  echo "Server started with PID $(cat "$PID_FILE"). Logs: $LOG_FILE"
}

stop_server() {
  local pid
  if [[ -f "$PID_FILE" ]]; then
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      echo "Stopping server PID $pid"
      kill -TERM "$pid" || true
      sleep 1
      if kill -0 "$pid" 2>/dev/null; then
        kill -KILL "$pid" || true
      fi
      rm -f "$PID_FILE"
      echo "Server stopped"
      return
    else
      rm -f "$PID_FILE"
    fi
  fi
  echo "PID file missing or stale; killing by port $PORT"
  kill_port
}

usage() {
  echo "Usage: $0 {run|start|stop} [args...]"
  echo "  所有 [args...] 直接传递给 cli.py，例如 --port 5002"
  echo "  run   前台运行（启动前清理目标端口进程，默认 5001）"
  echo "  start 后台运行（启动前清理目标端口进程）"
  echo "  stop  停止进程（优先使用PID文件，否则按端口清理；支持 --port）"
}

ARGS=("$@")
subcmd="run"
if ((${#ARGS[@]})); then
  case "${ARGS[0]}" in
    run|start|stop)
      subcmd="${ARGS[0]}"
      EXTRA_ARGS=("${ARGS[@]:1}")
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      EXTRA_ARGS=("${ARGS[@]}")
      ;;
  esac
else
  EXTRA_ARGS=()
fi

for ((i=0; i<${#ARGS[@]}; i++)); do
  arg="${ARGS[i]}"
  if [[ "$arg" == "--port" || "$arg" == "-p" ]]; then
    next="${ARGS[i+1]:-}"
    if [[ -n "$next" ]]; then
      PORT="$next"
    fi
  elif [[ "$arg" == --port=* ]]; then
    PORT="${arg#--port=}"
  fi
done

case "$subcmd" in
  start)
    start_background
    ;;
  stop)
    stop_server
    ;;
  run)
    run_foreground
    ;;
esac
