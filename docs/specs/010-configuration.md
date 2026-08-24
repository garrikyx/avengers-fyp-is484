# 010 — Configuration Reference

Status: Draft · Owner: TBD · Last updated: 2026-07-31

Precedence: command-line flag > environment variable > config file > built-in default
(`FR-CFG-001`). Environment variables are prefixed `MAGIC_TELEMETRY_` and map to keys by
upper-snake-casing the path (`agent.publishInterval` → `MAGIC_TELEMETRY_AGENT_PUBLISHINTERVAL`).

`NFR-CFG-004`: the defaults below are normative. A test MUST render the built-in defaults and
diff them against this document's values.

## 1. Agent configuration

```yaml
agent:
  agentId: magic-agent-sg-01        # required, must match backend-registered identity
  application: Magic
  stateDir: /var/lib/magic-telemetry # offsets + alert state only
  gomaxprocs: 0                      # 0 => min(2, NumCPU)
  memoryLimitMb: 150
  metricsListen: 127.0.0.1:9464      # local /metrics; loopback only by default
  logLevel: info                     # debug | info | warn | error
  shutdownGrace: 5s
  startupGrace: 60s

logs:
  - name: fix
    instanceId: magic-prod-01
    paths: ["/var/log/magic/fix*.log"]     # globs allowed
    allowedRoots: ["/var/log/magic"]       # NFR-SEC-015
    logType: fix
    parsers: [fix]
    mode: tail                              # tail | interval
    pollInterval: 1s                        # interval mode, and tail fallback poll
    discoveryInterval: 30s
    startAt: end                            # end | beginning (first run only)
    encoding: utf-8                         # utf-8 | latin-1
    fixDelimiter: auto                      # auto | soh | pipe | caret | semicolon
    validateChecksum: false
    maxJoinLines: 4
    maxLineBytes: 65536
    partialLineTimeout: 2s           # default is max(2s, 2 x pollInterval), see §1.1
    rotationDrainTimeout: 5s
    logStallThreshold: 5m
  - name: application
    instanceId: magic-prod-01
    paths: ["/var/log/magic/application.log"]
    allowedRoots: ["/var/log/magic"]
    logType: app
    parsers: [applog]
    mode: interval
    pollInterval: 5s

parsing:
  maxClockSkew: 5m
  maxRejectReasonLabels: 50
  rejectReasonPatterns:              # FR-PRS-022, applied to normalised tag 58
    - label: price_exceeds_limit
      match: "price.*(exceeds|outside).*limit"
    - label: unknown_symbol
      match: "unknown (symbol|instrument)"
    - label: market_closed
      match: "market (is )?closed|exchange closed"
    - label: risk_limit_breach
      match: "risk limit|credit limit|position limit"
    - label: duplicate_order
      match: "duplicate (order|clordid)"
    - label: throttled
      match: "throttl|rate limit|too many"
  errorSignatures:                   # FR-RUL-001 signature rules, app logs only
    - label: out_of_memory
      match: "OutOfMemoryError|std::bad_alloc"
    - label: db_connection_lost
      match: "connection (lost|refused).*(db|database)"

metrics:
  bucketSeconds: 10
  localRetentionBuckets: 360         # 1h
  maxSeriesPerBucket: 2000
  maxSymbols: 200
  maxPendingOrders: 100000
  pendingOrderTtl: 5m
  maxPlausibleLatency: 60s
  minSampleSize: 20

publish:
  endpoint: https://telemetry.internal.example/telemetry/batch
  interval: 10s
  timeout: 10s
  maxBatchItems: 500
  compressThreshold: 4096
  bufferBytes: 67108864              # 64 MiB, memory only
  bufferMaxAge: 15m
  retry: { base: 1s, factor: 2, cap: 60s, jitter: 0.2 }
  tls: { minVersion: "1.2", caFile: "", clientCertFile: "", clientKeyFile: "" }
  # token comes from MAGIC_TELEMETRY_PUBLISH_TOKEN (NFR-SEC-004)

heartbeat:
  interval: 10s

callbacks:
  enabled: true
  endpoint: https://magic-host.internal.example/magic/callbacks/telemetry-alerts
  allowInsecureCallback: false
  dryRun: false
  connectTimeout: 3s
  timeout: 10s
  maxAttempts: 5
  retry: { base: 1s, factor: 2, cap: 60s, jitter: 0.2 }
  maxInflight: 4
  queueSize: 256
  maxBytes: 16384
  # HMAC secret from MAGIC_TELEMETRY_CALLBACK_SECRET

alerting:
  evaluationInterval: 5s
  renotifyInterval: 30m
  maxActiveAlerts: 100
  maxAlertsPerRule: 10
  defaultFor: 1m
  defaultResolveAfter: 5m
  schedules:
    - name: trading-hours
      timezone: Asia/Singapore
      days: [Mon, Tue, Wed, Thu, Fri]
      from: "08:30"
      to: "17:30"
  silences: []
  rules: []                          # see spec 005 §1.2 for the shipped defaults
```

### 1.1 Notes on selected keys

