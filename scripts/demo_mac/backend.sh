#!/usr/bin/env bash
# UBS-134 macOS demo: backend on :8080 (+8081 internal). Normally started by demo.sh; can be run on its own.
set -euo pipefail
source "$(dirname "$0")/_env.sh"
set_title "1 backend :8080"
claim_pid backend
cd "$ROOT"
exec "$VENV/telemetry-backend" --config config/demo/backend.yaml
