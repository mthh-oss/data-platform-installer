#!/usr/bin/env bash
# One-click start: API (8000) + Web (5173)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/logs"
PID_DIR="$ROOT_DIR/logs"

mkdir -p "$LOG_DIR"

API_PORT="${DPI_API_PORT:-8000}"
WEB_PORT="${DPI_WEB_PORT:-5173}"
API_HOST="${DPI_API_HOST:-0.0.0.0}"
WEB_HOST="${DPI_WEB_HOST:-0.0.0.0}"

info() { echo "[dpi] $*"; }
warn() { echo "[dpi][warn] $*" >&2; }
die()  { echo "[dpi][error] $*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing command: $1"
}

is_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  [[ -n "${pid:-}" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

start_backend() {
  local pid_file="$PID_DIR/api.pid"
  local log_file="$LOG_DIR/api.log"

  if is_running "$pid_file"; then
    info "backend already running (pid $(cat "$pid_file"))"
    return
  fi

  need_cmd python3
  cd "$BACKEND_DIR"

  if [[ ! -d .venv ]]; then
    info "creating python venv..."
    python3 -m venv .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  info "installing backend deps..."
  pip install -q -r requirements.txt

  info "starting backend on ${API_HOST}:${API_PORT}..."
  nohup .venv/bin/uvicorn app.main:app --host "$API_HOST" --port "$API_PORT" \
    >"$log_file" 2>&1 &
  echo $! >"$pid_file"
  sleep 1
  if is_running "$pid_file"; then
    info "backend started (pid $(cat "$pid_file")), log: $log_file"
  else
    die "backend failed to start, see $log_file"
  fi
}

start_frontend() {
  local pid_file="$PID_DIR/web.pid"
  local log_file="$LOG_DIR/web.log"

  if is_running "$pid_file"; then
    info "frontend already running (pid $(cat "$pid_file"))"
    return
  fi

  need_cmd npm
  cd "$FRONTEND_DIR"

  if [[ ! -d node_modules ]]; then
    info "installing frontend deps (npm install)..."
    npm install
  fi

  info "starting frontend on ${WEB_HOST}:${WEB_PORT}..."
  nohup npm run dev -- --host "$WEB_HOST" --port "$WEB_PORT" \
    >"$log_file" 2>&1 &
  echo $! >"$pid_file"
  sleep 2
  if is_running "$pid_file"; then
    info "frontend started (pid $(cat "$pid_file")), log: $log_file"
  else
    die "frontend failed to start, see $log_file"
  fi
}

check_docker() {
  if command -v docker >/dev/null 2>&1 && docker version >/dev/null 2>&1; then
    info "docker: ok"
  else
    warn "docker not available — control plane can start, but component deploy will fail"
  fi
}

main() {
  info "project root: $ROOT_DIR"
  check_docker
  start_backend
  start_frontend

  echo
  info "ready"
  info "  UI : http://<server-ip>:${WEB_PORT}"
  info "  API: http://<server-ip>:${API_PORT}/api/health"
  info "  stop: $ROOT_DIR/bin/stop.sh"
  info "  logs: $LOG_DIR/"
}

main "$@"
