# 005 — Rule Engine, Alerting and Callbacks

Status: Draft · Owner: TBD · Last updated: 2026-07-31

Alerting lives in the **agent**, not the backend, so that alerts survive a backend outage
(`NFR-REL-003`). The backend receives alert state changes for querying and summarisation but
is not in the decision path.

## 1. Rule types

`FR-RUL-001`: Day-1 supports exactly these five rule kinds. A new kind requires a code change
and a spec update; new *instances* of a kind are configuration only.

| Kind | Evaluates | Example |
| --- | --- | --- |
| `rate` | A ratio of two counters over a window, with a minimum denominator | reject rate > 5% over 5m with ≥ 20 orders |
| `threshold` | A counter sum or gauge value over a window | parse errors > 100 in 5m |
| `latency` | An approximate percentile or max of a histogram over a window | p95 ack latency > 500ms over 5m |
| `absence` | No occurrences of a counter for a duration | zero log lines for 5m during trading hours |
| `signature` | Count of `app.error_signature` matches for a named pattern | 3+ `OutOfMemory` matches in 1m |

### 1.1 Rule definition

```yaml
rules:
  - name: HighRejectRate
    kind: rate
    numerator: orders_rejected
    denominator: [orders_acked, orders_rejected]
    window: 5m
    minSamples: 20
    operator: ">"
    threshold: 0.05
    for: 2m                  # condition must hold this long before firing
    resolveAfter: 5m         # condition must be false this long before resolving
    severity: critical
    groupBy: [instanceId]    # one alert per instance, not per symbol
    callback: true
    scheduleRef: trading-hours
    description: "Reject rate exceeded configured threshold."
    runbook: docs/specs/011-observability-and-runbooks.md#high-reject-rate
```

| ID | Requirement |
| --- | --- |
| `FR-RUL-003` | Every rule MUST declare `name`, `kind`, `window`, `severity` and `for`. `name` MUST be unique and stable — it appears in callbacks and queries. |
| `FR-RUL-004` | `for` (fire delay) and `resolveAfter` (resolve delay) MUST both be supported to prevent flapping. Defaults: `for: 1m`, `resolveAfter: 5m`. |
| `FR-RUL-005` | `groupBy` MUST default to `[instanceId]`. Allowing `symbol` in `groupBy` MUST also require `maxAlertsPerRule` (default 10) to avoid one bad session producing hundreds of alerts. |
| `FR-RUL-006` | Rate and latency rules MUST NOT fire when the sample count is below `minSamples`; they report `insufficient_data` instead. |
| `FR-RUL-007` | Rules MAY reference a named schedule (`scheduleRef`) so that absence rules do not fire outside trading hours. Schedules are defined once with a timezone (spec 010 §5). |
| `FR-RUL-008` | Thresholds MUST be reloadable via SIGHUP without restarting the agent or losing alert state. |
| `FR-RUL-009` | A malformed rule MUST be rejected at load with a clear error naming the rule; the agent MUST refuse to start on invalid config rather than silently skipping rules. |

### 1.2 Day-1 default rule set

`FR-RUL-010`: These rules ship as defaults. Values are provisional pending
[Q-5](../plan/open-questions.md).

| Rule | Kind | Condition (default) | Severity |
| --- | --- | --- | --- |
| `HighRejectRate` | rate | reject rate > 5% over 5m, ≥ 20 samples, for 2m | critical |
| `RejectSpike` | threshold | `orders_rejected` > 50 in 1m | warning |
| `CancelRejectSpike` | threshold | `cancel_rejects` > 20 in 5m | warning |
| `SessionRejects` | threshold | `session_rejects` > 5 in 5m | critical |
| `AckLatencyBreach` | latency | p95 `ack_latency_ms` > 500 over 5m, ≥ 50 samples | warning |
| `AckLatencySevere` | latency | p95 `ack_latency_ms` > 2000 over 5m, ≥ 50 samples | critical |
| `ParseErrorRate` | rate | `parse_errors` / `log_lines_read` > 1% over 5m | warning |
| `ParserBroken` | rate | same ratio > 25% over 5m | critical |
| `NoLogActivity` | absence | `log_lines_read` == 0 for 5m within trading hours | critical |
| `NoExecutions` | absence | `executions` == 0 for 15m while `orders_submitted` > 0 | warning |
| `FixSessionDown` | threshold | `logouts` ≥ 1 or `heartbeat_timeouts` ≥ 1 in 1m | critical |
| `SeqGapDetected` | threshold | `seq_gaps` > 0 in 1m | warning |
| `ClockSkew` | threshold | `clock_skew_events` > 10 in 5m | warning |
| `CallbackFailing` | threshold | `callback_failures` > 3 in 5m | warning |
| `BackendUnreachable` | threshold | `publish_failures` > 5 consecutive | warning |

