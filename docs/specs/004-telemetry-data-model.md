# 004 — Telemetry Data Model

Status: Draft · Owner: TBD · Last updated: 2026-10-16

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
- `FR-MET-022`: FIX `fields` MUST contain only allowlisted values from spec 003 §4.
  Derived operational metadata is restricted to §2.3 below. No `text`, no price,
  no account, no raw line. Agent and backend share the compile-time field allowlist
  in `telemetry_shared.events`; the backend MUST reject unknown keys.
- `FR-MET-023`: Events MUST be rate-limited per `eventType` per instance
  (`maxEventsPerMinute`, default 600). Excess is dropped and counted, never queued
  indefinitely, so a reject storm cannot become an event storm.

### 2.1 Event type catalogue

| `eventType` | When emitted | Sampled / rate-limited |
| --- | --- | --- |
| `fix.order_reject` | ExecutionReport or OrderCancelReject indicating rejection | rate-limited |
| `fix.execution` | Trade execution — **sampled**, metrics carry the truth | sampled 1:N, rate-limited |
| `fix.session_reject` | 35=3 session-level reject | rate-limited |
| `fix.session_state` | Logon / Logout / heartbeat timeout | rate-limited defensively |
| `fix.seq_gap` | Sequence gap or regression detected | rate-limited |
| `parse.error` | Parse failure, one per reason per bucket (aggregated) | aggregated, rate-limited |
| `log.rotated` | Rotation detected and handled | rate-limited defensively |
| `log.truncated` | Truncation detected | rate-limited defensively |
| `log.stalled` | No new lines for `logStallThreshold` | rate-limited defensively |
| `app.error_signature` | Configured application pattern matched at any N/I/W/E/F level; no alert rule required | rate-limited |
| `app.error` | E/F application lines summarised by level over a completed bucket, whether or not a signature matched | aggregated, rate-limited |
| `agent.started` / `agent.stopping` / `agent.state_reset` | Lifecycle | rate-limited defensively |
| `alert.fired` / `alert.resolved` | Alert state change (spec 005) | rate-limited defensively |
| `callback.failed` | Terminal callback failure (permanent HTTP failure, exhausted retries, oversized payload) | rate-limited |

### 2.2 Event classes

Every `eventType` belongs to one class. The class is fixed by the `eventType` prefix and is
not a separate field.

| Class | Prefixes | Source |
| --- | --- | --- |
| **System event** | `host.*`, `agent.*`, `log.*` | The host, Magic's process, the agent itself |
| **Application event** | `fix.*`, `app.*`, `parse.*` | What Magic logs or trades |
| **Alert event** | `alert.*`, `callback.*` | The Rule Engine and Callback Dispatcher, about either class |

Host conditions (disk, memory, Magic process liveness) are not separate event types. They
are gauges (§4.7) that rules turn into `alert.fired` / `alert.resolved` (spec 005 §1.2).
That is the event the agent pushes.

### 2.3 Derived operational metadata

UBS-117 publishes observations independently of alert rules. `app.error` is a
summary (default 10 seconds, matching `publish.metricsBucketSeconds`), with only
`level: E` / `level: F` and a count. E maps to event severity `warning`, F to
`critical`; this mapping does **not** fire an alert. All N/I/W/E/F levels contribute
to metrics. A configured signature can emit `app.error_signature` at any level:
N/I map to `info`, W/E to `warning`, and F to `critical`, with the original level
retained as a dimension. Signatures need no matching alert rule. Signature events
provide additional classification and MUST NOT be added
to `app.error` counts when calculating error totals. Metrics remain the counting
source of truth: events are sampled/rate-limited and have bounded retention.
Summaries use the active processing bucket; backlogged lines arriving after their
read-time bucket closed contribute to that active bucket. Metric bucketing remains
unchanged, so event summaries describe detection time rather than exact source time.
Application signature timestamps use the agent's read time, and summary timestamps
use its processing bucket; both declare `timeSource: agent`.

The `app.error` summary is a deliberate extension to the original UBS-117 catalogue
to retain the sponsor's unclassified error/failure observations. It produces at most
one summary per E/F level per bucket; routine unmatched N/I/W lines remain metrics
under FR-MET-020. It adds no alert rule or notification. UBS-128 owns generic
F-level alerting, and UBS-129/130 own host/process detection.

| Event type | Additional allowed fields | Meaning |
| --- | --- | --- |
| `app.error`, `parse.error` | `count`, `bucketSeconds` | Summary count and bucket width; timestamp is bucket start |
| `fix.seq_gap` | `expectedSeqNum`, `gapSize`, `isRegression` | Derived sequence comparison; `seqNum` is the observed number |
| `fix.session_state` | `state`, `silentSeconds` | `logon`, `logout`, or `heartbeat_timeout`; silence duration for timeout only |
| `fix.execution` | `sampleEvery` | One out of every N observed trades; never extrapolate exact totals from samples |
| `alert.fired`, `alert.resolved` | `alertId`, `ruleName`, `status` | Reference to the existing alert record; no copied message text |
| `log.rotated`, `log.truncated`, `log.stalled` | `sourceIndex` | Zero-based configured monitor order; no filesystem path |
| `agent.state_reset` | `reason` | Closed values: `missing`, `corrupt`, `unreadable` |
| `callback.failed` | `alertId`, `reason`, `attempts`, `httpStatus` | Closed reasons: `payload_too_large`, `permanent_http_failure`, `retries_exhausted`; status omitted for transport errors/no request |

