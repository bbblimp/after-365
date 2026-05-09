#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK_FILE="$REPO_ROOT/state/daily_run.lock"
LOG_DIR="$REPO_ROOT/logs/raw"
LOG_FILE="$LOG_DIR/$(date +%F).log"
PROMPT_FILE="$REPO_ROOT/prompts/cron-agent.md"

resolve_codex() {
  if [[ -n "${CODEX_BIN:-}" && -x "$CODEX_BIN" ]]; then
    printf '%s\n' "$CODEX_BIN"
    return 0
  fi

  if command -v codex >/dev/null 2>&1; then
    command -v codex
    return 0
  fi

  local candidate
  for candidate in /home/blech/.vscode/extensions/openai.chatgpt-*/bin/linux-x86_64/codex; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

run_python_fallback() {
  echo "$(date -Is) running Python fallback daily_run.py $*"
  python3 scripts/daily_run.py "$@"
}

run_codex_agent() {
  local codex_bin="$1"
  local run_date="$2"
  local prompt_path
  prompt_path="$(mktemp /tmp/after365-cron-prompt.XXXXXX.md)"
  trap 'rm -f "$prompt_path"' RETURN

  {
    printf 'Run date: %s\n\n' "$run_date"
    cat "$PROMPT_FILE"
  } > "$prompt_path"

  echo "$(date -Is) running Codex agent for After 365 date $run_date"
  AFTER365_RUN_DATE="$run_date" "$codex_bin" \
    --search \
    --ask-for-approval never \
    exec \
    --sandbox workspace-write \
    -C "$REPO_ROOT" \
    - < "$prompt_path"
}

list_due_dates() {
  local today="${AFTER365_TODAY:-$(date +%F)}"
  local limit="${AFTER365_CATCHUP_LIMIT:-14}"

  if [[ -n "${AFTER365_RUN_DATE:-}" ]]; then
    printf '%s\n' "$AFTER365_RUN_DATE"
    return 0
  fi

  python3 scripts/list_missing_dates.py --today "$today" --limit "$limit"
}

mkdir -p "$LOG_DIR" "$REPO_ROOT/state"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "$(date -Is) another After 365 run is already active" >> "$LOG_FILE"
  exit 0
fi

cd "$REPO_ROOT"

if [[ "${1:-}" == "--list-missing" ]]; then
  list_due_dates
  exit 0
fi

{
  echo "$(date -Is) starting After 365 daily run"

  if [[ "${1:-}" == "--smoke-agent" ]]; then
    codex_bin="$(resolve_codex)"
    echo "$(date -Is) smoke testing Codex agent at $codex_bin"
    "$codex_bin" --ask-for-approval never exec --sandbox workspace-write -C "$REPO_ROOT" "Reply with READY only. Do not edit files or run tools."
  elif [[ "${1:-}" == "--python-only" ]]; then
    shift
    run_python_fallback "$@"
  else
    if codex_bin="$(resolve_codex)"; then
      mapfile -t due_dates < <(list_due_dates)
      if [[ "${#due_dates[@]}" -eq 0 ]]; then
        echo "$(date -Is) no missing After 365 run dates found"
      fi
      for run_date in "${due_dates[@]}"; do
        run_codex_agent "$codex_bin" "$run_date"
      done
    else
      echo "$(date -Is) Codex CLI not found; falling back to placeholder Python run"
      run_python_fallback "$@"
    fi
  fi

  echo "$(date -Is) finished After 365 daily run"
} >> "$LOG_FILE" 2>&1
