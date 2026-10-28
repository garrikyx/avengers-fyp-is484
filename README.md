# UBS Telemetry System for Magic Application

SMU FinTech capstone project

The repo contains five main applications:

```text
apps/
├── agent/       # Runs on each Magic log host; supports multiple instances
├── backend/     # Central telemetry API/service
├── teams/       # Microsoft Teams integration
├── mcp/         # Read-only MCP server for Microsoft 365 Copilot
└── simulator/   # Generates synthetic Magic/FIX logs for testing
```

Shared code lives in:

```text
packages/
└── telemetry_shared/
```

## Architecture

```text
Magic / Simulator
      ↓
Telemetry Agent
      ↓
Telemetry Backend ←── Ollama (local LLM, NL fallback only)
 (bounded in-memory stores)
      ↓
Microsoft Teams / Copilot (MCP)

Day 2:
Telemetry Backend → approved historical store (technology TBD)
```

Default to one Telemetry Agent per Magic host, with per-file-set instance IDs. Multiple
agents send structured telemetry to the central backend.

Day 1 deploys on a local server and uses bounded, process-local in-memory stores (6h
default, 24h maximum); no telemetry database or Redis dependency is required
([ADR 0005](docs/adr/0005-in-memory-metric-store.md)). Day 2 adds approved historical
storage; its technology and retention are not yet selected. Day-2 cloud uploads require
client-information masking in derived telemetry; raw logs/full FIX payloads remain
prohibited.

The POC uses simulator formats, mock Magic callbacks, and real queries plus
firing/resolved notifications in one team-controlled Teams chat. Custom backend
authentication is outside POC acceptance; platform credentials and message validation
required to connect Teams/Copilot still apply. Historical/end-of-day reporting and
central config distribution are Day-2. See
[the reconciled decisions](docs/plan/open-questions.md) for POC scope and remaining
production inputs. These are acceptance targets, not a claim that all integration
features are implemented.

Raw Magic logs and full FIX payloads must not be persisted.

---

## Where should I work?

### Telemetry Agent

```text
apps/agent/src/telemetry_agent/
```

Feature folders will include:

```text
logs/          # Log monitoring, offsets, rotation (M1)
pipeline/      # Bounded queues + parser worker pool (M1.5)
parser/        # FIX parsing / future binary parsing (M2)
metrics/       # Rolling metrics and aggregation
rules/         # Day-1 threshold alerts
callbacks/     # Callback delivery
health/        # Agent heartbeat and health
publishing/    # Sending telemetry to backend
```

If your Jira story relates to processing Magic logs, you are probably working here.

---

### Telemetry Backend

```text
apps/backend/src/telemetry_backend/
```

Main areas:

```text
api/           # FastAPI endpoints
services/      # Business logic
repositories/  # Store abstractions
anomaly/       # Day-2 anomaly detection
persistence/   # Day-2 historical storage (technology TBD)
```

Backend flow should generally be:

```text
API → Service / Repository → bounded in-memory store (Day 1)
```

Keep storage access behind service/repository abstractions.

---

### Microsoft Teams

```text
apps/teams/src/teams_agent/
```

Used for:

- sending alerts to Teams
- receiving user questions
- calling backend APIs
- formatting responses

Teams communicates through backend APIs; it does not access telemetry stores directly.

---

### Magic Simulator

```text
apps/simulator/src/magic_simulator/
```

Used to generate synthetic FIX/log activity for development because we do not have
access to the real UBS production Magic environment.

---

## Shared Schemas

Before creating your own request/event dictionaries, check:

```text
packages/telemetry_shared/
```

Shared models should be defined here and reused across applications.

Examples:

```text
TelemetryEvent
MetricSnapshot
AlertEvent
AgentHeartbeat
```

If your feature requires a new field or event type:

1. Check whether a shared schema already exists.
2. Update the shared model if needed.
3. Inform the team if the change affects another component.
4. Add/update tests.

