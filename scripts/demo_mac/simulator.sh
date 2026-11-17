#!/usr/bin/env bash
# UBS-134 macOS demo: log generator (Fix.log + Application.log). Usage: simulator.sh [reject-rate] [app-fault-rate]. Normally started by demo.sh; can be run on its own.
set -euo pipefail
source "$(dirname "$0")/_env.sh"
need_run_folder
load_sim
RATE="${1:-$RATE}"
FAULTS="${2:-$FAULTS}"
save_sim "$RATE" "$FAULTS"
set_title "3 simulator (rejects $RATE, faults $FAULTS)"
claim_pid simulator
cd "$RUN"
exec "$PY" "$ROOT/apps/simulator/src/simulator/mock_logger.py" \
  --interval 0.05 --max-bytes 100000 --reject-rate "$RATE" --app-faults "$FAULTS"
