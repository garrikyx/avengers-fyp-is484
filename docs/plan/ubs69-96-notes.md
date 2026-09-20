# UBS-69 / UBS-96 implementation notes — backend health read side, self-metrics

Working notes for the stacked `UBS-69-Backend-Health-Endpoints` → `UBS-96-Backend-Self-Metrics`
branches (which sit on top of 58 → 59 → 60 because they need the spec-shaped
`AgentHeartbeat`). Same convention as the other notes: code says *what*, this says *why*.
End-to-end picture: [`health-reporter-overview.md`](./health-reporter-overview.md).

## Decisions that need team sign-off (read first)

| Topic | Decision | Why | Who it affects |
| --- | --- | --- | --- |
| Who creates the FastAPI app | UBS-69 adds `app.py` with `create_public_app()` / `create_internal_app()`, one router file per concern under `api/`, shared `AppDeps` on `app.state`. | Nobody owned it; `fastapi`/`uvicorn` were declared but unused. A factory + router-per-file is the least-conflict shape for parallel tickets. | **Mitch (UBS-66)** mounts the ingestion router in `create_public_app` and deletes `api/ingest_placeholder.py`. |
| Agent registry lives in UBS-69 | `services/agent_registry.py` has both `record_heartbeat()` (write) and `get()/all()/status_of()/stale_agents()` (read). | UBS-69's scope note calls it "the read side of that same registry"; a read side can't be tested without a writer. One registry, not two. | **Mitch (UBS-87)**: remaining scope = call `registry.record_heartbeat()` from the batch path and emit the first-contact *event* when it returns `True`. |
| Placeholder `POST /telemetry/heartbeat` | Spec 007 §2.3's narrow endpoint, validation + `record_heartbeat()` only. No auth / limits / queue. | Makes 58 → 69 runnable end to end today; replaces `scripts/heartbeat_receiver_stub.py` (deleted). | Mitch absorbs or deletes it. |
| Stale vocabulary | `missing` (spec 007 §5.1 `counts`), not the UBS-58 ticket's `unresponsive`. | Wire contract. | Amend UBS-58/69 tickets. |
| Threshold | `alerting.missingHeartbeatThreshold` default **60s** (spec 005 `FR-RUL-030`, spec 010), not "3× interval". | The backend doesn't know each agent's interval; the spec gives one number. | — |
| `/metrics` implementation | `prometheus-client` dependency added; `SelfMetrics` owns a private `CollectorRegistry`. | Standard exposition format and histograms for free; hand-rolling the text format is error-prone. Dependency needs team OK. | — |
| `/readyz` warm-up source | `warming` until `store.warmupWindow` (2m) has elapsed since the **first accepted telemetry ingest**; heartbeats do not count. Until the ingestion path lands, `/readyz` stays 503 `warming` with `sinceFirstIngestSeconds: null`. | FR-QRY-005 exists so an empty store is never read as "no activity"; agents saying hello is not data. | **Mitch (UBS-66)**: call `deps.warmup.mark_ingest()` when a batch is accepted. |
| `dataCompleteness.staleAgents` | `services/data_completeness.build()` + `registry.stale_agents()` shipped and tested; **no query endpoint exists to attach it to**. | Building a query API here would be UBS-91's work. | **UBS-91** (unassigned) calls `build()` per query and fills the bucket-level fields from the store. **Garrison (UBS-95)** reads `stale_agents()` for `AgentHeartbeatMissing`. |

## Module map (`apps/backend/src/telemetry_backend/`)