`FR-RUL-030` (backend-side): The backend MUST additionally raise `AgentHeartbeatMissing` when
no heartbeat has arrived from a known agent for `missingHeartbeatThreshold` (default `60s`).
This is the one rule the backend owns, because a dead agent cannot alert on itself.

## 2. Alert lifecycle

```
        condition true            for elapsed
inactive ─────────────► pending ─────────────► firing
    ▲                      │                     │
    │ condition false      │ condition false     │ condition false
    └──────────────────────┘                     ▼
                                              resolving ──resolveAfter elapsed──► resolved ──► inactive
                                                  │
                                                  └── condition true again ──► firing (no new notification)
```

| ID | Requirement |
| --- | --- |
| `FR-RUL-011` | Alert identity (dedup key) MUST be `hash(ruleName + application + instanceId + sorted groupBy values)`. `alertId` MUST be stable for the whole lifecycle of one occurrence and MUST change for a new occurrence after resolution. |
| `FR-RUL-012` | Transitions `pending→firing` and `resolving→resolved` MUST each emit exactly one event (`alert.fired` / `alert.resolved`) and, when `callback: true`, exactly one callback attempt sequence. |
| `FR-RUL-013` | A firing alert MUST be re-notified every `renotifyInterval` (default `30m`, `0` disables) while it remains firing, with `notificationCount` incremented. |
| `FR-RUL-014` | Alert state MUST be persisted in the agent state file so a restart does not duplicate notifications (`FR-RUL-020`). |
| `FR-RUL-015` | An alert MUST carry: `alertId`, `ruleName`, `severity`, `status`, `matchedCondition` (human-readable, e.g. `rejectRate > 0.05 for 5 minutes`), `observedValue`, `threshold`, `firstObservedUtc`, `lastObservedUtc`, `instanceId`, `groupBy` values, and a `metricContext` object of at most 10 supporting numbers. |
| `FR-RUL-016` | `metricContext` MUST be built from allowlisted metrics only — never from raw log lines or FIX text. |
| `FR-RUL-017` | Global alert output MUST be capped at `maxActiveAlerts` (default 100); beyond that the agent emits one `AlertStorm` meta-alert and suppresses further new alerts until it drops below the cap. |

## 3. Callback dispatch

### 3.1 Requirements

