# ADR 0006 — Telemetry Agent is written in Python

Status: Accepted · Date: 2026-08-31 · Deciders: TBD · Supersedes: [ADR 0001](./0001-agent-in-go.md)

## Context

The team repository is a **Python monorepo** (`apps/agent`, `apps/backend`, `packages/telemetry_shared`)
established in commit `6601a5a`. ADR 0001 chose Go for the agent based on footprint, static
binary deployment, and `-benchmem`-enforceable parsing allocations.

For the capstone delivery model, a single-language Python stack reduces operational complexity,
lets the agent share Pydantic models with the backend via `packages/telemetry_shared/`, and
matches how the team develops and tests (`pytest`, `ruff`, `mypy`, `uv`).

The agent's constraints remain: bounded CPU and memory on a trading host, read-only log access,
no raw log egress, and per-file concurrency for tailing and parsing.

## Decision

The Telemetry Agent is written in **Python 3.12+** under `apps/agent/src/telemetry_agent/`,
packaged as part of the uv workspace and deployed via container or managed virtualenv on the
Magic host.

## Rationale

| Factor | Assessment |
| --- | --- |
| **Team monorepo** | Ryan's scaffold and README already define a Python agent layout; fighting that adds migration cost with no Day-1 benefit. |
| **Shared models** | `packages/telemetry_shared/` replaces hand-maintained Go/Python dual schemas for Day-1. |
| **Iteration speed** | Parser, metrics, rules and callbacks evolve together; one language keeps PRs reviewable. |
| **Test tooling** | `pytest` requirement-ID tests, `hypothesis` property tests, and `mypy --strict` align with spec 012. |
| **Go concerns mitigated** | Bounded queues (`FR-PUB-004`), explicit memory caps (`NFR-PERF-003`), load shedding, and per-line exception recovery address the footprint risks ADR 0001 cited for Python. |

ADR 0001 remains in the record for historical context. New agent work follows this ADR.

## Consequences

- Parser plugin interface is a Python `typing.Protocol` (`FR-PRS-030`); Day-2 binary parsers are
  Python packages registered at import time (`FR-PRS-032`), not dynamically loaded modules.
- Deployment requires a Python runtime on the host (container image or bundled venv), not a
  single static binary.
- Concurrency uses `asyncio` tasks or thread-per-file readers rather than goroutines; the
  supervisor loop coordinates file sets.
- `NFR-PERF-004` is enforced via profiling and allocation-aware parser design in pytest, not
  Go `-benchmem`.
- The backend and agent share one language; schema drift is managed through
  `packages/telemetry_shared/` rather than `/contracts` code generation for Day-1.

## Reversal conditions

Revisit if: load testing shows the agent cannot meet `NFR-PERF-003` (<500 MB RSS, <2% CPU at
target throughput) after bounded-queue tuning and parser optimisation — consider moving only
the log monitor hot path to a compiled extension or back to Go while keeping Python for rules
and publishing.

Or if: Magic platform mandates no Python runtime on trading hosts (→ reinstate ADR 0001 for
the agent shell only).
