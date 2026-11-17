#!/usr/bin/env bash
# UBS-134 macOS demo: Teams bot on :3978 with dev credentials (as make teams-run). Dev only, never on a deployed bot. Normally started by demo.sh; can be run on its own.
set -euo pipefail
source "$(dirname "$0")/_env.sh"
set_title "5 Teams bot :3978"
export CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=00000000-0000-0000-0000-000000000000
export CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=dummy
export CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=00000000-0000-0000-0000-000000000000
export CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED=true
# UBS-120 alert cards: the Agents Playground is a 1:1 chat.
export TEAMS_NOTIFY_ALLOW_PERSONAL=true
claim_pid teams_bot
cd "$ROOT"
exec "$VENV/telemetry-teams"