| ID | Requirement |
| --- | --- |
| `FR-CBK-001` | Callbacks MUST be HTTPS POST to the configured Magic endpoint with `Content-Type: application/json`. Plain HTTP MUST be rejected at config load unless `allowInsecureCallback: true` is set explicitly (permitted for local development only). |
| `FR-CBK-002` | The payload MUST match §3.3 and MUST be limited to `maxCallbackBytes` (default 16 KiB). |
| `FR-CBK-003` | Requests MUST carry `X-Telemetry-Delivery-Id` (unique per attempt) and `X-Telemetry-Idempotency-Key` (= `alertId` + `status` + `notificationCount`) so Magic can deduplicate retries. |
| `FR-CBK-004` | Retries MUST use exponential backoff with jitter: base `1s`, factor 2, cap `60s`, `maxAttempts` default 5. |
| `FR-CBK-005` | Requests MUST be signed: `X-Telemetry-Signature: v1=<hex HMAC-SHA256(timestamp + "." + body)>` plus `X-Telemetry-Timestamp`. The secret comes from the environment, never from the config file or source (`NFR-SEC-004`). Verification on Magic's side MUST use a constant-time comparison. |
| `FR-CBK-006` | HTTP 2xx = delivered. 408, 429, 5xx and transport errors = retry (honouring `Retry-After` when present). Other 4xx = permanent failure, no retry, count `callback_failures` and emit `callback.failed`. |
| `FR-CBK-007` | Per-endpoint concurrency MUST be capped (`maxInflightCallbacks`, default 4) and the pending queue bounded (`callbackQueueSize`, default 256, drop-oldest with counter). |
| `FR-CBK-008` | Timeouts: connect `3s`, total `10s`, both configurable. A slow Magic endpoint MUST NOT stall the pipeline. |
| `FR-CBK-009` | Delivery outcome per attempt (status code, latency, attempt number, error class) MUST be recorded as metrics and included in the next backend publish. Response bodies MUST NOT be logged beyond the first 200 characters, and MUST be scrubbed of anything resembling a token. |
| `FR-CBK-010` | Callback failure MUST NOT prevent the alert from reaching the backend; the two paths are independent. |
| `FR-CBK-011` | A `dryRun: true` mode MUST log intended callbacks without sending, for pre-production validation. |

### 3.2 Flow

1. Rule Engine transitions an alert to `firing`.
2. An alert event is enqueued for both the Callback Dispatcher and the Backend Publisher.
3. Dispatcher signs and POSTs to the Magic endpoint.
4. On 2xx: record `delivered`, latency, and `correlationId` from the response if present.
5. On retryable failure: schedule the next attempt per backoff; leave the alert `firing`.
6. On exhaustion: mark `undelivered`, emit `callback.failed`, and let the `CallbackFailing`
   rule fire so the failure itself is visible.
7. On resolution, repeat with `status: "resolved"`.

### 3.3 Payload

```json
POST /magic/callbacks/telemetry-alerts
{
  "schemaVersion": 1,
  "alertId": "alert-1024",
  "status": "firing",
  "severity": "critical",
  "application": "Magic",
  "instanceId": "magic-prod-01",
  "agentId": "magic-agent-sg-01",
  "ruleName": "HighRejectRate",
  "summary": "Reject rate exceeded configured threshold for the last 5 minutes.",
  "matchedCondition": "rejectRate > 0.05 for 5 minutes",
  "observedValue": 0.064,
  "threshold": 0.05,
  "firstObservedUtc": "2026-06-12T03:58:00.000Z",
  "timestampUtc": "2026-06-12T04:00:00.000Z",
  "notificationCount": 1,
  "metricContext": {
    "orders_acked": 1188,
    "orders_rejected": 81,
    "topRejectReason": "OrderExceedsLimit",
    "topRejectReasonCount": 46
  },
  "runbookUrl": "https://…/011-observability-and-runbooks.md#high-reject-rate"
}
```

Expected acknowledgement:

```json
200 OK
{ "status": "received", "correlationId": "cb-5531" }
```

`FR-CBK-012`: The agent MUST treat any 2xx as success even if the body is absent or
unparseable; `correlationId` is recorded when present and never required.

The final protocol (HTTPS vs message queue, auth scheme, endpoint path) is
[Q-2](../plan/open-questions.md). The dispatcher MUST therefore sit behind a `CallbackSink`
interface with the HTTPS implementation as the Day-1 default.

## 4. Suppression and safety

| ID | Requirement |
| --- | --- |
| `FR-RUL-018` | A maintenance window (`silences` config: rule name / instance / time range) MUST suppress notification while still recording alert state. |
| `FR-RUL-019` | Rules dependent on the agent's own health (`ParseErrorRate`, `NoLogActivity`) MUST be suppressed for `startupGrace` (default `60s`) after agent start so a cold start does not page anyone. |
| `FR-RUL-021` | Dependent-alert suppression: while `NoLogActivity` is firing for an instance, trading rules for that instance MUST be suppressed, since absence of data is not absence of rejects. |
