#!/usr/bin/env bash
#
# Launch IdeaForge (backend + frontend) and capture EVERYTHING into one
# timestamped log file:  backend/logs/complete.log
#
# The backend writes its structured, timestamped logs (app + uvicorn + HTTP
# access + build orchestrator + Claude summaries + warnings) directly into
# complete.log via app/core/logging_config.py. This script additionally folds
# the frontend (Vite) output into the same file, tagged and timestamped.
#
# Usage:
#   ./run.sh            # start backend + frontend, stream logs to complete.log
#   tail -f backend/logs/complete.log   # watch everything live
#
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$BACKEND_DIR/logs"
LOG_FILE="$LOG_DIR/complete.log"

mkdir -p "$LOG_DIR"

# Prefix each line of a stream with a timestamp + tag, append to the complete
# log, and echo to this terminal.
stamp_to_log() {
  local tag="$1"
  while IFS= read -r line; do
    printf '%s [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$tag" "$line"
  done | tee -a "$LOG_FILE"
}

pids=()
cleanup() {
  echo ""
  echo "Shutting down IdeaForge..."
  for pid in "${pids[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup INT TERM EXIT

echo "================================================================"
echo " IdeaForge — complete log: $LOG_FILE"
echo " Watch live with:  tail -f $LOG_FILE"
echo "================================================================"

# --- Backend ---------------------------------------------------------------
# Backend logs go straight into complete.log via its logging config; its
# console output is shown here for live viewing (not re-appended, to avoid
# duplicate lines in the file).
(
  cd "$BACKEND_DIR" || exit 1
  # shellcheck disable=SC1091
  source .venv/bin/activate
  alembic upgrade head
  exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
pids+=($!)

# --- Frontend --------------------------------------------------------------
# Vite has no built-in file logging, so capture its output into complete.log.
(
  cd "$FRONTEND_DIR" || exit 1
  npm run dev 2>&1 | stamp_to_log frontend
) &
pids+=($!)

wait
