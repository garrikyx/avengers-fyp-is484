# ADR 0006 — Telemetry Agent is written in Python

Status: Accepted · Date: 2026-08-31 · Updated: 2026-09-07 · Deciders: TBD · Supersedes: [ADR 0001](./0001-agent-in-go.md)

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

## Monitor → parser bridge

The log monitor and parser engine have different resource profiles and MUST NOT be coupled
directly:

| Stage | Profile | Constraint |
| --- | --- | --- |
| Log monitor | I/O-bound (read, split lines, checkpoint) | MUST never block on downstream slowness |
| Parser engine | CPU-bound (classify, frame, extract) | MAY lag under burst; absorbs backlog in a bounded queue |

The bridge is implemented as a **bounded line queue** per monitored file set, plus a shared
**parser worker pool** (`asyncio` + `ThreadPoolExecutor`):

```
[Log Monitor task] ──blocking put──► [LineQueue (bounded)] ──► [Parser workers (pool)]
        │                                    │
        │ read cursor (in-memory)            ▼
        │                            [EventQueue (bounded)]
        │                                    │
        ▼                                    ▼
 committed_offset (state.json)         ingest + dedupe (FR-PIP-007)
   only after parse+ingest (FR-PIP-006)
```

Design rules:

1. **Zero loss by default.** On enqueue when the queue is full, block until capacity is
   available (`pipeline.overflowPolicy: block`). Read lag grows under overload but no line is
   discarded while the source file remains on disk (ADR 0004). Optional `drop_oldest` policy
   retains shed-load behaviour and increments drop counters.
2. **Commit after process.** Persisted offset (`committed_offset`) advances only after
   parse+ingest succeeds (`FR-PIP-006`). Restart re-reads from the last committed byte;
   dedupe by `(device, inode, byte_offset)` prevents double-count (`FR-PIP-007`).
3. **Parser gets the larger buffer.** Default `pipeline.lineQueueSize` is **2048** lines —
   much larger than downstream event queues (default **256**) — because parsing is the first
   CPU-bound stage (`FR-PIP-002`).
4. **Parser workers are capped.** Default `pipeline.parseWorkers: min(2, cpu_count)`; workers
   pull lines from the queue and call `Parser.parse()` synchronously in the pool
   (`FR-PIP-003`, `NFR-PERF-005`).
5. **Downstream stages keep smaller queues.** Parsed events flow to the metrics aggregator
   through a separate bounded channel (`pipeline.eventQueueSize`, default 256). Default policy
   blocks on overflow; optional `drop_oldest` counts `pipeline.events_dropped`.

## Consequences

- Parser plugin interface is a Python `typing.Protocol` (`FR-PRS-030`); Day-2 binary parsers are
  Python packages registered at import time (`FR-PRS-032`), not dynamically loaded modules.
- Deployment requires a Python runtime on the host (container image or bundled venv), not a
  single static binary.
- Concurrency uses `asyncio` for I/O-bound log monitors and a bounded thread pool for
  CPU-bound parsing; the supervisor loop coordinates file sets and pipeline stages.
- The **monitor → parser bridge** is a bounded queue with asymmetric sizing and default
  blocking backpressure (`FR-PIP-001`). Committed offsets lag the read cursor until ingest
  completes (`FR-PIP-006`, `FR-PIP-007`).
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
