#!/usr/bin/env bash
if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi
set -eu

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/logs"
API_PORT="${DPI_API_PORT:-8000}"
WEB_PORT="${DPI_WEB_PORT:-5173}"

check() {
  local name="$1"
  local pid_file="$PID_DIR/$2.pid"
  if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "$name: running (pid $(cat "$pid_file"))"
  else
    echo "$name: stopped"
  fi
}

check "backend " "api"
check "frontend" "web"

if command -v curl >/dev/null 2>&1; then
  echo -n "api health: "
  curl -fsS "http://127.0.0.1:${API_PORT}/api/health" 2>/dev/null || echo "unreachable"
fi

echo "ui expect: http://127.0.0.1:${WEB_PORT}"