`log.stalled` reports one observation after the configured idle threshold, rearmed
by the next complete log line. It is not proof of an application outage or an
automatic alert. Runtime `agent.state_reset` currently reports offset-zero recovery;
the end-of-file recovery policy in spec 002 FR-LOG-022 remains a separate gap.

Alert observations mirror state/severity changes from AlertRouter. Cooldown
reminders continue on the existing alert/callback path but do not create another
observation. A severity change keeps the same `alertId`; it is not a second incident.
The mirror remembers the most recent 4096 alert IDs per instance; reminders for
an evicted ID can appear again. Consumers use `alertId` for incident counting.

The publisher's existing memory buffer/retry mechanism carries events. No separate
event bus, event database or MCP ingestion path is introduced. Rate limits use a
rolling monotonic 60-second window per event type per instance (including lifecycle
and alert observations defensively). Excess increments `events_rate_limited` and
the heartbeat's `droppedEventsLast5Min`. Metric/alert processing continues.

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
  "gauges": { "pending_orders": 340, "read_lag_ms": 120, "publish_queue_depth": 4,
              "consecutive_publish_failures": 0 }
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
- `FR-MET-031`: `consecutive_publish_failures` is the number of publish attempts that have
  failed in a row since the last successful batch commit. It MUST reset to 0 on commit, and
  MUST be `null` — never 0 — when the agent has no Backend Publisher configured, so an agent
  that cannot report on publishing is never mistaken for one that is publishing cleanly. It
  backs `BackendUnreachable` (spec 005 §1.2); the `publish_failures` counter in §4.3 remains
  the cumulative windowed measure for trends and queries, and is not what that rule reads.

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

- `FR-MET-032`: `heartbeat_timeouts` counts FIX sessions that have gone silent for longer
  than `health.sessionHeartbeatTimeout` (default `60s`, mirroring the backend's
  `missingHeartbeatThreshold` in FR-RUL-030 so both ends agree on what a missing heartbeat
  is). *Any* message refreshes a session, not only `35=0` — FIX requires a Heartbeat only
  when the session is otherwise idle, so a session busy with orders is demonstrably alive.
  Each silence MUST be counted **once**, latched until the session speaks again: the
  detector runs on a periodic tick, and re-counting every tick would scale a single dead
  session with outage duration in a counter `FixSessionDown` reads at `>= 1` critical.
  A session that sends `35=5` Logout MUST be dropped rather than timed out, or one orderly
  shutdown would post both `logouts` and `heartbeat_timeouts` for the same event.
  Producer: `parser.fix.session_tracker.SessionHeartbeatTracker` (UBS-106).

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

### 4.6 Application.log counters

`app_log_lines` (dimensions `instanceId`, `level`), `app_log_errors` (dimensions
`instanceId`, `level`, `component`), and `app_error_signatures` (dimensions `instanceId`,
`errorSignature`).

`FR-MET-033`: The POC uses N/I/W/E/F. Failure is more severe than error:

- `[F]` failure is the most severe.
- `[E]` error is less severe than failure.

The proposed C level was withdrawn in UBS-127; UBS-128 implements an F-only default
alert. `app_log_errors` MUST count E and F lines, and the `level` dimension MUST let a rule
select one level (spec 005 §1.2). `[N]`, `[W]` and `[I]` lines count only toward
`app_log_lines`.

### 4.7 Host gauges

`FR-MET-034`: The agent MUST report these host gauges, sampled by the Host Monitor
(spec 002 §7.1) and carried in `gauges` at bucket close (`FR-MET-028`):

| Gauge | Value | Dimensions |
| --- | --- | --- |
| `host_disk_used_ratio` | Used ÷ total bytes, `0.0`–`1.0`, for each configured path's filesystem | `instanceId`, `mount` |
| `host_memory_used_ratio` | Used ÷ total physical memory, `0.0`–`1.0` | `instanceId` |
| `magic_process_up` | `1` if the configured Magic process is running, else `0` | `instanceId` |

A gauge the agent cannot read MUST be omitted, never reported as `0`. A rule then reports
`insufficient_data` instead of a false "disk empty" or "Magic down" (the same reasoning as
`FR-MET-031`).

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
| `level` | Application.log level, closed set `[NWEIF]` (`FR-MET-033`) | 5 |
| `mount` | Host filesystem path from `host.diskPaths` | 8 |
| `component` | Application.log component, free text | 50 per instance, `__other__` beyond cap |
| `errorSignature` | Application.log error signature, free text | 50 per instance, `__other__` beyond cap |

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
