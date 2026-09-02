# 004 — Telemetry Data Model

Status: Draft · Owner: TBD · Last updated: 2026-07-31

This is the contract between agent and backend. Changing anything here is a versioned
change (`schemaVersion`), and both sides MUST be updated together.

## 1. Identity fields

Present on every event, snapshot and heartbeat:

| Field | Type | Notes |
| --- | --- | --- |
| `schemaVersion` | int | Currently `1`. Backend rejects unknown major versions. |
| `agentId` | string | Stable per agent deployment, e.g. `magic-agent-sg-01`. MUST match the authenticated identity (`FR-ING-002`). |
| `application` | string | `Magic` for Day-1; reserved for future applications. |
| `instanceId` | string | Logical Magic instance, e.g. `magic-prod-01`. |
| `hostname` | string | Host the agent runs on. |
| `agentVersion` | string | Semver + build sha. |

## 2. Event envelope

`FR-MET-020`: Events are discrete, low-volume, operationally interesting records. High-volume
per-message data is **only** represented as metrics, never as events.

```json
{
  "schemaVersion": 1,
  "eventId": "01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60",
  "agentId": "magic-agent-sg-01",
  "application": "Magic",
  "instanceId": "magic-prod-01",
  "eventType": "fix.order_reject",
  "timestampUtc": "2026-06-12T04:00:00.123Z",
  "timeSource": "fix",
  "severity": "info",
  "dimensions": {
    "session": "MAGIC->EXCH1",
    "symbol": "ABC",
    "side": "buy",
    "ordType": "limit",
    "rejectReason": "OrderExceedsLimit"
  },
  "fields": {
    "msgType": "8",
    "execType": "Rejected",
    "ordStatus": "Rejected",
    "clOrdIdHash": "9f2c3d4e5f60a1b2",
    "orderQty": 500
  }
}
```

Rules:

- `FR-MET-021`: `eventId` MUST be a UUIDv7 so it is both unique and time-sortable.
- `FR-MET-022`: `fields` MUST contain only allowlisted values from spec 003 §4. No `text`,
  no price, no account, no raw line. A backend-side validator MUST reject unknown keys.
- `FR-MET-023`: Events MUST be rate-limited per `eventType` per instance
  (`maxEventsPerMinute`, default 600). Excess is dropped and counted, never queued
  indefinitely, so a reject storm cannot become an event storm.

### 2.1 Event type catalogue

| `eventType` | When emitted | Sampled / rate-limited |
| --- | --- | --- |
| `fix.order_reject` | ExecutionReport or OrderCancelReject indicating rejection | rate-limited |
| `fix.execution` | Trade execution — **sampled**, metrics carry the truth | sampled 1:N |
| `fix.session_reject` | 35=3 session-level reject | rate-limited |
| `fix.session_state` | Logon / Logout / heartbeat timeout | no |
| `fix.seq_gap` | Sequence gap or regression detected | rate-limited |
| `parse.error` | Parse failure, one per reason per bucket (aggregated) | aggregated |
| `log.rotated` | Rotation detected and handled | no |
| `log.truncated` | Truncation detected | no |
| `log.stalled` | No new lines for `logStallThreshold` | no |
| `app.error_signature` | Configured application error pattern matched | rate-limited |
| `agent.started` / `agent.stopping` / `agent.state_reset` | Lifecycle | no |
| `alert.fired` / `alert.resolved` | Alert state change (spec 005) | no |
| `callback.failed` | Callback exhausted retries | rate-limited |

## 3. Metric snapshot

`FR-MET-024`: One snapshot per completed 10s bucket per instance. Counters are **deltas for
that bucket**, not cumulative totals — this makes the backend's merge associative and makes
agent restarts harmless.

```json
{
  "schemaVersion": 1,
  "agentId": "magic-agent-sg-01",
  "application": "Magic",
  "instanceId": "magic-prod-01",
  "bucketStartUtc": "2026-06-12T04:00:00.000Z",
  "bucketSeconds": 10,
  "restarted": false,
  "series": [
    {
      "dimensions": { "session": "MAGIC->EXCH1", "symbol": "ABC", "side": "buy" },
      "counters": { "orders_submitted": 120, "orders_acked": 118, "orders_rejected": 2 },
      "histograms": {
        "ack_latency_ms": {
          "count": 118, "sum": 2714, "min": 4, "max": 96,
          "buckets": { "1": 0, "5": 12, "10": 60, "25": 38, "50": 6, "100": 2,
                       "250": 0, "500": 0, "1000": 0, "5000": 0, "+Inf": 0 }
        }
      }
    }
  ],
  "gauges": { "pending_orders": 340, "read_lag_ms": 120, "publish_queue_depth": 4 }
}
```

- `FR-MET-025`: Histogram bucket boundaries are fixed and shared by agent and backend:
  `1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000, +Inf` milliseconds. Percentiles are
  interpolated at query time from these buckets and MUST be reported as approximate.
- `FR-MET-026`: `sum`, `count`, `min` and `max` MUST accompany every histogram so averages
  and extremes are exact even though percentiles are not.
- `FR-MET-027`: A series with all-zero counters MUST be omitted from the snapshot.
- `FR-MET-028`: Gauges are instantaneous values at bucket close; the backend takes the latest,
  never the sum.

## 4. Metric catalogue

### 4.1 Trading counters

