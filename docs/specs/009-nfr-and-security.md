# 009 — Non-Functional Requirements and Security

Status: Draft · Owner: TBD · Last updated: 2026-07-31

Every requirement here is stated as something a test or a measurement can decide. Provisional
numbers are marked and depend on [Q-1](../plan/open-questions.md) (expected throughput).

## 1. Performance

| ID | Requirement | Verified by |
| --- | --- | --- |
| `NFR-PERF-001` | At a sustained 5 000 log lines/sec on one host (provisional), the agent MUST use less than 1 CPU core on average over 5 minutes and MUST NOT exceed 2 cores at peak. | Load test, spec 012 §5 |
| `NFR-PERF-002` | p95 latency from log line write to the line being reflected in a backend query MUST be under 5s; p99 under 10s. | End-to-end timing test |
| `NFR-PERF-003` | Agent RSS MUST stay under 150 MB at target throughput; the agent MUST shed load (drop + count) rather than exceed it. | Load test with RSS assertion |
| `NFR-PERF-004` | The agent MUST NOT allocate unbounded structures per parsed message on the hot path; parse allocations SHOULD be profiled and kept minimal. | `pytest-benchmark` or `tracemalloc` spot checks |
| `NFR-PERF-005` | Worker concurrency MUST be configurable and MUST default to a small bound (e.g. `min(2, cpu_count)`) so the agent cannot monopolise a trading host. | Unit test |
| `NFR-PERF-006` | The agent's deployment unit MUST declare explicit CPU and memory caps (cgroup, job object, or service unit limits), so the host operator can see the bound rather than trust the process. | Deployment review, spec 011 §4 |
| `NFR-PERF-007` | Backend MUST ingest 10 000 series-updates/sec per replica at p95 request latency under 200ms. | Load test |
| `NFR-PERF-008` | Backend query p95 MUST be under 300ms for a 1h range with `groupBy` of 2 dimensions, and under 1s for a 6h range. | Load test |
| `NFR-PERF-009` | A single log line MUST NOT trigger any synchronous network or disk I/O. | Code review + fault-injection test |
| `NFR-PERF-010` | The agent MUST NOT hold any lock on the monitored file, and MUST NOT prevent Magic from rotating or deleting it (Windows: open with full share flags). | Rotation test on both platforms |

## 2. Reliability

| ID | Requirement |
| --- | --- |
| `NFR-REL-001` | A malformed line, unknown enum, or unexpected encoding MUST NOT crash, stall, or degrade the agent; it is counted and dropped. |
| `NFR-REL-002` | Log rotation MUST lose no more than the lines written to the old file after the last read and before the rotation drain completes, and the drain MUST cover `rotationDrainTimeout` (default `5s`). |
| `NFR-REL-003` | A total backend outage MUST NOT affect log reading, parsing, aggregation, rule evaluation, or callback delivery. Only query freshness degrades. |
| `NFR-REL-004` | An agent restart MUST resume within `5s` and re-read at most `checkpointInterval` of data; duplicated data MUST be confined to the buckets marked `restarted: true`. |
| `NFR-REL-005` | The agent MUST recover from an unhandled exception in any per-line or per-file worker without terminating the process, and MUST count `agent.exceptions_recovered`. A fatal error in the supervisor is fatal by design. |
| `NFR-REL-006` | Backend replica loss MUST lose only that replica's in-memory state; agents MUST continue publishing to surviving replicas, and queries MUST report reduced `dataCompleteness` rather than wrong numbers. |
| `NFR-REL-007` | Clock changes (NTP step, DST) MUST NOT create negative durations or duplicate buckets; all internal timing MUST use a monotonic clock, with wall-clock used only for labelling. |
| `NFR-REL-008` | The agent MUST start successfully when a configured log file does not yet exist, and MUST begin reading when it appears. |
| `NFR-REL-009` | No unbounded queue, map, or buffer anywhere. Every accumulating structure MUST have a documented cap and a drop counter. This is enforced by code review checklist and by the memory soak test. |

## 3. Security

### 3.1 Data minimisation

| ID | Requirement |
| --- | --- |
| `NFR-SEC-001` | Raw log lines MUST NOT be persisted to disk, transmitted off-host, or included in any event, metric label, alert, or error message. |
| `NFR-SEC-002` | Only the allowlisted FIX tags of spec 003 §4 may be extracted, and only in their specified emitted form (hashed where required). An automated test MUST run a corpus containing distinctive sentinel values in non-allowlisted tags (price, account, party IDs, free text) and assert those sentinels appear in **no** outbound payload, log file, or state file. |
| `NFR-SEC-003` | The agent state file MUST contain only offsets, file identities, and alert state. |
| `NFR-SEC-012` | Order identifiers MUST be HMAC-SHA256 hashed and truncated (spec 003 §4); the key MUST come from the environment and MUST be rotatable (rotation breaks cross-period correlation, which is accepted and documented). |
| `NFR-SEC-013` | Debug logging MUST NOT have a mode that prints raw lines. If a developer needs that locally, it MUST be a separate build tag (`//go:build debugraw`) that is never compiled into release artefacts, and CI MUST assert the release binary does not include it. |

### 3.2 Secrets

