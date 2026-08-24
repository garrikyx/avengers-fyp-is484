# 002 — Telemetry Agent Design

Status: Draft · Owner: TBD · Last updated: 2026-07-31

## 1. Process model

The agent is a single process containing one goroutine pipeline per monitored file, feeding
shared aggregation and dispatch stages through bounded channels.

```
per file:  [Log Monitor] ──lines──► [Parser Engine] ──events──► ┐
                                                                ├─► [Metrics Aggregator]
                                                                │        │ snapshots (10s)
                                                                │        ▼
                                                                ├─► [Rule Engine] ──alerts──► [Callback Dispatcher] ──► Magic
                                                                │        │
                                                                └────────┴──► [Backend Publisher] ──► Backend
                                                                     [Health Reporter] ──► Backend
```

`FR-PUB-004`: Every inter-stage channel MUST be bounded. On overflow the agent drops the
oldest item, increments a drop counter per stage, and never blocks the log reader.

## 2. Log Monitor

### 2.1 Requirements

| ID | Requirement |
| --- | --- |
| `FR-LOG-001` | MUST monitor a configurable set of file paths and glob patterns, each tagged with `instanceId`, `logType` and `parser`. |
| `FR-LOG-002` | MUST support two read modes per file set: `tail` (event-driven via fsnotify with a poll fallback) and `interval` (scan every `pollInterval`). |
| `FR-LOG-003` | MUST track a byte offset per file and resume from it after restart. |
| `FR-LOG-004` | MUST identify files by `(device, inode)` on POSIX and by file ID on Windows, not by path, so rotation is detected reliably. |
| `FR-LOG-005` | MUST detect rotation (rename, create-new, copy-truncate) and read the tail of the rotated file before switching to the new one, up to `rotationDrainTimeout`. |
| `FR-LOG-006` | MUST detect truncation (size < offset) and reset the offset to 0, emitting a `log.truncated` event. |
| `FR-LOG-007` | MUST emit only complete lines; a trailing partial line is retained in a buffer until its newline arrives or `partialLineTimeout` elapses. |
| `FR-LOG-008` | MUST cap line length at `maxLineBytes` (default 64 KiB); longer lines are truncated once, counted, and flagged `truncated=true`. |
| `FR-LOG-009` | MUST open files read-only with no locking that could block Magic's writes. |
| `FR-LOG-010` | MUST report per-file read lag (now − timestamp of last line read) and offset progress. |
| `FR-LOG-011` | Files matching a glob that appear after start MUST be picked up within `discoveryInterval`; files that disappear MUST be closed without error. |
| `FR-LOG-012` | On first-ever start for a file, the monitor MUST begin at EOF (`startAt: end`) unless configured `startAt: beginning`, so startup does not replay a day of logs. |

### 2.2 Offset checkpointing

- Offsets are checkpointed to a local state file (`state.json`, atomic write via temp+rename)
  every `checkpointInterval` (default `5s`) and on clean shutdown. `FR-LOG-020`
- The state file contains offsets, file identities and rule state only. It MUST NOT contain
  log content. `NFR-SEC-003`
- `FR-LOG-023`: Because an in-memory identity comparison cannot be serialised, persisted file
  identity MUST be a digest of the file's head together with **the length that digest covers**,
  and MUST be invalidated whenever the head changes. Both failure modes this prevents are
  silent:
  - Digesting "whatever is present now" makes a file shorter than the digest window change
    identity every time it grows, so every restart re-reads it from the beginning. Recording the
    length lets a later comparison digest exactly the same prefix.
  - After an in-place truncation the cached digest describes content that no longer exists. If
    it is not invalidated, the checkpoint pairs a valid offset with a stale identity, and the
    next start fails to recognise the file and re-reads it.
- `FR-LOG-024`: A rotation observed while running proves the replacement is a different file, so
  that file's checkpoint MUST NOT be consulted. Relying on the digest alone would resume at the
  old offset whenever a replacement begins with the same bytes, such as a fixed log header.
- On restart, a checkpoint at most `checkpointInterval` old means at most that much data is
  re-read. Re-reading MAY double-count metrics within one bucket; the agent MUST mark the
  first snapshot after restart with `restarted: true` so the backend can annotate it.
  `FR-LOG-021`

## 3. Parser Engine

Behaviour is specified in [003-fix-parsing.md](./003-fix-parsing.md). The agent-level
contract:

| ID | Requirement |
| --- | --- |
| `FR-PRS-001` | Each line MUST be classified as `fix`, `app_log`, or `unsupported` before parsing. |
| `FR-PRS-002` | A parse failure MUST produce a `parse.error` event with reason code and MUST NOT stop the pipeline or be retried. |
| `FR-PRS-003` | Parsing MUST be pure and allocation-bounded; no network or disk access. |

## 4. Metrics Aggregator

Data model in [004-telemetry-data-model.md](./004-telemetry-data-model.md). Agent-level
contract:

| ID | Requirement |
| --- | --- |
| `FR-MET-001` | MUST aggregate into fixed 10s wall-clock buckets keyed by bucket start time. |
| `FR-MET-002` | MUST retain the last `localRetentionBuckets` (default 360 = 1h) buckets in memory to serve rule windows and to republish after a backend outage. |
| `FR-MET-003` | Late events (log timestamp older than the current bucket) MUST be attributed to their own bucket if it is still in memory, otherwise counted in `metrics.late_dropped`. |
| `FR-MET-004` | MUST enforce the cardinality limits in spec 004 §5 and fold excess dimension values into `__other__`. |

### 4.1 Latency measurement

`FR-MET-010`: The agent MUST compute order acknowledgement latency by correlating a
`NewOrderSingle` (35=D) with the first `ExecutionReport` (35=8) sharing the same `ClOrdID`.

