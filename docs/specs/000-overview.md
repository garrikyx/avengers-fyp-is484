# 000 — Overview, Scope and Conventions

Status: Draft · Owner: TBD · Last updated: 2026-07-31

## 1. Purpose

The Telemetry System provides near real-time visibility into the Magic trading
application: application logs, FIX message flow, order and execution activity, rejection
patterns, latency indicators, and health. It exposes that visibility through query APIs and
natural language access via Microsoft Copilot or Teams, and pushes critical conditions back
to Magic as callbacks.

The system is **streaming-first** and **stores no raw logs**. It derives metrics, counters,
summaries and structured events as log lines are produced, and discards the raw content.

## 2. Problem statement

| ID | Problem | Addressed by |
| --- | --- | --- |
| P-1 | Limited visibility into live trading activity and application health during production hours | Streaming metrics + query APIs (specs 004, 006) |
| P-2 | Rejects, execution failures, latency spikes and protocol errors are slow to identify | FIX parsing + rule engine (specs 003, 005) |
| P-3 | Troubleshooting is reactive and depends on manual log inspection | Real-time alerting + callbacks to Magic (spec 005) |
| P-4 | Support, development and operations teams cannot ask questions of live telemetry | Natural language adapter (spec 008) |
| P-5 | Raw trading logs are sensitive and cannot be centralised in a log store | No-raw-persistence design (ADR 0004, spec 009) |

## 3. Scope

### 3.1 In scope (Day-1)

- Real-time tailing and interval-based reading of configured log files, including rotation.
- FIX 4.2 / 4.4 tag=value parsing with validation and malformed-line tolerance.
- Rolling metrics for orders, executions, rejections, rejection reasons and latency.
- Configurable alert rules with severity, hysteresis and resolution.
- Callback delivery to a Magic-provided HTTPS endpoint, with retry and delivery tracking.
- Structured telemetry publication to a centralised backend.
- Metrics, alert and health query APIs.
- Natural language query access through Copilot or Teams for a fixed intent catalogue.
- Self-monitoring: heartbeat, parse error counts, queue depth, callback failures.

### 3.2 Out of scope (Day-2 or later)

- Binary / proprietary protocol parsing (the parser interface must accommodate it — `FR-PRS-020`).
- Durable persistence, historical forensics, log replay, long-term trend analytics.
- Anomaly detection and adaptive thresholds.
- Dashboards beyond what the query API enables; rich Teams interactive workflows.
- Any storage or transmission of raw log lines or full FIX message bodies.

### 3.3 Explicit non-goals

- The system is **not** a log aggregation platform and does not replace one.
- The system is **not** in the order path and MUST never be able to affect order flow.
- The system does **not** guarantee complete message capture; it is a telemetry system, not
  an audit or regulatory record. Gaps are reported (`FR-HLT-004`), not backfilled.

## 4. Actors and consumers

| Actor | Interaction |
| --- | --- |
| Magic application | Writes logs; receives alert callbacks; owns the callback endpoint contract |
| Telemetry Agent | Runs on the Magic host; reads logs; publishes telemetry; sends callbacks |
| Telemetry Backend | Aggregates telemetry from all agents; serves queries |
| Support / Ops engineer | Asks questions in Teams or Copilot; receives alerts |
| Developer | Queries metrics APIs during incident investigation |
| Platform operator | Deploys and configures agents, runs the runbooks in spec 011 |

## 5. Glossary

| Term | Meaning |
| --- | --- |
| **Magic** | The trading application under observation |
| **Agent** | Telemetry Agent process, deployed on or beside a Magic host |
| **Backend** | Centralised Telemetry Backend Service |
| **Instance** | One logical Magic application instance (`instanceId`), e.g. `magic-prod-01` |
| **Session** | A FIX session, identified by `SenderCompID` / `TargetCompID` pair |
| **Bucket** | A fixed-width time slice of aggregated metrics (default 10s) |
| **Window** | A rolling aggregation over N buckets (1m / 5m / 15m / 1h) |
| **Event** | A structured, derived record emitted by the agent (never a raw log line) |
| **Callback** | An HTTPS POST from the agent to a Magic-owned endpoint |
| **Derived data** | Counters, histograms, allowlisted field values — the only data that leaves the host |

## 6. Requirement ID scheme

Functional requirements are `FR-<AREA>-<NNN>`; non-functional are `NFR-<AREA>-<NNN>`.

| Area code | Domain | Home spec |
| --- | --- | --- |
| `LOG` | Log monitoring, offsets, rotation | 002 |
| `PRS` | Parser engine and FIX parsing | 003 |
| `MET` | Metrics aggregation and data model | 004 |
| `RUL` | Rule engine and alerting | 005 |
| `CBK` | Callback dispatch and delivery | 005 |
| `PUB` | Backend publisher, batching, buffering | 002 |
| `ING` | Backend ingestion | 006 |
| `QRY` | Query engine and APIs | 006, 007 |
| `NLQ` | Natural language adapter | 008 |
| `HLT` | Health and self-observability | 011 |
| `CFG` | Configuration | 010 |
| `PERF`, `REL`, `SEC`, `SCA`, `OBS` | Non-functional areas | 009 |

Rules for IDs: allocate the next free number in the owning spec, never renumber, never
reuse. A withdrawn requirement keeps its ID and is annotated `(withdrawn — see …)`.

## 7. Day-1 acceptance definition

Day-1 is complete when, against a synthetic Magic log stream at the throughput agreed in
[open question Q-1](../plan/open-questions.md):

1. A reject burst in the log is visible in a backend metrics query within 5 seconds.
2. The `HighRejectRate` rule fires, is delivered to a mock Magic callback endpoint, and
   resolves when the burst stops.
3. "Why are Magic orders rejecting in the last 30 minutes?" in Copilot or Teams returns a
   grouped rejection summary consistent with the metrics query.
4. Log rotation, a 5-minute backend outage, and an agent restart each occur during the run
   without data loss beyond the documented bounds in `NFR-REL-001`–`NFR-REL-004`.
5. An automated test proves no raw log line or non-allowlisted FIX tag left the host
   (`NFR-SEC-002`).