| ID | Requirement |
| --- | --- |
| `NFR-SEC-004` | No secret (agent token, callback HMAC secret, hash key, Copilot credentials) may appear in source, config files, container images, or command lines. Environment variables or a secret manager only. |
| `NFR-SEC-005` | Secret comparison MUST be constant-time (`hmac.compare_digest` in Python). |
| `NFR-SEC-006` | Secrets MUST be redacted from all logs and from all error responses; a CI check MUST grep artefacts for known secret-shaped patterns. |

### 3.3 Transport and identity

| ID | Requirement |
| --- | --- |
| `NFR-SEC-007` | All network calls MUST use TLS 1.2 or higher with certificate verification enabled. Disabling verification MUST NOT be possible in a release build; local development uses a real local CA. |
| `NFR-SEC-008` | Agents MUST authenticate to the backend, and the backend MUST reject a payload whose `agentId` differs from the authenticated identity. |
| `NFR-SEC-009` | Query and NL access MUST be authenticated per user and authorised read-only. No endpoint may mutate telemetry. |
| `NFR-SEC-010` | The agent MUST run as an unprivileged account with read-only access to the log directory and no write access anywhere except its own state directory. It MUST NOT require membership in any group that grants Magic process control. |

### 3.4 Input handling

| ID | Requirement |
| --- | --- |
| `NFR-SEC-014` | Log content, FIX fields, and question text are all untrusted input. None of them may be used to build a file path, a shell command, a `require`/import target, an SQL/query string, or a template with code execution. |
| `NFR-SEC-015` | Configured file paths MUST be resolved once at load, canonicalised, and checked against an allowed root list; symlinks pointing outside the allowed roots MUST be refused. |
| `NFR-SEC-016` | The backend MUST NOT perform any filesystem operation derived from request content. |
| `NFR-SEC-017` | Any value rendered into HTML, Markdown, Adaptive Cards, or a terminal MUST be escaped for that context (`FR-QRY-038`, `FR-NLQ-022`). |
| `NFR-SEC-018` | Deserialisation MUST use strict schema validation (Pydantic strict models with `extra="forbid"`). Python code MUST NOT use `pickle`, `eval`, `exec`, or dynamic `importlib` on any external input. |
| `NFR-SEC-019` | Dependencies MUST be pinned with a lockfile, scanned in CI (`govulncheck`, `pip-audit`), and the build MUST fail on a known high-severity vulnerability. |

### 3.5 Auditability

`NFR-SEC-011`: The backend MUST log, for each query: request ID, authenticated user or agent,
interpreted query, result row count, and duration — but not the raw question text and not
result values.

## 4. Scalability

| ID | Requirement |
| --- | --- |
| `NFR-SCA-001` | Agents MUST be independent; adding an agent MUST require no change to other agents. |
| `NFR-SCA-006` | The backend MUST support at least 50 agents and 100 instances per replica within its memory budget, and the memory model MUST be documented as bytes-per-series-per-bucket so capacity can be computed rather than guessed. |
| `NFR-SCA-007` | Adding a replica MUST require only configuration of the replica registry or load balancer, with no data migration. |

## 5. Configurability

| ID | Requirement |
| --- | --- |
| `NFR-CFG-001` | Log paths, read modes, parser selection, dimensions, alert thresholds, callback endpoints, aggregation windows, retention and retry limits MUST all be configurable without a code change. |
| `NFR-CFG-002` | Configuration MUST be validated at start; the process MUST refuse to start on invalid configuration with a message naming the offending key and the reason. |
| `NFR-CFG-003` | Thresholds, rules, silences and reject-reason patterns MUST be reloadable on SIGHUP without restart or loss of alert state. Log paths and listeners MAY require a restart. |
| `NFR-CFG-004` | Every configuration key MUST have a documented default in spec 010, and the code default MUST match the document — verified by a test that renders defaults and compares to a golden file. |

## 6. Observability of the telemetry system itself

| ID | Requirement |
| --- | --- |
| `NFR-OBS-001` | The agent MUST expose the self-metrics of spec 004 §4.3 both in its heartbeat and on a local `/metrics` endpoint bound to loopback by default. |
| `NFR-OBS-002` | Every drop, rejection, retry and fold MUST have a counter. Silent data loss is a defect. |
| `NFR-OBS-003` | Agent and backend logs MUST be structured JSON with a consistent field set, including `requestId` / `batchId` correlation. |
| `NFR-OBS-004` | Log volume from the telemetry system itself MUST be bounded: repeated identical errors MUST be rate-limited and aggregated, so a log parse failure storm cannot fill the disk of a trading host. |

## 7. Compliance and operability constraints

| ID | Requirement |
| --- | --- |
| `NFR-OPS-001` | The agent MUST be distributable as a single binary with no runtime dependency beyond libc, and MUST support Linux x86-64 and Windows x86-64. |
| `NFR-OPS-002` | Deployment MUST be possible without restarting Magic. |
| `NFR-OPS-003` | The agent MUST support a `--check-config` and a `--dry-run` mode that validates configuration and reports which files it would read, without publishing or calling back. |
| `NFR-OPS-004` | Version and build information MUST be reported in `--version`, in heartbeats, and in structured logs. |
