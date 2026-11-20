#!/usr/bin/env bash
# Stop API + Web started by bin/start.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/logs"

info() { echo "[dpi] $*"; }

stop_one() {
  local name="$1"
  local pid_file="$PID_DIR/$2.pid"
  if [[ ! -f "$pid_file" ]]; then
    info "$name: not running (no pid file)"
    return
  fi
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -z "${pid:-}" ]]; then
    rm -f "$pid_file"
    info "$name: empty pid file removed"
    return
  fi
  if kill -0 "$pid" 2>/dev/null; then
    # kill process group if possible (npm may spawn children)
    kill "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
    info "$name: stopped (pid $pid)"
  else
    info "$name: process not alive"
  fi
  rm -f "$pid_file"
}

stop_one "backend" "api"
stop_one "frontend" "web"
info "done"