| Metric | Increment condition |
| --- | --- |
| `orders_submitted` | 35=D observed |
| `orders_replaced` | 35=G observed |
| `orders_cancel_requested` | 35=F observed |
| `orders_acked` | 35=8 with ExecType New for a known ClOrdID |
| `orders_rejected` | 35=8 with ExecType/OrdStatus Rejected |
| `orders_canceled` | 35=8 with ExecType Canceled |
| `orders_expired` | 35=8 with ExecType Expired |
| `cancel_rejects` | 35=9 observed |
| `session_rejects` | 35=3 observed |
| `executions` | 35=8 with ExecType Trade |
| `executed_qty` | Sum of LastQty on Trade |
| `order_qty` | Sum of OrderQty on 35=D |
| `fills_full` | ExecType Trade with LeavesQty = 0 |
| `fills_partial` | ExecType Trade with LeavesQty > 0 |

### 4.2 Protocol and session counters

`fix_messages_total`, `fix_messages_by_type` (dimension `msgType`), `seq_gaps`,
`seq_gap_messages` (sum of gap sizes), `seq_regressions`, `logons`, `logouts`,
`heartbeat_timeouts`.

### 4.3 Agent self counters

`log_lines_read`, `log_bytes_read`, `parse_errors` (dimension `reason`),
`unsupported_lines`, `unclassified_reject_text`, `unknown_enum_values`,
`clock_skew_events`, `late_dropped`, `latency_uncorrelated`, `latency_implausible`,
`dropped_stage_events` (dimension `stage`), `publish_attempts`, `publish_failures`,
`publish_rejected`, `dropped_batches`, `callback_attempts`, `callback_failures`,
`callback_retries`, `rotations_detected`, `truncations_detected`.

### 4.4 Histograms

| Histogram | Definition |
| --- | --- |
| `ack_latency_ms` | 35=D → first 35=8 for the same ClOrdID |
| `exec_latency_ms` | 35=D → first Trade ExecutionReport |
| `cancel_latency_ms` | 35=F → 35=8 Canceled or 35=9 |
| `publish_latency_ms` | Batch send duration |
| `callback_latency_ms` | Callback POST duration |
| `log_read_lag_ms` | Line timestamp → read time |

### 4.5 Derived KPIs (computed at query time, never stored)

`FR-QRY-010`: `rejectRate = orders_rejected / (orders_acked + orders_rejected)`;
`fillRate = executions / orders_acked`; `cancelRate = orders_canceled / orders_submitted`;
`parseErrorRate = parse_errors / log_lines_read`. Each MUST return `null` rather than 0 when
its denominator is below `minSampleSize` (default 20), so an idle minute never looks like a
100% reject rate.

## 5. Dimensions and cardinality

| Dimension | Values | Cap |
| --- | --- | --- |
| `application` | `Magic` | 4 |
| `instanceId` | configured | 64 per agent |
| `session` | `SENDER->TARGET` | 32 per instance |
| `symbol` | from tag 55 | 200 per instance, top-N by volume |
| `side` | buy / sell / sellShort / other | 8 |
| `ordType` | market / limit / stop / stopLimit / other | 16 |
| `msgType` | known set | 32 |
| `rejectReason` | tag 103 name or normalised label | 50 |
| `sessionRejectReason` | tag 373 name | 16 |
| `reason` (parse errors) | closed set from spec 003 §3 | 12 |
| `severity` | info / warning / critical | 3 |

`FR-MET-029`: Cardinality caps MUST be enforced at the agent with a top-N sketch per bucket;
values beyond the cap are folded into `__other__` and `metrics.cardinality_folded` is
incremented. The backend MUST additionally enforce the caps defensively (`FR-ING-006`).

`FR-MET-030`: Not every counter carries every dimension. The permitted dimension set per
metric MUST be declared in one shared table (generated into both agent and backend) so that
`orders_submitted` cannot accidentally acquire a `rejectReason` label. Series count per
instance per bucket MUST be capped at `maxSeriesPerBucket` (default 2000).

## 6. Heartbeat

```json
{
  "schemaVersion": 1,
  "agentId": "magic-agent-sg-01",
  "instanceIds": ["magic-prod-01"],
  "sentAtUtc": "2026-06-12T04:00:02.000Z",
  "agentVersion": "0.1.0+abc1234",
  "uptimeSeconds": 86400,
  "status": "healthy",
  "files": [
    { "path": "/var/log/magic/fix.log", "instanceId": "magic-prod-01",
      "offset": 918273645, "readLagMs": 120, "lastLineAtUtc": "2026-06-12T04:00:01.880Z",
      "rotationsDetected": 3, "state": "reading" }
  ],
  "parseErrorCountLast5Min": 2,
  "callbackFailuresLast5Min": 0,
  "publishQueueDepth": 4,
  "publishBufferBytes": 1048576,
  "droppedEventsLast5Min": 0,
  "activeAlertCount": 1,
  "resourceUsage": { "rssMb": 84, "cpuPercent": 1.8, "activeTasks": 42 }
}
```

`FR-HLT-002`: `status` is `healthy` | `degraded` | `unhealthy`, derived from a documented rule
set in spec 011 §2 rather than hand-set per condition.

## 7. Schema evolution

| ID | Rule |
| --- | --- |
| `FR-ING-020` | Adding an optional field or a new `eventType` is a minor change; the backend MUST ignore unknown *optional* fields but MUST reject unknown *dimension* keys. |
| `FR-ING-021` | Removing or retyping a field, or changing histogram boundaries, requires `schemaVersion` +1 and a backend that accepts both versions for one release. |
| `FR-ING-022` | The shared schema MUST live in `packages/telemetry_shared/` as Pydantic models; hand-maintaining duplicate schemas across apps is prohibited. |