- Correlation state is a bounded LRU map (`maxPendingOrders`, default 100 000) with a TTL
  (`pendingOrderTtl`, default `5m`). Evictions increment `metrics.latency_uncorrelated`.
- Timestamps: prefer the FIX `SendingTime` (52) / `TransactTime` (60) when present and
  parseable; otherwise fall back to the log line timestamp. The chosen source MUST be
  recorded on the histogram as dimension `timeSource=fix|log`. `FR-MET-011`
- Negative or absurd latencies (> `maxPlausibleLatency`, default `60s`) are discarded and
  counted in `metrics.latency_implausible`. `FR-MET-012`
- Latency is stored as a bucketed histogram, never as a raw sample list. `FR-MET-013`

## 5. Rule Engine

See [005-alerting-and-callbacks.md](./005-alerting-and-callbacks.md).

`FR-RUL-002`: Rule evaluation MUST be driven by a ticker (default every `5s`) reading
completed buckets — not by each incoming event — so that evaluation cost is independent of
message throughput.

## 6. Backend Publisher

| ID | Requirement |
| --- | --- |
| `FR-PUB-001` | MUST publish a batch every `publishInterval` (default `10s`) containing: metric snapshots for newly completed buckets, structured events, alert state changes, and a heartbeat. |
| `FR-PUB-002` | MUST gzip bodies above `compressThreshold` (default 4 KiB) and set `Content-Encoding: gzip`. |
| `FR-PUB-003` | MUST include a monotonically increasing `batchSeq` per agent and a stable `batchId` (UUIDv7) so the backend can deduplicate retries idempotently. |
| `FR-PUB-004` | MUST buffer unpublished batches in memory up to `publishBufferBytes` (default 64 MiB) or `publishBufferMaxAge` (default `15m`), whichever is hit first, then drop oldest and count `publish.dropped_batches`. |
| `FR-PUB-005` | MUST retry failed publishes with exponential backoff (base `1s`, factor 2, cap `60s`, ±20% jitter). |
| `FR-PUB-006` | MUST treat HTTP 4xx (except 408/429) as permanent: log, count `publish.rejected`, and drop the batch rather than retry forever. |
| `FR-PUB-007` | MUST NOT let publishing block aggregation or rule evaluation. |
| `FR-PUB-008` | Buffered data MUST be memory-only; it is lost on restart by design (no raw or derived data spooled to disk beyond the offset state file). |

## 7. Health Reporter

See [011-observability-and-runbooks.md](./011-observability-and-runbooks.md).
`FR-HLT-001`: A heartbeat MUST be published every `heartbeatInterval` (default `10s`) even
when there is no telemetry, and MUST include read lag, parse error counts, callback failure
counts, queue depths and drop counters.

## 8. Sequence flows

### 8.1 Log ingestion and metric publication

1. Magic appends a line to a monitored file.
2. Log Monitor detects the change (fsnotify or poll), reads from the last committed offset,
   splits complete lines, and emits them with `{instanceId, path, logType, readAt}`.
3. Parser Engine classifies the line. For FIX, it extracts allowlisted tags and emits a
   `fix.*` event; on failure it emits `parse.error`.
4. Metrics Aggregator updates counters for the event's bucket and dimension set, and updates
   latency histograms via `ClOrdID` correlation.
5. Every `5s` the Rule Engine evaluates completed buckets and may transition alert state.
6. Every `10s` the Publisher sends the batch of snapshots, events, alert changes and
   heartbeat.
7. Backend validates, deduplicates by `batchId`, merges into in-memory views.
8. Data becomes queryable. End-to-end target: p95 under 5s from log write to queryable
   (`NFR-PERF-002`).

### 8.2 Restart

1. On SIGTERM the agent stops readers, flushes the current bucket, attempts one final publish
   with a `shutdownGrace` deadline (default `5s`), checkpoints offsets, and exits 0.
2. On start it loads `state.json`, reopens files by identity, and resumes from checkpointed
   offsets (subject to `FR-LOG-021`).
3. Alert state is restored from the state file so an alert that was firing before restart does
   not re-fire and re-notify. `FR-RUL-020`
4. If the state file is missing or corrupt, the agent MUST start cleanly at EOF for all files
   and emit a `agent.state_reset` event rather than refusing to start. `FR-LOG-022`

### 8.3 Backend outage

1. Publishes fail; the Publisher backs off and buffers (`FR-PUB-004`, `FR-PUB-005`).
2. Aggregation, rule evaluation and callbacks continue unaffected (`NFR-REL-003`).
3. On recovery, buffered batches are sent oldest-first before new ones; the backend accepts
   out-of-order buckets and merges by bucket timestamp (`FR-ING-005`).
4. The heartbeat gap is visible in the backend as an agent connectivity alert (`FR-RUL-030`).

## 9. Resource discipline

The agent's resource requirements are owned by
[009-nfr-and-security.md](./009-nfr-and-security.md) §1 and are not restated here. The ones that
constrain this spec's design most directly:

| Constraint on the design above | Owning ID |
| --- | --- |
| RSS ceiling — why every stage is bounded and sheds rather than queues (`FR-PUB-004`) | `NFR-PERF-003` |
| No per-message map allocation — why the parser fills a fixed allowlisted struct (spec 003 §4) | `NFR-PERF-004` |
| `GOMAXPROCS` default of `min(2, NumCPU)` — why per-file goroutines are cheap but not unlimited | `NFR-PERF-005` |
| Documented CPU/memory caps in the deployment unit — see spec 011 §4 | `NFR-PERF-006` |
| No synchronous I/O per line — why publishing is decoupled by a channel and a ticker | `NFR-PERF-009` |