Do not independently create different versions of the same telemetry object inside
Agent, Backend and Teams.

---

## Python Folder Structure

We use Python's `src` layout.

Example:

```text
apps/agent/
└── src/
    └── telemetry_agent/
        ├── __init__.py
        └── main.py
```

- `apps/agent` = deployable application
- `src` = source-code directory
- `telemetry_agent` = actual Python package
- `__init__.py` = marks the package
- `main.py` = application entry point

Imports should look like:

```python
from telemetry_agent.parser.fix import FixParser
```

not:

```python
from src.telemetry_agent.parsers.fix import FixParser
```

---

## Before Starting Your Jira Story

1. Pull the latest branch.
2. Read `CLAUDE.md`.
3. Identify which application/folder owns your feature.
4. Check `telemetry_shared` before defining new schemas.
5. Reuse existing abstractions instead of creating duplicate implementations.
6. Create/update tests for your acceptance criteria.
7. Do not add unrelated dependencies or refactor unrelated features.
8. Do not persist raw logs or full FIX messages.
9. Keep thresholds/config values configurable rather than hard-coded.
10. Run tests/linting before creating your PR.

---

## Local Tools

Current stack:

```text
Python 3.14+
FastAPI
Pydantic
Bounded in-memory telemetry stores (Day 1)
Historical storage (Day 2; technology TBD)
pytest
Ruff
mypy
Docker / Docker Compose
```

