#!/usr/bin/env bash
# UBS-134 macOS demo: MCP server for Copilot on :8765. Normally started by demo.sh; can be run on its own.
set -euo pipefail
source "$(dirname "$0")/_env.sh"
set_title "6 MCP server (Copilot) :8765"
claim_pid mcp
cd "$ROOT"
exec "$VENV/telemetry-mcp"