| Key | Why it matters |
| --- | --- |
| `logs[].startAt` | `beginning` on a large existing file will replay it; only use for backfill testing. |
| `logs[].allowedRoots` | Enforces `NFR-SEC-015`; a glob resolving outside these roots is a startup error. |
| `parsing.rejectReasonPatterns` | The only way rejection text becomes a queryable label. Order matters: first match wins. |
| `publish.bufferBytes` | Directly bounds how long a backend outage is survivable at a given rate. Document the implied minutes in the runbook. |
| `metrics.minSampleSize` | Prevents low-volume periods from producing 100% reject rates. |
| `logs[].partialLineTimeout` | Defaults to `max(2s, 2 × pollInterval)` and MUST exceed `pollInterval` (`FR-CFG-004`). A timeout shorter than a poll cycle flushes *every* line that spans two writes as two lines, turning a correct log into a stream of malformed ones. The flat 2s default is correct for tail mode but not for interval mode's slower poll, hence the derivation. |
| `callbacks.dryRun` | Required for pre-production validation before Magic's endpoint exists. |

## 2. Backend configuration

```yaml
backend:
  listen: 0.0.0.0:8080
  internalListen: 127.0.0.1:8081     # /metrics, /healthz, /readyz  (FR-HLT-012)
  logLevel: info
  workers: 4

ingest:
  maxBodyBytes: 8388608              # 8 MiB
  maxBatchesPerMinutePerAgent: 30
  dedupeCacheSize: 10000
  dedupeTtl: 30m
  queueSize: 10000                   # 503 when full (FR-ING-009)
  maxBucketAge: 1h
  schemaVersions: [1]

store:
  retentionWindow: 6h                # max 24h
  rollups: ["1m", "5m"]
  memoryLimitMb: 4096
  memoryWarnPercent: 75
  memoryShedPercent: 90
  warmupWindow: 2m
  maxInstances: 100
  recentAlertLimit: 500

query:
  timeout: 3s
  maxRangeSeconds: 21600
  maxGroups: 500
  maxSeriesPoints: 1500
  minSampleSize: 20
  mode: fanout                       # fanout | colocated  (NFR-SCA-004)
  replicaRegistry: []                # peer URLs when mode=fanout
  fanoutTimeout: 1500ms

alerting:
  missingHeartbeatThreshold: 60s

nl:
  enabled: true
  maxQuestionChars: 500
  perUserRateLimitPerMinute: 20
  llm:
    provider: azure-openai
    deployment: gpt-4o-mini
    timeout: 2s
    maxRetries: 1
    structuredOutput: true           # FR-NLQ-007
  defaultTimezone: Asia/Singapore
  defaultTimeRange: 30m

auth:
  agentAuth: bearer                  # bearer | mtls
  userAuth: entra
  entra: { tenantId: "", audience: "", requiredScope: "Telemetry.Read" }
```

## 3. Required environment variables

| Variable | Component | Purpose |
| --- | --- | --- |
| `MAGIC_TELEMETRY_PUBLISH_TOKEN` | Agent | Bearer token for backend ingestion (when `agentAuth: bearer`) |
| `MAGIC_TELEMETRY_CALLBACK_SECRET` | Agent | HMAC-SHA256 key for callback signing |
| `MAGIC_TELEMETRY_ID_HASH_KEY` | Agent | HMAC key for identifier hashing (`FR-PRS-021`) |
| `MAGIC_TELEMETRY_AGENT_TOKENS` | Backend | Agent token store reference or secret manager path |
| `MAGIC_TELEMETRY_LLM_API_KEY` | Backend | LLM credential for the NL fallback |
| `MAGIC_TELEMETRY_ENTRA_CLIENT_SECRET` | Backend | Entra app credential |

`NFR-SEC-004`: the process MUST fail to start if a required secret is missing, rather than
falling back to an insecure default. The `ID_HASH_KEY` MUST be identical across agents that
need comparable hashes, and rotating it is a documented, deliberate operation.

## 4. Validation rules at load

| ID | Rule |
| --- | --- |
| `FR-CFG-002` | Unknown keys are a startup error, not a warning — a typo'd threshold silently doing nothing is unacceptable. |
| `FR-CFG-003` | Every `logs[]` entry MUST have a unique `name`, a non-empty `instanceId`, and at least one path; overlapping globs across entries MUST be reported as an error. |
| `FR-CFG-004` | Durations MUST parse; `pollInterval` MUST be ≥ `100ms`; `bucketSeconds` MUST be one of 5, 10, 15, 30, 60. |
| `FR-CFG-005` | `callbacks.endpoint` MUST be `https://` unless `allowInsecureCallback: true`. |
| `FR-CFG-006` | `store.retentionWindow` MUST be ≤ 24h and `query.maxRangeSeconds` MUST be ≤ `retentionWindow`. |
| `FR-CFG-007` | Rule definitions MUST reference existing metrics and existing schedules; a dangling `scheduleRef` is a startup error. |
| `FR-CFG-020` | `--check-config` MUST perform all of the above plus glob resolution and print the effective configuration with secrets redacted. |
