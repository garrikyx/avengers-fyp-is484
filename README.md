# UBS Telemetry System for Magic Application

SMU FinTech capstone project

The repo contains four main applications:

```text
apps/
├── agent/       # Runs beside each Magic instance
├── backend/     # Central telemetry API/service
├── teams/       # Microsoft Teams integration
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
Telemetry Backend
      ↓
Redis
      ↓
Microsoft Teams

Day 2:
Telemetry Backend → PostgreSQL
```

Each Magic instance is paired with one Telemetry Agent. Multiple agents send structured telemetry to the central backend.

Day 1 uses Redis for temporary/shared telemetry state. Day 2 adds PostgreSQL for approved historical metrics, alerts and anomaly data.

Raw Magic logs and full FIX payloads must not be persisted.

---

# Where should I work?

## Telemetry Agent

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

## Telemetry Backend

```text
apps/backend/src/telemetry_backend/
```

Main areas:

```text
api/           # FastAPI endpoints
services/      # Business logic
repositories/  # Redis / PostgreSQL access
anomaly/       # Day-2 anomaly detection
persistence/   # Day-2 PostgreSQL
```

Backend flow should generally be:

```text
API → Service → Repository → Redis/PostgreSQL
```

Do not call Redis directly from FastAPI route handlers.

---

## Microsoft Teams

```text
apps/teams/src/teams_agent/
```

Used for:

* sending alerts to Teams
* receiving user questions
* calling backend APIs
* formatting responses

Teams should communicate with the backend, not directly with Redis or PostgreSQL.

---

## Magic Simulator

```text
apps/simulator/src/magic_simulator/
```

Used to generate synthetic FIX/log activity for development because we do not have access to the real UBS production Magic environment.

---

# Shared Schemas

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

Do not independently create different versions of the same telemetry object inside Agent, Backend and Teams.

---

# Python Folder Structure

We use Python's `src` layout.

Example:

```text
apps/agent/
└── src/
    └── telemetry_agent/
        ├── __init__.py
        └── main.py
```

* `apps/agent` = deployable application
* `src` = source-code directory
* `telemetry_agent` = actual Python package
* `__init__.py` = marks the package
* `main.py` = application entry point

Imports should look like:

```python
from telemetry_agent.parser.fix import FixParser
```

not:

```python
from src.telemetry_agent.parsers.fix import FixParser
```

---

# Before Starting Your Jira Story

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

# Local Tools

Current stack:

```text
Python 3.14+
FastAPI
Pydantic
Redis
PostgreSQL (Day 2)
pytest
Ruff
mypy
Docker / Docker Compose
```

Useful commands will be added as the project setup matures.

---

# Important Design Rules

* Agent must remain lightweight.
* Target Agent resource usage: **<2% CPU and <500 MB memory**.
* Backend should be stateless and horizontally scalable.
* Shared state belongs in Redis.
* Historical Day-2 data belongs in PostgreSQL.
* Raw logs/full FIX payloads must not be persisted, only sanitised logs
* Teams only communicates through Backend APIs.
* Day-1 rules use configured thresholds.
* Day-2 anomaly detection compares current behaviour against historical/rolling baselines.

If you are unsure where your feature belongs, check the folder responsibilities above before creating new modules.


## Quick start

```bash
# Install uv (if not present)
curl -LsSf https://astral.sh/uv/install.sh | sh

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

# Run the full stack locally (agent + backend + health monitor)

> **Tentative** — local development only. `config/agent.yaml` points at
> localhost over plain http; the production deployment of the agent is
> not set up yet.

`telemetry-agent` is the real agent (UBS-114): one process that tails the
logs, parses them, updates metrics and agent health, evaluates the rules and
publishes alerts + heartbeats to the backend (and signed callbacks to Magic).
It replaces the old `telemetry-agent-heartbeat` and
`scripts/health_monitor_demo.py` demos.

Four terminals, all from the repo root:

```bash
uv sync --all-packages                                     # once

uv run telemetry-backend                                   # 1. backend: :8080 public, :8081 internal
uv run python apps/simulator/src/simulator/mock_logger.py  # 2. writes ./logs/Application.log + Fix.log
uv run telemetry-agent --config config/agent.yaml          # 3. the agent
# 4. optional: anything listening on 127.0.0.1:9000 receives the Magic callbacks
```

Check config only: `uv run telemetry-agent --check-config`.
Secrets come from the environment (see `.env.example`); on localhost the
agent falls back to dev values with a warning.

What to look at:

```bash
curl http://127.0.0.1:8080/telemetry/health/agents                    # agent healthy / degraded / missing
curl http://127.0.0.1:8080/telemetry/health/agents/magic-agent-sg-01  # full heartbeat detail
curl http://127.0.0.1:8080/telemetry/alerts                           # alerts the rules fired
curl http://127.0.0.1:8081/metrics                                    # backend self-metrics
curl -i http://127.0.0.1:8081/readyz                                  # backend readiness
```

Ctrl-C stops the agent cleanly (offsets saved, final batch sent); about 60s
later the backend reports it `missing`.

The same path is covered automatically, no processes needed:

```bash
uv run pytest tests/integration/test_UBS_114_agent_end_to_end.py \
              tests/integration/test_UBS_112_113_logs_to_alerts.py \
              tests/integration/test_health_monitor_e2e.py -q
```

Known (Windows only): while the agent runs, the simulator's log rotation can
fail with `WinError 32` because the agent holds the log open. Run the
simulator with `--max-bytes 50000000` to avoid rotating during a demo.
