# 001 — Architecture

Status: Draft · Owner: TBD · Last updated: 2026-07-31

## 1. Shape of the system

Two deployable units:

1. **Telemetry Agent** — one process per Magic host (or per instance, see §4), colocated with
  the log files. Does all reading, parsing, aggregation, rule evaluation and callback  dispatch.
2. **Telemetry Backend Service** — centralised, horizontally scalable. Ingests derived
  telemetry from many agents, holds in-memory metric views, serves queries and the natural  language adapter.

```
Magic host                                        Central
┌──────────────────────────────┐                  ┌────────────────────────────────┐
│ Magic app ──► log files      │                  │ Telemetry Backend              │
│                  │           │                  │  ingest ─► metric store        │
│                  ▼           │  HTTPS/JSON      │            alert store         │
│  ┌────────────────────────┐  │  batches         │              │                 │
│  │ Telemetry Agent        │──┼─────────────────►│              ▼                 │
│  │  log monitor           │  │  (every 10s)     │  query API ─► NL adapter       │
│  │  parser engine         │  │                  └──────┬─────────────┬───────────┘
│  │  metrics aggregator    │  │                         │             │
│  │  rule engine           │  │                  Copilot / Teams   Dashboards
│  │  callback dispatcher   │──┼──► Magic callback endpoint (HTTPS, alerts only)
│  │  health reporter       │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

Key property: **alerting does not depend on the backend.** The rule engine and callback
dispatcher run in the agent, so a backend outage degrades querying but not alerting
(`NFR-REL-003`).

## 2. Component responsibilities


| Component           | Responsibility                                                                         | Outputs                                                   | Spec     |
| ------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------- | -------- |
| Log Monitor         | Tail and interval-scan configured files; track offsets; detect rotation and truncation | Log lines with source metadata, rotation events, read lag | 002      |
| Parser Engine       | Classify each line; parse FIX; extract allowlisted fields; emit parse errors           | Structured message events, parse error events             | 003      |
| Metrics Aggregator  | Maintain bucketed counters, gauges and latency histograms across dimensions            | Metric snapshots per bucket                               | 004      |
| Rule Engine         | Evaluate thresholds, patterns, absence and latency conditions with hysteresis          | Alert firing / resolved state transitions                 | 005      |
| Callback Dispatcher | Deliver alerts to Magic with signing, retry, backoff and delivery tracking             | Callback attempts, delivery outcomes                      | 005      |
| Backend Publisher   | Batch, compress and publish snapshots/events; buffer while offline                     | Ingestion requests, publish queue metrics                 | 002      |
| Health Reporter     | Heartbeat and agent self-metrics                                                       | Heartbeat documents                                       | 011      |
| Ingestion Service   | Authenticate agents, validate payloads, normalise, fan into stores                     | Accept/reject responses                                   | 006      |
| Metric Store        | In-memory rolling time buckets per dimension set                                       | Query-ready aggregates                                    | 006      |
| Alert Store         | Active and recent alert state per instance                                             | Alert query results                                       | 006      |
| Query Service       | Filter, aggregate, group and summarise                                                 | Query responses                                           | 006, 007 |
| NL Adapter          | Map questions to structured queries; render summaries                                  | Human-readable answers                                    | 008      |




## 3. Technology stack


| Concern           | Choice                                             | Rationale / ADR                                                                                                                      |
| ----------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Agent language    | Go 1.23+, no CGO, single static binary             | Bounded footprint, trivial deployment next to Magic, cross-compiles to Linux and Windows — [ADR 0001](../adr/0001-agent-in-go.md)    |
| Backend language  | Python 3.12, FastAPI, Uvicorn, Pydantic v2         | Fast iteration, first-class OpenAPI for the Copilot plugin, strong validation — [ADR 0002](../adr/0002-backend-in-python-fastapi.md) |
| Agent → backend   | HTTPS/1.1 + JSON, gzip, batched every 10s          | Debuggable, proxy-friendly; gRPC is a Day-2 swap behind the same interface — [ADR 0003](../adr/0003-https-json-transport-day-1.md)   |
| Agent → Magic     | HTTPS POST, HMAC-SHA256 signed                     | Magic-owned contract, pending [Q-2](../plan/open-questions.md)                                                                       |
| Backend storage   | Process-local ring of time buckets, 24h max        | No DB on Day-1 — [ADR 0005](../adr/0005-in-memory-metric-store.md)                                                                   |
| Config            | YAML file + env var overrides, SIGHUP reload       | Spec 010                                                                                                                             |
| Agent packaging   | Static binary + systemd unit / Windows service     | Spec 011                                                                                                                             |
| Backend packaging | Container image, N replicas behind a load balancer | §5                                                                                                                                   |




## 4. Deployment topology

Default: **one agent per host**, monitoring all Magic instances whose logs that host owns.
Each monitored file set is tagged with its `instanceId` in configuration, so a single agent
reports for multiple instances.


| Option                       | When to prefer                                                    | Trade-off                                               |
| ---------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------- |
| One agent per host (default) | Multiple Magic instances share a host and log directory           | One failure domain for all instances on the host        |
| One agent per instance       | Strict process isolation or per-instance resource limits required | More processes, more config, higher aggregate overhead  |
| Remote agent on a log-share  | Logs are on a network share the agent can read                    | Read latency and share availability become dependencies |


`FR-CFG-010`: The agent MUST support monitoring multiple instances in one process, with
per-file-set `instanceId`, parser selection and thresholds.

Resolution of the preferred production topology is [Q-4](../plan/open-questions.md).

## 5. Scaling and multi-tenancy

- `NFR-SCA-001`: Agents are stateless with respect to the backend and MAY publish to any
backend replica; no agent affinity is required for ingestion.
- Because Day-1 metric state is per-replica in memory, **query correctness requires that a
given** `instanceId`**'s data be readable from wherever it landed.** Day-1 resolves this with
*consistent-hash routing at the load balancer on* `instanceId`, so all data for an instance
lands on one replica. `FR-ING-010`.
- `FR-QRY-020`: A query that spans instances routed to different replicas MUST be answered by
scatter-gather across replicas and merged, or the router MUST guarantee co-location.
Day-1 implements scatter-gather with a documented replica registry.
- Day-2 removes this constraint by introducing a shared store (ADR 0005, reversal condition).



## 6. Data flow summary

Full sequences are in specs 002 (ingestion), 005 (alert/callback) and 008 (NL query). In
short:

1. **Ingestion:** log line → classify → parse → allowlisted fields → bucket counters →
  rule evaluation → 10s snapshot → backend → in-memory views → queryable.
2. **Alert:** rule condition true for its `for` duration → alert fires → signed callback to
  Magic with retry → alert included in next publish → resolved when condition clears.
3. **Query:** question → intent + filters + time range → structured query → in-memory
  evaluation → grouped results → rendered summary.



## 7. Trust and failure boundaries


| Boundary                | Control                                                                                            |
| ----------------------- | -------------------------------------------------------------------------------------------------- |
| Magic process ↔ agent   | Read-only file access. The agent MUST NOT write to, signal, or link against Magic. `NFR-SEC-010`   |
| Host ↔ network          | Only derived data crosses; enforced by the field allowlist in spec 003 and tested by `NFR-SEC-002` |
| Agent ↔ backend         | Mutual TLS or bearer token; agent identity asserted as `agentId` and verified. `FR-ING-002`        |
| Agent ↔ Magic callback  | HMAC-SHA256 request signature with a shared secret from the environment. `FR-CBK-005`              |
| Backend ↔ Copilot/Teams | OAuth 2.0 / Entra ID app registration, scoped read-only. [Q-3](../plan/open-questions.md)          |


Failure behaviour, in order of what degrades first: backend queries → telemetry freshness →
callbacks → alerting. Log reading and parsing are the last things to be sacrificed, and the
agent MUST shed load rather than grow unboundedly (`FR-PUB-004`, `NFR-PERF-003`).