# 007 — API Contracts

Status: Draft · Owner: TBD · Last updated: 2026-10-16

Base path: `/telemetry`. All requests and responses are JSON, UTF-8. All timestamps are
UTC ISO-8601 with milliseconds. This spec is the source for the OpenAPI document
generated from FastAPI; where they disagree, this spec is wrong and MUST be corrected.

## 1. Conventions

| ID           | Requirement                                                                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FR-QRY-030` | Every request MUST accept an optional `X-Request-Id`; if absent the backend generates one. It MUST be echoed in the response and in logs.               |
| `FR-QRY-031` | Errors MUST use one shape (§7). No endpoint returns a bare string or a stack trace.                                                                     |
| `FR-QRY-032` | Unknown top-level request fields MUST be rejected with `400 invalid_field` (strict models), so typos in a query never silently return the wrong answer. |
| `FR-QRY-033` | All list responses MUST be explicitly bounded and MUST report `truncated: true` when a cap was applied.                                                 |

Production authentication target (final identity/tenant arrangements remain Q-3):

- Agent → backend: `Authorization: Bearer <agent token>` or mutual TLS. `FR-ING-002`.
- Human/tool → backend: OAuth 2.0 bearer token from Entra ID, scope `Telemetry.Read`.
- Copilot/Teams → backend: same, via the app registration in
  [Q-3](../plan/open-questions.md).

For the local synthetic-data POC, custom backend token enforcement is deferred (spec 009
§3.3). The Teams/Copilot adapter may call these APIs without a backend user token. The
selected Microsoft integration still requires its platform registration, credentials and
incoming-message validation. Platform setup and local-server reachability are part of
the real Teams demonstration; they do not imply per-user backend Entra enforcement.

## 2. Ingestion

### 2.1 `POST /telemetry/batch` (primary agent path)

Ingestion accepts `Content-Encoding: gzip` (`FR-PUB-002`) as well as uncompressed JSON.
`ingest.maxBodyBytes` (default 8 MiB) bounds both wire bytes and decompressed bytes;
either overflow returns `413 body_too_large`. Invalid/truncated gzip returns
`400 invalid_encoding`. Unsupported content encodings return `415 unsupported_encoding`.

```json
{
  "schemaVersion": 1,
  "batchId": "01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60",
  "batchSeq": 4821,
  "agentId": "magic-agent-sg-01",
  "application": "Magic",
  "sentAtUtc": "2026-06-12T04:00:10.000Z",
  "snapshots": [/* spec 004 §3 */],
  "events": [/* spec 004 §2 */],
  "alerts": [/* spec 005 §2 */],
  "heartbeat": {/* spec 004 §6 */}
}
```

```json
202 Accepted
{
  "status": "accepted",
  "batchId": "01920f3a-1c2d-7f00-8a1b-9f2c3d4e5f60",
  "receivedAtUtc": "2026-06-12T04:00:10.180Z",
  "duplicate": false,
  "accepted": { "snapshots": 6, "events": 3, "alerts": 1 },
  "rejected": []
}
```

Partial rejection:

```json
202 Accepted
{
  "status": "partially_accepted",
  "accepted": { "snapshots": 5, "events": 3, "alerts": 1 },
  "rejected": [
    { "kind": "snapshot", "index": 5, "code": "bucket_too_old",
      "detail": "bucketStartUtc is 2h12m old; limit is 1h" }
  ]
}
```

| Status    | Meaning                            | Agent behaviour                                           |
| --------- | ---------------------------------- | --------------------------------------------------------- |
| 202       | Accepted (possibly partial)        | Drop batch from buffer                                    |
| 400       | Schema invalid for the whole batch | Drop, count `publish.rejected`, log once                  |
| 401 / 403 | Auth failure or agentId mismatch   | Stop publishing, alert `BackendUnreachable`, retry slowly |
| 413       | Body too large                     | Split batch, halve `maxBatchItems`                        |
| 429       | Rate limited                       | Honour `Retry-After`                                      |
| 503       | Ingest queue full                  | Back off and buffer                                       |

### 2.2 `POST /telemetry/events`

Accepts `{ "events": [...] }` for callers that emit only events. Same response shape.
Retained because it matches the original design sketch and is convenient for testing.

### 2.3 `POST /telemetry/heartbeat`

Accepts one heartbeat document (spec 004 §6) for heartbeat-only callers. The configured
agent uses `POST /telemetry/batch` even for a heartbeat-only publish.

## 3. `POST /telemetry/query/metrics`

Request:

```json
{
  "timeRange": { "fromUtc": "2026-06-12T03:30:00Z", "toUtc": "2026-06-12T04:00:00Z" },
  "filters": {
    "application": "Magic",
    "instanceId": "magic-prod-01",
    "session": ["MAGIC->EXCH1", "MAGIC->EXCH2"]
  },
  "groupBy": ["rejectReason"],
  "metrics": ["orders", "executions", "rejections", "rejectRate"],
  "percentiles": { "ack_latency_ms": [50, 95, 99] },
  "topK": 5,
  "series": false,
  "step": "1m"
}
```

- `timeRange` MAY instead be `{ "last": "30m" }`. Exactly one form is allowed.
- Metric aliases accepted for convenience: `orders` → `orders_submitted`, `rejections` →
  `orders_rejected`, `executions` → `executions`. Aliases MUST be resolved in one shared
  table and echoed back under `interpretation`. `FR-QRY-034`

Response:

```json
200 OK
{
  "queryId": "q-8f21",
  "evaluatedAtUtc": "2026-06-12T04:00:05.120Z",
  "effectiveTimeRange": { "fromUtc": "2026-06-12T03:30:00Z", "toUtc": "2026-06-12T04:00:00Z" },
  "interpretation": {
    "metrics": ["orders_submitted", "executions", "orders_rejected", "rejectRate"],
    "groupBy": ["rejectReason"],
    "filters": { "application": "Magic", "instanceId": "magic-prod-01" },
    "clamped": []
  },
  "totals": {
    "orders_submitted": 1250,
    "executions": 1188,
    "orders_rejected": 62,
    "rejectRate": 0.0496
  },
  "latency": {
    "ack_latency_ms": { "p50": 11, "p95": 42, "p99": 96, "avg": 14.2,
                        "count": 1188, "approximate": true }
  },
  "groups": [
    { "dimensions": { "rejectReason": "OrderExceedsLimit" }, "counters": { "orders_rejected": 35 } },
    { "dimensions": { "rejectReason": "UnknownSymbol" },     "counters": { "orders_rejected": 18 } },
    { "dimensions": { "rejectReason": "__other__" },         "counters": { "orders_rejected": 9 } }
  ],
  "truncated": false,
  "dataCompleteness": {
    "agentsExpected": 1, "agentsReporting": 1, "staleAgents": [],
    "restartedBuckets": 0, "confidence": "complete"
  }
}
```

With `series: true`, `groups[].points` is added:

```json
"points": [
  { "tsUtc": "2026-06-12T03:30:00Z", "orders_rejected": 4 },
  { "tsUtc": "2026-06-12T03:31:00Z", "orders_rejected": null }
]
```

`FR-QRY-035`: `null` means "no data for this step", `0` means "data present, count
zero". Conflating the two is a defect.

### 3.1 `POST /telemetry/query/reject-reason-trends` (UBS-27)

`FR-QRY-040`: Identifies reject reasons that are increasing: each `rejectReason`'s
`orders_rejected` count in the latest `window` against the preceding window of equal
length. Built on the §3 query path, so retention, filters and fan-out behave the same.

Request (all optional): `window` (default `"15m"`), `threshold` (default `0.5`, i.e.
more than +50%), `minOccurrences` (default `5`, in the latest window), `filters` (as
§3).

A reason is `increasing` when `(current − previous) / previous > threshold`, `emerging`
when it was absent before, `decreasing` below −10%, otherwise `steady`; both rising
states need `minOccurrences`. `increasing[]` lists the rising reasons, `emerging` first,
then largest rise first; `reasons[]` lists every reason. When the store does not yet
cover the whole preceding window, `previousWindowComplete` is `false`, nothing is
flagged and `caveats` says why.

## 4. Alerts

### 4.1 `GET /telemetry/alerts`

Query parameters: `status` (`active` | `resolved` | `all`, default `active`),
`application`, `instanceId`, `ruleName`, `severity`, `since`, `limit` (default 100, max
500).

```json
200 OK
{
  "alerts": [
    {
      "alertId": "alert-1024",
      "source": "agent",
      "agentId": "magic-agent-sg-01",
      "application": "Magic",
      "instanceId": "magic-prod-01",
      "ruleName": "HighRejectRate",
      "severity": "critical",
      "status": "active",
      "matchedCondition": "rejectRate > 0.05 for 5 minutes",
      "observedValue": 0.064,
      "threshold": 0.05,
      "firstObservedUtc": "2026-06-12T03:58:00.000Z",
      "lastObservedUtc": "2026-06-12T04:00:00.000Z",
      "resolvedAtUtc": null,
      "notificationCount": 1,
      "delivery": { "status": "delivered", "attempts": 1, "lastAttemptUtc": "2026-06-12T03:58:01.000Z",
                    "correlationId": "cb-5531" },
      "metricContext": { "orders_acked": 1188, "orders_rejected": 81,
                         "topRejectReason": "OrderExceedsLimit" },
      "runbookUrl": "https://…#high-reject-rate"
    }
  ],
  "counts": { "active": 1, "critical": 1, "warning": 0 },
  "truncated": false
}
```

### 4.2 `GET /telemetry/alerts/{alertId}`

Returns one alert plus its state transition history (bounded to the last 50
transitions). `404` with `code: "not_found"` if unknown or evicted.

## 5. Health

### 5.1 `GET /telemetry/health/agents`

```json
200 OK
{
  "agents": [
    { "agentId": "magic-agent-sg-01", "status": "healthy",
      "instanceIds": ["magic-prod-01"],
      "lastHeartbeatUtc": "2026-06-12T04:00:02.000Z", "heartbeatAgeMs": 3100 }
  ],
  "counts": { "healthy": 1, "degraded": 0, "unhealthy": 0, "missing": 0 }
}
```

### 5.2 `GET /telemetry/health/agents/{agentId}`

```json
200 OK
{
  "agentId": "magic-agent-sg-01",
  "status": "healthy",
  "lastHeartbeatUtc": "2026-06-12T04:00:02.000Z",
  "agentVersion": "0.1.0+abc1234",
  "uptimeSeconds": 86400,
  "logReadLagMs": 120,
  "parseErrorCountLast5Min": 2,
  "callbackFailuresLast5Min": 0,
  "publishQueueDepth": 4,
  "droppedEventsLast5Min": 0,
  "files": [
    { "path": "/var/log/magic/fix.log", "instanceId": "magic-prod-01",
      "readLagMs": 120, "state": "reading", "rotationsDetected": 3 }
  ],
  "resourceUsage": { "rssMb": 84, "cpuPercent": 1.8 }
}
```

`FR-HLT-011`: File paths are the only path-like data the API returns. They are
configured values, never user input, and MUST NOT be interpolated into any filesystem
operation on the backend.

### 5.3 `GET /healthz`, `GET /readyz`, `GET /metrics`

Unauthenticated on the internal listener only (`FR-HLT-012`); `/metrics` MUST NOT be
exposed on a public listener.

## 6. Natural language

### 6.1 `POST /telemetry/nl/query`

```json
{
  "question": "Why are Magic orders rejecting in the last 30 minutes?",
  "context": {
    "defaultApplication": "Magic",
    "userTimezone": "Asia/Singapore",
    "audience": "technical"
  }
}
```

```json
200 OK
{
  "answer": "Magic recorded 62 rejected orders in the last 30 minutes out of 1,250 submitted (5.0% reject rate). The largest category was OrderExceedsLimit with 35 occurrences, followed by UnknownSymbol with 18. The HighRejectRate alert is still active for magic-prod-01.",
  "intent": "rejection_summary",
  "confidence": 0.94,
  "interpretedQuery": {
    "intent": "rejection_summary",
    "timeRange": { "last": "30m" },
    "filters": { "application": "Magic" },
    "groupBy": ["rejectReason", "instanceId"],
    "metrics": ["orders_submitted", "orders_rejected", "rejectRate"]
  },
  "data": { "…": "the structured metrics response used to build the answer" },
  "citations": [
    { "type": "metrics_query", "queryId": "q-8f21" },
    { "type": "alert", "alertId": "alert-1024" }
  ],
  "caveats": ["Percentiles are approximate.", "Data covers 1 of 1 expected agents."],
  "chartRows": [{ "name": "OrderExceedsLimit", "value": 35 }],
  "alertSummaries": [{
    "alertId": "alert-1024",
    "ruleName": "HighRejectRate",
    "severity": "critical",
    "status": "firing",
    "instanceId": "magic-prod-01",
    "delivery": { "status": "delivered", "attempts": 1 }
  }]
}
```

`FR-NLQ-020`: The response MUST always include `interpretedQuery` and `data`. An answer
the user cannot verify against numbers is not acceptable for operational use.

When the question can't be answered as a telemetry query, the response is a
`clarification` instead (`FR-NLQ-003`, `FR-NLQ-030`). It carries no numbers, so
`interpretedQuery` and `data` are absent:

```json
200 OK
{
  "kind": "clarification",
  "message": "Hi! I can answer questions about Magic telemetry. Try one of these.",
  "supportedIntents": ["rejection_summary", "order_flow_summary", "latency_summary"],
  "details": [],
  "reason": "greeting",
  "suggestedQuestions": ["How is Magic doing today?", "Is Magic slow right now?"]
}
```

| Field                | Meaning                                                                                                                                                                                               |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reason`             | `clarify` (default: no intent matched), `greeting`, `help`, `out_of_scope` (the question isn't about telemetry), or `llm_unavailable` (the LLM timed out or couldn't be reached and no rule matched). |
| `suggestedQuestions` | Example questions from the intent catalogue. Surfaces may render them as buttons that re-ask the question. Empty if none apply.                                                                       |

