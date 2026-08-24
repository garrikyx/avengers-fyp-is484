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
monitor/       # Log monitoring, offsets, rotation
parsers/       # FIX parsing / future binary parsing
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
from telemetry_agent.parsers.fix import FixParser
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
Python 3.12+
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

# Lint & format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy .

```