| File | Role |
| --- | --- |
| `config.py` (extended) | `BackendHealthConfig` (`missing_heartbeat_threshold_seconds`, `warmup_window_seconds`, `listen`, `internal_listen`) + `load_backend_health_config(config/backend.yaml)`. Unlike the agent's loader, unknown keys inside `backend:`/`store:`/`alerting:` are **tolerated**, because spec 010 puts other components' keys (`workers`, `retentionWindow`, …) in the same sections; a misspelt key of ours keeps its default, so use `telemetry-backend --check-config` to see effective values. |
| `deps.py` | `AppDeps` — the one object both apps share (`config`, `clock`, `registry`, `self_metrics`, `warmup`). `get_deps(request)` is the FastAPI dependency. Injectable clock is what makes every staleness/warm-up test deterministic. |
| `app.py` | The two factories. Public app: `health` + `ingest_placeholder` routers + a latency middleware. Internal app: `internal` router only. |
| `main.py` | `telemetry-backend` console script: two `uvicorn.Server`s in one asyncio loop bound to `listen` / `internalListen` (`FR-HLT-012`). `--check-config` for the install runbook. |
| `services/agent_registry.py` | `AgentRegistry`, `AgentRecord`. |
| `services/data_completeness.py` | `DataCompleteness` model + `build()`. |
| `api/health.py` | `GET /telemetry/health/agents`, `GET /telemetry/health/agents/{agentId}`. |
| `api/ingest_placeholder.py` | Temporary `POST /telemetry/heartbeat`. |
| `services/self_metrics.py` (UBS-96) | `SelfMetrics` (private Prometheus registry; typed counters/gauges/histogram for ingestion, store, query, agents) and `WarmupTracker`. |
| `api/internal.py` (UBS-96) | `GET /healthz`, `GET /readyz`, `GET /metrics`. |
| `packages/telemetry_shared/models/health.py` (extended) | `AgentHealthSummary`, `AgentHealthList`, `HealthCounts`, `AgentHealthDetail`, `RegistryStatus` — response contracts shared with the NL adapter / UI later. |

## Design points (UBS-69)

- **Staleness is decided on the backend clock, at read time.** `AgentRecord.received_at`
  is stamped by the backend; `heartbeatAgeMs = now − received_at`. The agent's own
  `sentAtUtc` is echoed as `lastHeartbeatUtc` but never used to judge liveness — a
  skewed agent clock must not make a live agent look dead or a dead one look alive
  (tested: an agent 3h ahead still goes `missing` 60s after it stops). No background
  sweeper is needed for the endpoints; UBS-95's alert rule will need a ticker, which is
  its concern.
- **`status` vs `reportedStatus`.** `status` is the backend's verdict: `missing` if
  stale, else whatever the agent last said. `reportedStatus` + `statusReasons` keep the
  agent's last word verbatim, so an operator sees "missing, and the last thing it said
  was `unhealthy: parse error rate 100%`".
- **Late, older heartbeats don't roll back.** `record_heartbeat()` ignores a document
  whose `sentAtUtc` is older than the stored one (out-of-order delivery through a
  retry buffer is exactly what `BufferingHeartbeatSink` produces).
- **First contact is a return value, not an event.** `record_heartbeat()` returns `True`
  once per agent; emitting the `FR-ING-010` event is the ingestion path's job (UBS-87).
- **`FR-HLT-011`.** `files[].path` is passed through from the heartbeat and is the only
  path-like field; a test asserts nothing else in the detail response contains a path
  separator, and nothing on the backend ever opens it.
- **404 shape** follows spec 007 §4.2's `{code: "not_found"}` (inside FastAPI's `detail`).
- **Memory-only** like the Metric Store (`FR-QRY-005`): a restart forgets all agents
  until their next heartbeat — at most one interval.

## Design points (UBS-96)

- **`/healthz` checks nothing.** Process up → 200. A broken store or a silent fleet must
  not make an orchestrator restart a backend that is otherwise serving (`FR-HLT-010`).
- **`/readyz` is 503 while warming**, with a body (`status`, `warmupWindowSeconds`,
  `sinceFirstIngestSeconds`) so a human can tell "just started" from "never got data".
  Warm-up starts at the first *accepted telemetry batch*, not process start and not the
  first heartbeat — `WarmupTracker.mark_ingest()` is the hook the ingestion path calls.
- **Every metric exists from the first scrape** with value 0, even those whose producer
  (ingestion, dedupe, store) is another ticket. A missing series looks like a broken
  exporter; a 0 looks like idle. Producers call plain `.inc()` / `.set()` on typed
  attributes of `deps.self_metrics` and never see Prometheus.
