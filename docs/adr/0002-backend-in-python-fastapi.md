# ADR 0002 — Backend is Python 3.12 + FastAPI

Status: Accepted · Date: 2026-07-31 · Deciders: TBD

## Context

The backend's demands are almost the inverse of the agent's. It runs on ordinary
infrastructure, not a trading host, and its hard problems are integration and iteration
speed, not footprint:

- It must expose an OpenAPI document good enough to drive a Copilot API plugin (spec 008 §6).
- It must do strict schema validation on every ingested payload (`FR-ING-003`, `FR-ING-007`) —
  the second line of defence for the no-sensitive-data guarantee.
- It must host the natural language adapter, including LLM structured-output calls.
- It holds only in-memory state (ADR 0005), so raw single-node throughput matters less than
  correctness and clarity.
- It will change more often than the agent, as intents, KPIs and rules evolve.

## Decision

The Telemetry Backend Service is **Python 3.12** with **FastAPI**, **Uvicorn**, and
**Pydantic v2**, packaged as a container image and run as N replicas.

## Rationale

- **OpenAPI for free, and accurate.** The Copilot plugin and Teams bot are grounded in the
  generated schema. Hand-maintaining an OpenAPI document alongside a different framework is a
  known source of drift, and a wrong schema means a Copilot agent that calls the API wrongly.
- **Pydantic v2 strict models** give exactly the validation posture the specs demand: unknown
  fields rejected rather than ignored (`FR-QRY-032`), typed coercion under control, and
  field-level error reporting for partial batch rejection.
- **LLM and Azure/Entra ecosystem** integration is best-supported in Python, and the NL layer
  is the most likely part of the system to be iterated on.
- **Iteration speed** for query semantics, KPIs and rendering templates, where the work is
  logic rather than performance.

Alternatives: Node/TypeScript with Fastify (comparable, and a reasonable choice — rejected only
because the NL/Azure tooling and the validation story are stronger in Python for this team);
Go for both components (rejected because it would make the NL and Copilot work harder for no
gain, given the backend has no footprint constraint); .NET (rejected for the same iteration
reasons as ADR 0001, inverted).

## Consequences

- Python's GIL bounds per-process CPU throughput. Mitigated by running multiple Uvicorn workers
  and multiple replicas, and by keeping ingestion cheap: validate, enqueue, `202`
  (`FR-ING-009`). If aggregation ever becomes CPU-bound, the merge path is the piece to move
  to a compiled extension or a separate service.
- The in-memory store must be written carefully in Python: per-instance locks
  (`FR-QRY-004`), pre-rolled rollups (`FR-QRY-001`), and an explicit bytes-per-series memory
  model (`NFR-SCA-006`), because Python object overhead per series is significant. Compact
  representations (arrays, `__slots__`, integer keys) are required, not optional.
- `mypy --strict` and `ruff` are blocking CI gates (spec 012 §8) — a dynamically typed service
  handling a versioned contract needs the type checker to be non-negotiable.
- Two languages, one contract: the `/contracts` schemas generate both Pydantic models and Go
  structs (`FR-ING-022`).
- Security rules for Python in this repository apply in full: no `pickle`, no `eval`/`exec`,
  no dynamic `importlib`, no user input in file paths, constant-time secret comparison
  (`NFR-SEC-018`, `NFR-SEC-005`).

## Reversal conditions

Revisit if: per-replica ingestion cannot reach `NFR-PERF-007` (10 000 series-updates/sec) after
representation optimisation; or the memory model per series proves unworkable within
`NFR-SCA-006`. In either case the metric store — not the API layer — is what moves, most likely
to Go or to an embedded time-series engine.
