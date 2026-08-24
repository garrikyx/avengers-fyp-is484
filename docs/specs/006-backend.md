# 006 — Telemetry Backend Service

Status: Draft · Owner: TBD · Last updated: 2026-07-31

Python 3.12 + FastAPI + Uvicorn ([ADR 0002](../adr/0002-backend-in-python-fastapi.md)),
in-memory state only ([ADR 0005](../adr/0005-in-memory-metric-store.md)).

## 1. Internal structure

```
HTTP (FastAPI)
├── /telemetry/*            ingestion  ─┐
├── /telemetry/query/*      query       │
├── /telemetry/alerts       alerts      │
├── /telemetry/nl/*         NL adapter  │
└── /healthz, /readyz, /metrics        │
                                        ▼
                              ┌──────────────────────┐
                              │ Ingestion Service    │ auth, validate, dedupe, normalise
                              └──────────┬───────────┘
                                         ▼
                    ┌────────────────┬───────────────┬────────────────┐
                    │ Metric Store   │ Alert Store   │ Agent Registry │
                    │ time buckets   │ active/recent │ heartbeats     │
                    └────────┬───────┴───────┬───────┴────────┬───────┘
                             └──────► Query Engine ◄──────────┘
                                         ▲
                                   NL Adapter (spec 008)
```

## 2. Ingestion

| ID | Requirement |
| --- | --- |
| `FR-ING-001` | MUST accept batches at `POST /telemetry/batch` containing snapshots, events, alert changes and a heartbeat, and MUST also accept the narrower single-purpose endpoints in spec 007. |
| `FR-ING-002` | MUST authenticate every request and MUST verify that the payload's `agentId` matches the authenticated identity; a mismatch is `403`, not a silent overwrite. |
| `FR-ING-003` | MUST validate against the Pydantic models generated from `/contracts` and return `400` with a field-level error list on failure. A single invalid item MUST NOT reject the whole batch: valid items are accepted and rejected items reported (HTTP `207`-style body with `accepted` / `rejected` counts). |
| `FR-ING-004` | MUST deduplicate by `batchId` using a bounded LRU of recent IDs (default 10 000 per agent, TTL `30m`), returning `202` with `duplicate: true`. |
| `FR-ING-005` | MUST accept out-of-order and late buckets, merging by `(instanceId, bucketStartUtc, dimensions)` with counter addition, gauge last-write-wins, and histogram bucket-wise addition. Buckets older than `maxBucketAge` (default `1h`) are rejected with reason `bucket_too_old`. |
| `FR-ING-006` | MUST defensively enforce the cardinality caps of spec 004 §5 and reject series that exceed `maxSeriesPerBucket`. |
| `FR-ING-007` | MUST reject unknown `dimensions` keys and unknown `fields` keys (allowlist enforcement, second line of defence for `NFR-SEC-002`). |
| `FR-ING-008` | MUST apply per-agent rate limiting (`maxBatchesPerMinute`, default 30; `maxBodyBytes`, default 8 MiB) and return `429` with `Retry-After`. |
| `FR-ING-009` | Ingestion MUST be non-blocking: parse and validate, hand to an in-process queue, respond `202`. Queue overflow returns `503` so the agent buffers rather than the backend growing unboundedly. |
| `FR-ING-010` | MUST record every agent's last heartbeat, version, and connectivity state in the Agent Registry, and MUST expose unknown-agent first-contact as an event. |

## 3. Metric store

| ID | Requirement |
| --- | --- |
| `FR-QRY-001` | Storage MUST be a per-instance ring buffer of 10s buckets covering `retentionWindow` (default `6h`, max `24h`), plus pre-rolled 1m and 5m rollups to keep long-window queries cheap. |
| `FR-QRY-002` | Each bucket holds a map from dimension-set hash to counters and histograms. Memory MUST be bounded by evicting the oldest bucket on insert past retention, and by the series caps of spec 004. |
| `FR-QRY-003` | Memory use MUST be estimated and exposed as a gauge; the service MUST log a warning above `memoryWarnPercent` (default 75%) of `memoryLimitMb` and shed the oldest retention tier above `memorySheddPercent` (default 90%) rather than being OOM-killed. |
| `FR-QRY-004` | The store MUST be safe under concurrent read/write with a per-instance lock, not one global lock. |
| `FR-QRY-005` | Restart loses all metric state. This is accepted; `/readyz` MUST report `warming` until `warmupWindow` (default `2m`) of data exists, so dashboards and alerts do not misread an empty store as zero activity. |

