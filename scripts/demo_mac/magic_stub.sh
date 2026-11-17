#!/usr/bin/env bash
# UBS-134 macOS demo: STUB Magic callback endpoint on :9000 (verifies the HMAC signature). Normally started by demo.sh; can be run on its own.
set -euo pipefail
source "$(dirname "$0")/_env.sh"
set_title "2 Magic callback STUB :9000"
mkdir -p "$RUN"
claim_pid magic_stub
cd "$ROOT"
exec "$PY" -m scripts.mock_magic_callback_receiver --record "$RUN/callbacks.jsonl"
