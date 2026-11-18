#!/usr/bin/env bash
# UBS-134 macOS demo: telemetry agent (tails .demo-run/logs; SIGTERM drains, publishes and checkpoints). Normally started by demo.sh; can be run on its own.
set -euo pipefail
source "$(dirname "$0")/_env.sh"
need_run_folder
set_title "4 agent"
claim_pid agent
cd "$RUN"
# The run folder's copy of config/demo/agent.yaml (demo.sh start runs
# `scripts.demo_showcase prepare`), so `demo.sh reload` never edits the repo.
CONFIG="$RUN/config/agent.yaml"
[ -f "$CONFIG" ] || CONFIG="$ROOT/config/demo/agent.yaml"
exec "$VENV/telemetry-agent" --config "$CONFIG"
