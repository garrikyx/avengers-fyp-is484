#!/usr/bin/env bash
# UBS-134: macOS demo launcher and storyline. The macOS version of
# scripts/demo_windows.bat, with the same commands plus `run`.
#
#   scripts/demo_mac/demo.sh              start everything (default)
#   scripts/demo_mac/demo.sh run [--auto] start, then play the whole storyline
#                                         (guided: press Enter; --auto: timed waits)
#   scripts/demo_mac/demo.sh alerts       table of every alert so far
#   scripts/demo_mac/demo.sh burst        60% rejects: HighRejectRate, RejectSpike, Abnormal*
#   scripts/demo_mac/demo.sh normal       back to 0.5% rejects: those alerts resolve
#   scripts/demo_mac/demo.sh app-fault    OutOfMemoryError lines: AppOutOfMemory, AppLogFailure
#   scripts/demo_mac/demo.sh app-normal   no more fault lines: those alerts resolve
#   scripts/demo_mac/demo.sh logs-stop    stop the log generator: NoLogActivity
#   scripts/demo_mac/demo.sh logs-start   restart it with the same settings
#   scripts/demo_mac/demo.sh agent-stop   stop the agent: AgentHeartbeatMissing
#   scripts/demo_mac/demo.sh agent-start  start the agent again (resumes from saved offsets)
#   scripts/demo_mac/demo.sh ask "..."    ask the NL API a question and print the answer
#   scripts/demo_mac/demo.sh stop         stop every demo component
#
# Where each component shows up:
#   default          one titled Terminal.app window per component (osascript)
#   DEMO_TMUX=1      one tmux session "fypdemo", one window per component
#   DEMO_HEADLESS=1  background processes, logs in .demo-run/proc/<name>.log
# DEMO_SKIP_PLAYGROUND=1 skips the Agents Playground (e.g. when showing Copilot only).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/_env.sh"

HEADLINE="Why are Magic orders rejecting in the last 30 minutes?"

# --- launching ---------------------------------------------------------------

view_mode() {
  if [ -n "${DEMO_HEADLESS:-}" ]; then echo headless
  elif [ -n "${DEMO_TMUX:-}" ]; then echo tmux
  elif command -v osascript >/dev/null 2>&1; then echo terminal
  else echo headless
  fi
}

launch() { # name (script is <name>.sh) [args...]
  local name="$1"; shift
  local cmd="cd '$ROOT' && '$HERE/$name.sh'"
  local arg
  for arg in "$@"; do cmd="$cmd '$arg'"; done
  mkdir -p "$PROC"
  case "$(view_mode)" in
    terminal)
      osascript -e "tell application \"Terminal\" to do script \"$cmd\"" >/dev/null
      ;;
    tmux)
      if tmux has-session -t fypdemo 2>/dev/null; then
        tmux new-window -t fypdemo -n "$name" "$cmd; exec bash"
      else
        tmux new-session -d -s fypdemo -n "$name" "$cmd; exec bash"
      fi
      ;;
    headless)
      nohup "$HERE/$name.sh" "$@" >"$PROC/$name.log" 2>&1 &
      ;;
  esac
}

# --- commands ----------------------------------------------------------------

preflight() {
  say "=== Preflight ==="
  (cd "$ROOT" && uv sync --all-packages) || { say "uv sync failed"; exit 1; }
  local busy="" p
  for p in $DEMO_PORTS; do port_listening "$p" && busy="$busy $p"; done
  if [ -n "$busy" ]; then
    say "Ports already in use:$busy"
    say "Run \"scripts/demo_mac/demo.sh stop\" or close the old windows first."
    exit 1
  fi
  local models
  if models="$(curl -sf -m 2 http://127.0.0.1:11434/api/tags 2>/dev/null)"; then
    if printf '%s' "$models" | grep -q '"name":"llama3.2[:"]'; then
      if printf '%s' "$models" | grep -q '"name":"llama3.2"\|"name":"llama3.2:latest"'; then
        say "Ollama: llama3.2 available"
      else
        say "WARNING: config/demo/backend.yaml asks Ollama for llama3.2, but only a tagged"
        say "         variant is pulled. Fix with: ollama cp llama3.2:3b llama3.2"
      fi
    else
      say "WARNING: Ollama has no llama3.2. Run: ollama pull llama3.2"
      say "         Free-form questions get the fallback reply; rule-matched ones still answer."
    fi
  else
    say "Ollama not running: rule-matched questions (the headline question) still answer."
  fi
  if [ -z "${DEMO_SKIP_PLAYGROUND:-}" ] && ! command -v npx >/dev/null 2>&1; then
    say "WARNING: npx not found (brew install node); the Agents Playground will not start."
  fi
  if [ "$(view_mode)" = tmux ] && ! command -v tmux >/dev/null 2>&1; then
    say "DEMO_TMUX is set but tmux is not installed (brew install tmux)."; exit 1
  fi
}

