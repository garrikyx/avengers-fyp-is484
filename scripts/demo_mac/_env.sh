# UBS-134 macOS demo: shared settings and helpers. Sourced, not run.
#
# Bash 3.2 compatible (the macOS default /bin/bash): no associative arrays,
# no ${var,,}, no mapfile. Same entrypoints, config/demo/* and dev-only values
# as scripts/demo_windows.bat and scripts/demo.py. Local hosting only.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN="$ROOT/.demo-run"
PIDS="$RUN/pids"
PROC="$RUN/proc"
BACKEND="http://127.0.0.1:8080"

# .venv/bin on macOS/Linux; .venv/Scripts when smoke-testing under Git Bash.
if [ -d "$ROOT/.venv/bin" ]; then VENV="$ROOT/.venv/bin"; else VENV="$ROOT/.venv/Scripts"; fi
PY="$VENV/python"

# Simulator settings (same as the bat). Saved in the run folder so every
# restart (burst, app-fault, logs-start, ...) keeps the other setting.
NORMAL_RATE=0.005
BURST_RATE=0.6
FAULT_RATE=0.05

# Dev-only values, the same fallbacks as .env.example and scripts/demo.py.
export MAGIC_TELEMETRY_ID_HASH_KEY="dev-only"
export MAGIC_TELEMETRY_PUBLISH_TOKEN="dev-local-token"
export MAGIC_TELEMETRY_CALLBACK_SECRET="dev-local-secret"
export TELEMETRY_BACKEND_URL="$BACKEND"
# UBS-120 alert cards: demo.sh start writes one random secret per run to
# $RUN/notify-token. Every component script reads it from there, because a new
# Terminal.app window does not inherit this shell's environment.
if [ -z "${MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN:-}" ] && [ -f "$RUN/notify-token" ]; then
  MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN="$(cat "$RUN/notify-token")"
fi
export MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN="${MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN:-}"
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8

DEMO_PORTS="8080 8081 9000 3978 8765"

say() { printf '%s\n' "$*"; }

# Window/pane title for the component running in this terminal.
set_title() { printf '\033]0;FYP demo: %s\007' "$1"; }

# Record this shell's PID, then `exec` the component so the PID stays the same.
claim_pid() {
  mkdir -p "$PIDS"
  echo "$$" >"$PIDS/$1.pid"
}

need_run_folder() {
  if [ ! -d "$RUN/logs" ]; then
    say "No run folder; run scripts/demo_mac/demo.sh start first."
    exit 1
  fi
}

port_listening() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    # Git Bash smoke tests: no lsof, use Windows netstat.
    netstat -an 2>/dev/null | grep -E "[:.]$1 .*LISTEN" >/dev/null
  fi
}

wait_http() { # url label
  local i=0
  while [ "$i" -lt 60 ]; do
    if curl -sf "$1" >/dev/null 2>&1; then say "  $2 is up"; return 0; fi
    sleep 1; i=$((i + 1))
  done
  say "  $2 did not come up in 60 s; check its window or $PROC/."
  return 1
}

wait_port() { # port label
  local i=0
  while [ "$i" -lt 60 ]; do
    if port_listening "$1"; then say "  $2 is listening on :$1"; return 0; fi
    sleep 1; i=$((i + 1))
  done
  say "  $2 did not listen on :$1 in 60 s; check its window or $PROC/."
  return 1
}

is_running() { # name
  local pid
  [ -f "$PIDS/$1.pid" ] || return 1
  pid="$(cat "$PIDS/$1.pid")"
  kill -0 "$pid" 2>/dev/null
}

# SIGTERM (the agent drains, publishes and checkpoints), then SIGKILL after 10 s.
stop_component() { # name
  local pid i
  [ -f "$PIDS/$1.pid" ] || return 0
  pid="$(cat "$PIDS/$1.pid")"
  if kill -0 "$pid" 2>/dev/null; then
    pkill -TERM -P "$pid" 2>/dev/null || true
    kill -TERM "$pid" 2>/dev/null || true
    i=0
    while kill -0 "$pid" 2>/dev/null && [ "$i" -lt 10 ]; do sleep 1; i=$((i + 1)); done
    if kill -0 "$pid" 2>/dev/null; then
      pkill -KILL -P "$pid" 2>/dev/null || true
      kill -KILL "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$PIDS/$1.pid"
}

load_sim() {
  RATE="$NORMAL_RATE"
  FAULTS=0
  [ -f "$RUN/sim-rate.txt" ] && RATE="$(cat "$RUN/sim-rate.txt")"
  [ -f "$RUN/sim-faults.txt" ] && FAULTS="$(cat "$RUN/sim-faults.txt")"
  return 0
}

save_sim() { # rate faults
  echo "$1" >"$RUN/sim-rate.txt"
  echo "$2" >"$RUN/sim-faults.txt"
}
