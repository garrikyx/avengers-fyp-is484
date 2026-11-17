#!/usr/bin/env bash
# UBS-134 macOS demo: Microsoft 365 Agents Playground (Teams App Test Tool) on :56150. Normally started by demo.sh; can be run on its own.
set -euo pipefail
source "$(dirname "$0")/_env.sh"
set_title "7 Agents Playground :56150"
claim_pid playground
cd "$ROOT"
# Open the browser once the playground is listening (it does not open one itself).
( wait_port 56150 "Agents Playground" >/dev/null && \
  { command -v open >/dev/null 2>&1 && open "http://localhost:56150" || true; } ) &
exec npx -y @microsoft/teams-app-test-tool start -e http://localhost:3978/api/messages -c msteams