cmd_start() {
  preflight
  local token="${MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN:-}"
  rm -rf "$RUN"
  mkdir -p "$RUN/logs" "$PIDS" "$PROC"
  save_sim "$NORMAL_RATE" 0
  # UBS-120: one random secret per run for the backend and the bot (no dev fallback).
  [ -n "$token" ] || token="$("$PY" -c 'import secrets; print(secrets.token_hex(24))')"
  (umask 077 && printf '%s\n' "$token" >"$RUN/notify-token")
  export MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN="$token"
  say "Fresh run folder: $RUN (view: $(view_mode))"

  say "=== 1. Backend :8080 ==="
  launch backend
  wait_http "$BACKEND/healthz" "backend /healthz"

  say "=== 2. Magic callback STUB :9000 ==="
  launch magic_stub
  wait_port 9000 "Magic stub"

  say "=== 3. Simulator (log generator) ==="
  launch simulator

  say "=== 4. Agent ==="
  launch agent

  say "=== 5. Teams bot :3978 ==="
  launch teams_bot
  wait_port 3978 "Teams bot"

  say "=== 6. MCP server for Copilot :8765 ==="
  launch mcp
  wait_port 8765 "MCP server"

  say "=== 7. Agents Playground ==="
  if [ -n "${DEMO_SKIP_PLAYGROUND:-}" ]; then
    say "  skipped: DEMO_SKIP_PLAYGROUND is set"
  else
    launch playground
    say "  opens http://localhost:56150 once it is listening"
  fi

  say ""
  say "All components started. Say \"hi\" in the Agents Playground first, so the bot"
  say "remembers the chat for alert cards (UBS-120). Then ask: \"$HEADLINE\""
  say "Copilot / MCP Inspector: http://127.0.0.1:8765/mcp"
  say "Let normal trading run for 3+ minutes before \"burst\": the anomaly rules"
  say "(AbnormalRejectRate, AbnormalExecutionIssueRate) need that baseline."
  if [ "$(view_mode)" = tmux ]; then say "Attach with: tmux attach -t fypdemo"; fi
}

restart_simulator() { # new-rate|"" new-faults|""
  need_run_folder
  load_sim
  [ -n "$1" ] && RATE="$1"
  [ -n "$2" ] && FAULTS="$2"
  save_sim "$RATE" "$FAULTS"
  stop_component simulator
  launch simulator
  say "Simulator restarted: reject rate $RATE, app faults $FAULTS."
}

cmd_alerts() {
  local body
  if ! body="$(curl -sf -m 5 "$BACKEND/telemetry/alerts?status=all&limit=50")"; then
    say "Backend not reachable on $BACKEND."; return 1
  fi
  printf '%s' "$body" | "$PY" -c '
import json, sys
from datetime import datetime
r = json.load(sys.stdin)
def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone().strftime("%H:%M:%S") if s else ""
rows = r.get("alerts") or []
if not rows:
    print("No alerts yet.")
else:
    fmt = "{:<28} {:<9} {:<9} {:>12} {:>9} {:>9} {:>9}"
    print(fmt.format("rule", "severity", "status", "observed", "threshold", "first", "resolved"))
    for a in rows:
        obs = a.get("observedValue")
        print(fmt.format(a.get("ruleName", "")[:28], a.get("severity", ""), a.get("status", ""),
                         "" if obs is None else f"{obs:.4g}", str(a.get("threshold", "")),
                         t(a.get("firstObservedUtc")), t(a.get("resolvedAtUtc"))))
c = r.get("counts") or {}
print("Active: %s  (critical %s, warning %s)" % (c.get("active", 0), c.get("critical", 0), c.get("warning", 0)))
'
}

cmd_ask() { # question
  local q="${1:-$HEADLINE}"
  say "Q: $q"
  curl -sf -m 30 -X POST "$BACKEND/telemetry/nl/query" -H 'content-type: application/json' \
    -d "$("$PY" -c 'import json,sys; print(json.dumps({"question": sys.argv[1]}))' "$q")" \
    | "$PY" -c 'import json,sys; r=json.load(sys.stdin); print("A:", r.get("answer") or r.get("reply") or r); print("   (source:", r.get("source"), ")")' \
    || say "  NL query failed; is the backend up?"
}

cmd_stop() {
  local n
  for n in playground mcp teams_bot agent simulator magic_stub backend; do stop_component "$n"; done
  if command -v tmux >/dev/null 2>&1; then tmux kill-session -t fypdemo 2>/dev/null || true; fi
  say "All demo components stopped."
}