## 4. Query engine

| ID | Requirement |
| --- | --- |
| `FR-QRY-006` | MUST support filtering on any dimension (exact match and `in` lists), an absolute or relative time range, `groupBy` over up to 3 dimensions, and a metric selection list. |
| `FR-QRY-007` | MUST support the derived KPIs of spec 004 §4.5, honouring `minSampleSize` and returning `null` for insufficient data. |
| `FR-QRY-008` | MUST support `topK` on a grouped result with an explicit `__other__` remainder row, so a summary of 200 symbols is answerable. |
| `FR-QRY-009` | MUST support a `series: true` mode returning a time series at a requested step (`10s`, `1m`, `5m`), aligned to the step boundary, with gaps as `null` and never as `0`. |
| `FR-QRY-011` | MUST clamp requests: `maxRangeSeconds` (default `21600`), `maxGroups` (default 500), `maxSeriesPoints` (default 1500). Exceeding these returns `400` with the applied limit named, rather than silently truncating. |
| `FR-QRY-012` | Percentiles MUST be interpolated from the fixed histogram buckets and labelled `"approximate": true` in the response. Requests for percentiles on a metric with `count < minSampleSize` return `null`. |
| `FR-QRY-013` | Every response MUST include `queryId`, `evaluatedAtUtc`, the effective (post-clamping) time range, the filters as interpreted, and `dataCompleteness` (see §5). |
| `FR-QRY-014` | Queries MUST be read-only and MUST have a server-side deadline (`queryTimeout`, default `3s`), returning `504` with partial-result metadata rather than hanging. |

### 4.1 Data completeness

`FR-QRY-015`: Because agents can be behind, restarted, or dropping data, every query response
MUST carry a `dataCompleteness` block so an answer is never silently wrong:

```json
"dataCompleteness": {
  "agentsExpected": 3,
  "agentsReporting": 3,
  "staleAgents": [],
  "restartedBuckets": 0,
  "droppedBatchesReported": 0,
  "confidence": "complete"
}
```

`confidence` is `complete` | `partial` | `degraded`. The NL adapter MUST surface anything other
than `complete` in its prose answer (`FR-NLQ-010`).

## 5. Alert store

| ID | Requirement |
| --- | --- |
| `FR-QRY-016` | MUST hold all active alerts and the last `recentAlertLimit` (default 500) resolved alerts per instance, with `firstObservedUtc`, `lastObservedUtc`, `resolvedAtUtc`, `notificationCount` and delivery status. |
| `FR-QRY-017` | Alert state from agents MUST be merged by `alertId`; a `resolved` update for an unknown `alertId` MUST be stored anyway (agents may have restarted) and flagged `synthetic: true`. |
| `FR-QRY-018` | MUST own the `AgentHeartbeatMissing` rule (`FR-RUL-030`) and expose those alerts identically to agent-generated ones, distinguished by `source: backend`. |

## 6. Health and self-metrics

`FR-HLT-010`: `/healthz` is a liveness probe (process up, no dependency checks). `/readyz`
reports readiness including warm-up state. `/metrics` exposes Prometheus-format internals:
ingest rate, validation failures, queue depth, dedupe hits, store memory, query latency
histogram, per-agent staleness.

## 7. Scaling model

| ID | Requirement |
| --- | --- |
| `NFR-SCA-002` | The service MUST run as N stateless-except-for-cache replicas. No inter-replica coordination on the ingest path. |
| `NFR-SCA-003` | Query correctness across replicas MUST be handled by scatter-gather: the replica receiving a query fans out to peers listed in the replica registry, merges bucket-wise, and unions `dataCompleteness`. Fan-out MUST have its own shorter deadline and MUST degrade to `confidence: partial` if a peer fails. |
| `NFR-SCA-004` | Alternatively (and preferably once available) the load balancer MUST consistently hash on `instanceId`, making fan-out unnecessary. The implementation MUST support both and select via config `queryMode: fanout \| colocated`. |
| `NFR-SCA-005` | Target: 10 000 ingested series-updates/sec and 50 concurrent queries per replica at p95 query latency < 300ms (spec 009). |

## 8. Configuration and secrets

Backend configuration is specified in [010-configuration.md](./010-configuration.md).
All secrets (agent tokens or CA bundle, Copilot/Teams app credentials, identifier hash key)
MUST come from environment variables or a secret manager, never from the config file
(`NFR-SEC-004`).
