# Metrics Query API (UBS-68, UBS-91, UBS-92)

Status: Implemented · Last updated: 2026-09-29

Spec source: [007-api-contracts.md §3](../specs/007-api-contracts.md), [006-backend.md §5](../specs/006-backend.md)

## Endpoint

`POST /telemetry/query/metrics`

## Example request

```json
{
  "timeRange": { "fromUtc": "2026-06-12T03:30:00Z", "toUtc": "2026-06-12T04:00:00Z" },
  "filters": {
    "application": "Magic",
    "instanceId": "magic-prod-01"
  },
  "groupBy": ["rejectReason"],
  "metrics": ["orders", "executions", "rejections", "rejectRate"],
  "topK": 5,
  "series": false
}
```

Relative time range:

```json
{ "timeRange": { "last": "30m" }, "metrics": ["orders"] }
```

## Example response

```json
{
  "queryId": "q-a1b2c3d4",
  "evaluatedAtUtc": "2026-06-12T04:00:05.120Z",
  "effectiveTimeRange": {
    "fromUtc": "2026-06-12T03:30:00Z",
    "toUtc": "2026-06-12T04:00:00Z"
  },
  "interpretation": {
    "metrics": ["orders_submitted", "executions", "orders_rejected", "rejectRate"],
    "groupBy": ["rejectReason"],
    "filters": { "application": "Magic", "instanceId": "magic-prod-01" },
    "clamped": []
  },
  "totals": {
    "orders": 1250,
    "executions": 1188,
    "rejections": 62,
    "rejectRate": 0.0496
  },
  "groups": [
    {
      "dimensions": { "rejectReason": "OrderExceedsLimit" },
      "counters": { "rejections": 35 }
    }
  ],
  "truncated": false,
  "dataCompleteness": {
    "agentsExpected": 1,
    "agentsReporting": 1,
    "staleAgents": [],
    "restartedBuckets": 0,
    "droppedBatchesReported": 0,
    "confidence": "complete",
    "failedPeers": []
  }
}
```

## Metric and dimension aliases

| Request alias | Canonical |
| --- | --- |
| `orders` | `orders_submitted` |
| `rejections` | `orders_rejected` |
| `rejectRate` | derived indicator |
| `sessionId` | stored as `session_id` |
| `rejectReason` | stored as `reject_reason` |

## Operational limits (UBS-91)

| Limit | Default | Violation |
| --- | --- | --- |
| `maxRangeSeconds` | 21600 (6h) | `400 invalid_time_range` |
| `maxGroups` | 500 | `400 invalid_field` |
| `maxSeriesPoints` | 1500 | `400 invalid_field` |
| `queryTimeout` | 3s | `504 query_timeout` |

Requests outside the store retention window return `400 invalid_time_range` naming the available range — never an empty result that reads as “no problems.”

## Multi-replica mode (UBS-92)

Configure via `QueryConfig`:

- `queryMode: colocated` (default) — local store only; load balancer hashes on `instanceId`.
- `queryMode: fanout` — fan out to `replicaRegistry` peers, merge bucket-wise, degrade to `confidence: partial` on peer failure.

Internal peer requests carry `X-Replica-Query: 1` to prevent fan-out loops.

## Code locations

| Component | Path |
| --- | --- |
| Request/response models | `packages/telemetry_shared/src/telemetry_shared/models/metrics_query.py` |
| Alias tables | `packages/telemetry_shared/src/telemetry_shared/query/aliases.py` |
| Query engine | `apps/backend/src/telemetry_backend/services/query_engine.py` |
| Replica fan-out | `apps/backend/src/telemetry_backend/services/replica_fanout.py` |
| HTTP route | `apps/backend/src/telemetry_backend/main.py` |

## Verified by

- `tests/unit/backend/services/test_UBS_68_query_engine.py`
- `tests/unit/backend/api/test_UBS_68_metrics_query.py`
- `tests/unit/backend/services/test_UBS_91_query_limits.py`
- `tests/unit/backend/services/test_UBS_92_replica_fanout.py`