Both fields are optional and additive. Clients that ignore them still get `message` and
`supportedIntents`.

### 6.2 `GET /telemetry/nl/intents`

Returns the intent catalogue (spec 008 §2) with example questions. Used to build Copilot
prompt grounding and to keep documentation honest.

## 7. Error shape

```json
400 Bad Request
{
  "error": {
    "code": "invalid_time_range",
    "message": "timeRange exceeds the maximum queryable window.",
    "details": [ { "field": "timeRange", "issue": "range is 12h; maxRangeSeconds is 21600" } ],
    "requestId": "req-4d2a"
  }
}
```

Closed set of codes: `invalid_field`, `invalid_time_range`, `invalid_filter`,
`unknown_metric`, `unknown_dimension`, `unsupported_schema_version`, `bucket_too_old`,
`cardinality_exceeded`, `rate_limited`, `queue_full`, `unauthorized`, `forbidden`,
`agent_id_mismatch`, `not_found`, `query_timeout`, `internal_error`, `body_too_large`,
`invalid_encoding`, `unsupported_encoding`.

| ID           | Requirement                                                                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `FR-QRY-036` | Error messages MUST NOT echo raw request content beyond the field name and a bounded, escaped excerpt (max 100 chars).                      |
| `FR-QRY-037` | `internal_error` MUST return `requestId` and nothing else about the failure; details go to server logs.                                     |
| `FR-QRY-038` | Any string from a request that appears in an error message or is rendered into HTML/Markdown/Teams output MUST be escaped for that context. |

## 8. Versioning

`FR-QRY-039`: Breaking API changes get a new path prefix (`/telemetry/v2/...`). The
`schemaVersion` field governs the ingestion payload contract; the path governs the HTTP
contract. Both are needed because agents and query clients upgrade independently.