# --- storyline (demo.sh run) -------------------------------------------------

AUTO=""
step() { # title
  say ""
  say "=================================================================="
  say "  $1"
  say "=================================================================="
}

pause() { # seconds-in-auto-mode message
  if [ -n "$AUTO" ]; then
    say "  ... waiting $1 s ($2)"
    sleep "$1"
  else
    printf '  %s  [press Enter] ' "$2"
    read -r _ </dev/tty
  fi
}

orders_flowing() {
  curl -sf -m 5 -X POST "$BACKEND/telemetry/query/metrics" -H 'content-type: application/json' \
    -d '{"timeRange":{"last":"1m"},"metrics":["orders_submitted"]}' \
    | "$PY" -c 'import json,sys; r=json.load(sys.stdin); sys.exit(0 if (r.get("totals") or {}).get("orders_submitted") else 1)'
}

cmd_run() {
  [ "${1:-}" = "--auto" ] && AUTO=1
  step "1/8  Start the stack"
  cmd_start
  local i=0
  until orders_flowing; do
    i=$((i + 1)); [ "$i" -gt 60 ] && { say "No orders after 60 s; check the agent and simulator."; exit 1; }
    sleep 1
  done
  say "  Orders are flowing into the backend."

  step "2/8  Normal trading (builds the 3-minute anomaly baseline)"
  cmd_ask "$HEADLINE"
  pause 180 "Show the playground and the metrics while the baseline builds"

  step "3/8  Reject burst"
  restart_simulator "$BURST_RATE" ""
  pause 45 "HighRejectRate, RejectSpike and the Abnormal* rules fire"
  cmd_alerts
  cmd_ask "Any alerts open for Magic?"

  step "4/8  Back to normal: the reject alerts resolve"
  restart_simulator "$NORMAL_RATE" ""
  pause 90 "The burst ages out of the 1-minute window"
  cmd_alerts

  step "5/8  Application faults (Application.log [F] lines)"
  restart_simulator "" "$FAULT_RATE"
  pause 20 "AppOutOfMemory and AppLogFailure fire"
  cmd_alerts
  restart_simulator "" 0

  step "6/8  Log generator stops: NoLogActivity"
  stop_component simulator
  pause 75 "A full minute with no new lines"
  cmd_alerts
  launch simulator

  step "7/8  Agent stops: AgentHeartbeatMissing"
  stop_component agent
  pause 35 "The backend notices the missing heartbeat"
  cmd_alerts
  launch agent
  say "  Agent restarted from its saved offsets."

  step "8/8  Summary"
  pause 30 "Everything resolves"
  cmd_alerts
  say ""
  say "Storyline complete. The stack is still running; stop it with: scripts/demo_mac/demo.sh stop"
}

# --- dispatch ----------------------------------------------------------------

CMD="${1:-start}"
[ "$#" -gt 0 ] && shift
case "$CMD" in
  start) cmd_start ;;
  run) cmd_run "$@" ;;
  stop) cmd_stop ;;
  alerts) cmd_alerts ;;
  ask) cmd_ask "$@" ;;
  burst) restart_simulator "$BURST_RATE" ""; say "Expect HighRejectRate and RejectSpike in ~15 s, the Abnormal* rules in ~15-30 s (after a 3 min baseline)." ;;
  normal) restart_simulator "$NORMAL_RATE" ""; say "Expect the reject alerts to step down and resolve in ~1-2 min." ;;
  app-fault) restart_simulator "" "$FAULT_RATE"; say "Expect AppOutOfMemory and AppLogFailure within a few seconds." ;;
  app-normal) restart_simulator "" 0; say "Expect AppOutOfMemory and AppLogFailure to resolve once the 1 min window clears." ;;
  logs-stop) stop_component simulator; say "Log generator stopped. NoLogActivity should fire once a full minute has no new lines." ;;
  logs-start) need_run_folder; if is_running simulator; then say "Log generator is already running."; else launch simulator; say "Log generator restarted. NoLogActivity resolves once lines arrive again."; fi ;;
  agent-stop) stop_component agent; say "Agent stopped. AgentHeartbeatMissing should fire in about 20-30 s." ;;
  agent-start) need_run_folder; if is_running agent; then say "Agent is already running."; else launch agent; say "Agent started again from its saved offsets."; fi ;;
  *)
    say "Unknown command \"$CMD\"."
    say "Use: start, run, alerts, ask, burst, normal, app-fault, app-normal, logs-stop, logs-start, agent-stop, agent-start, stop."
    exit 2
    ;;
esac
