#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK_FILE="$REPO_ROOT/state/daily_run.lock"
LOG_DIR="$REPO_ROOT/logs/raw"
LOG_FILE="$LOG_DIR/$(date +%F).log"

mkdir -p "$LOG_DIR" "$REPO_ROOT/state"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "$(date -Is) another After 365 run is already active" >> "$LOG_FILE"
  exit 0
fi

cd "$REPO_ROOT"
{
  echo "$(date -Is) starting After 365 daily run"
  python3 scripts/daily_run.py "$@"
  echo "$(date -Is) finished After 365 daily run"
} >> "$LOG_FILE" 2>&1