See [Prerequisites](#prerequisites) for what to install, and the `Makefile` for the
common commands.

---

## Important Design Rules

- Agent must remain lightweight.
- Target Agent resource usage: **<2% CPU and <500 MB memory**.
- Backend supports horizontal scaling; Day-1 replica state is process-local and queries
  must preserve completeness.
- Day-1 telemetry state uses bounded in-memory stores (ADR 0005).
- Historical Day-2 data belongs behind storage abstractions; retention and technology
  remain undecided.
- Raw logs/full FIX payloads must not be persisted or transmitted; publish only
  allowlisted derived/sanitised telemetry.
- Teams only communicates through Backend APIs.
- Day-1 rules use configured thresholds.
- Day-2 anomaly detection compares current behaviour against historical/rolling
  baselines.

If you are unsure where your feature belongs, check the folder responsibilities above
before creating new modules.

## Prerequisites

Install these before running anything:

| Tool | Version | Why | Install |
| --- | --- | --- | --- |
| [uv](https://docs.astral.sh/uv/) | latest | Python 3.14 and every package in the workspace | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [Ollama](https://ollama.com/download) | 0.5 or later | Local LLM for natural-language questions the rule matcher can't parse (spec 008) | macOS: `brew install ollama` or the app; Windows: the installer; Linux: `curl -fsSL https://ollama.com/install.sh \| sh` |
| `llama3.2` model | | The model `config/backend.yaml` uses (about 2 GB) | `make ollama-setup` (or `ollama pull llama3.2`) |
| Node.js | 20 or later | Only for the Teams Agents Playground and the MCP Inspector (`npx`) | [nodejs.org](https://nodejs.org) |
| `make`, `curl` | | Shortcuts and checks below | Preinstalled on macOS/Linux; on Windows, run the commands from the `Makefile` directly |

Then make sure Ollama is running (open the Ollama app, or run `ollama serve`) and check:

```bash
make ollama-check        # "Ollama OK: llama3.2 at http://127.0.0.1:11434"
```

`make backend-run` runs this check first and stops with a fix-it message if Ollama is
missing, not running or the model isn't pulled. To use another model, pull it, set
`nl.llm.model` in `config/backend.yaml`, and pass `OLLAMA_MODEL=<name>` to `make`.

Ollama is only a fallback. Rule-matched questions and small talk never reach it, and if
it is slow or down the backend still answers (keyword match or a short reply) instead of
timing out. To run with no LLM at all, set `nl.llm.provider: mock` in
`config/backend.yaml` and skip `ollama-check` by running
`uv run telemetry-backend --config config/backend.yaml`.

## Quick start

```bash
# Install uv (if not present)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Pull the local LLM (once) and check Ollama is running
make ollama-setup
make ollama-check

# Create virtual environment
uv venv

# Activate virtual environment for MACBOOK
source .venv/bin/activate

# Sync workspace
uv sync

# Run tests
uv run pytest

# Parser tests
make parser-test

export MAGIC_TELEMETRY_ID_HASH_KEY=dev-only
make parser-demo

# Lint
make lint
```

Or without Make:

```bash
export MAGIC_TELEMETRY_ID_HASH_KEY=dev-only
uv run pytest tests/unit/agent/parser/ -v
uv run python -m telemetry_agent.parser.cli \
  --corpus apps/agent/testdata/fix/demo_logs.txt \
  --corpus apps/agent/testdata/magic/ \
  --config apps/agent/testdata/magic/demo_config.yaml
```

---

## Run the full stack locally (agent + backend + health monitor)

> **Tentative** — local development only. `config/agent.yaml` points at localhost over
> plain http; the production deployment of the agent is not set up yet.

`telemetry-agent` is the real agent (UBS-114): one process that tails the logs, parses
them, updates metrics and agent health, evaluates the rules and publishes alerts +
heartbeats to the backend (and signed callbacks to Magic). It replaces the old
`telemetry-agent-heartbeat` and `scripts/health_monitor_demo.py` demos.

Complete [Prerequisites](#prerequisites) first (Ollama running, model pulled). Then, in
separate terminals from the repo root:

```bash
uv sync --all-packages   # once

make backend-run         # 1. backend: :8080 public, :8081 internal; checks Ollama first
make simulator-run       # 2. writes ./logs/Application.log + Fix.log
make agent-run           # 3. the agent
# 4. optional: anything listening on 127.0.0.1:9000 receives the Magic callbacks
```

To ask questions in a chat window, add:

```bash
make teams-run           # 5. Teams bot on :3978 (dev-only dummy credentials)
make playground          # 6. Teams-style chat at http://localhost:56150
make mcp-run             # 7. optional: MCP server for Copilot on :8765/mcp
```

See [the Teams README](apps/teams/README.md) and [the MCP README](apps/mcp/README.md)
for details, and [the NL manual test plan](docs/plan/nl-ollama-manual-test-plan.md) for
what to check.

Or ask the backend directly:

```bash
curl -s http://127.0.0.1:8080/telemetry/nl/query -H 'Content-Type: application/json' \
  -d '{"question": "Is anything firing on Magic that I should worry about?"}'
```

Check config only: `uv run telemetry-agent --check-config`. Secrets come from the
environment (see `.env.example`); on localhost the agent falls back to dev values with a
warning.

What to look at:

```bash
curl http://127.0.0.1:8080/telemetry/health/agents                    # agent healthy / degraded / missing
curl http://127.0.0.1:8080/telemetry/health/agents/magic-agent-sg-01  # full heartbeat detail
curl http://127.0.0.1:8080/telemetry/alerts                           # alerts the rules fired
curl http://127.0.0.1:8081/metrics                                    # backend self-metrics
curl -i http://127.0.0.1:8081/readyz                                  # backend readiness
```

Ctrl-C stops the agent cleanly (offsets saved, final batch sent); about 60s later the
backend reports it `missing`.

The same path is covered automatically, no processes needed:

```bash
uv run pytest tests/integration/test_UBS_114_agent_end_to_end.py \
              tests/integration/test_UBS_112_113_logs_to_alerts.py \
              tests/integration/test_health_monitor_e2e.py -q
```

Known (Windows only): while the agent runs, the simulator's log rotation can fail with
`WinError 32` because the agent holds the log open. Run the simulator with
`--max-bytes 50000000` to avoid rotating during a demo.
