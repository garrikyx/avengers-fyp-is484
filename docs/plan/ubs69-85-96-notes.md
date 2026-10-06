# UBS-69 / UBS-85 / UBS-96 — decisions and open points

Status: 2026-09-29 · Branch `UBS-69-85-96-Backend-Health-Monitor` · Map of the code: [`health-reporter-overview.md` §10](./health-reporter-overview.md)

## Decisions

| # | Decision | Why |
| --- | --- | --- |
| 1 | `/readyz` uses `StreamProcessor.is_ready()`: `warmupWindow` since replica start **and** the store has data. UBS-96's earlier "since first ingest" `WarmupTracker` was dropped. | Standardise on what the downstream stream processor (UBS-88) already does, so there is one readiness definition. |
| 2 | One `StreamProcessor`, passed into `IngestionService`, is the one `/readyz` probes. | `main` built two: `/readyz` probed one that ingestion never fed, so it stayed `warming` forever. |
| 3 | `/metrics` only on the internal app (`backend.internalListen`, default `127.0.0.1:8081`); `/healthz` and `/readyz` on both apps. | FR-HLT-012 keeps `/metrics` off the public listener; the public probes stay so existing demos and probes keep working. |
| 4 | Self-metrics read ingestion / stream processor / store numbers at scrape time from their public attributes. | No edits to other owners' code and no second copy of a counter to drift. |
| 5 | UBS-85 checks dedupe **before** the rate limit. | A retry of a batch we already hold costs no quota and gets its 202. |
| 6 | UBS-85 remembers a `batchId` only **after** the batch is on the queue. | A 503 `queue_full` batch was never kept, so the agent's retry must be accepted, not swallowed as a duplicate. |
| 7 | Only `POST /telemetry/batch` is guarded. | It is the only payload with a `batchId`. |
| 8 | Dedupe/rate state is per replica, in memory. | ADR 0005; consistent-hash routing on the agent (spec 001) keeps an agent on one replica normally, so cross-replica dedupe is best-effort. |

## Not in this change

- `maxBodyBytes` / 413 (the other half of FR-ING-008).
- `rotationsDetected` is always 0 on the wire: `LogMonitor` exposes no rotation count yet.
- The agent runtime process: the e2e test and `scripts/health_monitor_demo.py` wire the health path by hand.
- Backend gzip decoding: the agent compresses bodies over 4 KiB; heartbeat-only batches stay under that.

## Open points for the team

- Garrison's `UBS-93-94-95-Alert-Event-Store` branch adds its own `services/agent_registry.py` (different API, records from the ingestion worker). Whichever of the two PRs merges second resolves the overlap; `HeartbeatMonitor` would need `agents_exceeding_threshold` / `get_record` equivalents on this registry (`stale_agents()` and `get()` already exist).
- ~~`scripts/heartbeat_receiver_stub.py` — keep or drop?~~ Dropped 2026-10-07 with `HttpHeartbeatSink`; heartbeats go through the Backend Publisher only.