- **Per-agent gauges are recomputed at scrape time** from the registry
  (`refresh_agent_gauges()`), so there is no background thread and decommissioned agents
  drop out of the exposition. Label cardinality is bounded by the registry size
  (`store.maxInstances`).
- **Query latency is labelled by route template**, never the raw path
  (`/telemetry/health/agents/{agent_id}`, not `/…/magic-agent-sg-01`); unmatched paths are
  bucketed as `unmatched`. Buckets bracket the 3s query deadline / 5s p95 SLO.
- **Listener split is tested both ways**: the public app 404s `/healthz` `/readyz`
  `/metrics`; the internal app 404s every public route.
- **Metric names**: `telemetry_backend_ingest_batches_total`, `…_ingest_validation_failures_total`,
  `…_ingest_dedupe_hits_total`, `…_dropped_payloads_total`, `…_heartbeats_received_total`,
  `…_ingest_queue_depth`, `…_store_buckets`, `…_store_memory_bytes`,
  `…_query_latency_seconds{route}`, `…_agents_known`, `…_agents_stale`,
  `…_agent_heartbeat_age_seconds{agent_id}`, `…_agent_stale{agent_id}`, `…_warming_up`.

## Missing downstream / upstream

| Gap | Effect | Owner |
| --- | --- | --- |
| Real ingestion (`POST /telemetry/batch`, auth, limits, queue) | Heartbeats arrive only via the placeholder route; batch-embedded heartbeats are not recorded | UBS-66 / 85 / 87 |
| First-contact event | Only a boolean today | UBS-87 |
| `/readyz` never becomes `ready` | nothing calls `warmup.mark_ingest()` until the batch path exists | UBS-66 |
| Ingest / dedupe / store metrics stay 0 | producers not wired | UBS-66 / 85 / 90 |
| Query API + `dataCompleteness` in responses | Helper exists, nothing calls it | UBS-91 |
| `AgentHeartbeatMissing` alert | Staleness reported, not alerted | UBS-95 |
| `files[].instanceId` | `null` — the agent's `LogMonitor` has no file→instance mapping yet | agent, UBS-22 owner |
| Persistence / multi-replica registry | Each replica has its own registry; `query.mode: fanout` (spec 010) would need a merge | later |

## How to see it

```bash
uv run telemetry-backend                                   # :8080 public, :8081 internal
uv run telemetry-agent-heartbeat --interval 2 --sink http://127.0.0.1:8080/telemetry/heartbeat
curl -s localhost:8080/telemetry/health/agents | jq
curl -s localhost:8080/telemetry/health/agents/magic-agent-local | jq
curl -s -i localhost:8081/healthz          # 200 ok
curl -s -i localhost:8081/readyz           # 503 warming until telemetry batches arrive
curl -s localhost:8081/metrics | grep telemetry_backend_agent
# Ctrl-C the agent; after alerting.missingHeartbeatThreshold (60s) the list shows "missing"
```

Automated: `tests/unit/backend/services/test_agent_registry.py`, `test_data_completeness.py`,
`tests/unit/backend/api/test_health_api.py`, `tests/unit/backend/test_backend_health_config.py`,
and `tests/integration/backend/test_heartbeat_roundtrip.py` (builds a heartbeat with the
agent's real `HealthReporter`, posts it through the app, reads it back). UBS-96:
`tests/unit/backend/api/test_internal_api.py`, `tests/unit/backend/services/test_self_metrics.py`.

## Also touched, and why

- `apps/backend/pyproject.toml`: `pyyaml` (config loader), `httpx` (FastAPI `TestClient`),
  `prometheus-client` (UBS-96), `telemetry-backend` console script.
- `config/backend.yaml`: created (commented example; spec 010 §2 keys).
- `scripts/heartbeat_receiver_stub.py`: **deleted** — the backend's placeholder route and
  health endpoints replace it. Agent demo/heartbeat docstrings updated to point at the
  backend.
- `AgentRegistry.all()` rather than `.list()`: a method named `list` shadows the builtin
  inside its own annotations under `from __future__ import annotations`.
