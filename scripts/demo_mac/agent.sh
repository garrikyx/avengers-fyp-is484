#!/usr/bin/env bash
# UBS-134 macOS demo: telemetry agent (tails .demo-run/logs; SIGTERM drains, publishes and checkpoints). Normally started by demo.sh; can be run on its own.
set -euo pipefail
source "$(dirname "$0")/_env.sh"
need_run_folder
set_title "4 agent"
claim_pid agent
cd "$RUN"
exec "$VENV/telemetry-agent" --config "$ROOT/config/demo/agent.yaml"
