# UBS-58 / 59 / 60 implementation notes — heartbeat emitter, parse-error window, publish queue depth

Working notes for the stacked `UBS-58-Heartbeat-Emitter` → `UBS-59-Parse-Error-Rate`
→ `UBS-60-Publish-Queue-Depth` branches, in the same spirit as `ubs30-notes.md`: the
code says *what*, this says *why*.

## Ticket vs. spec decisions (read first — these need team sign-off)

| Topic | Jira UBS-58 says | Spec says | Built as | Status |
| --- | --- | --- | --- | --- |
| Heartbeat interval default | 30s | `heartbeat.interval: 10s` (spec 002 `FR-HLT-001`, spec 010) | **10s**, configurable via `heartbeat.interval` | needs team OK; ticket to be amended |
| "Backend records `lastHeartbeatUtc`" and "missing heartbeat beyond 3x interval flags `unresponsive`" | in UBS-58's AC | `missingHeartbeatThreshold: 60s` backend-side (spec 005 `FR-RUL-030`, spec 006 `FR-ING-010`); UBS-69's own scope note says stale detection must be backend-side | **Not built here** — moved to UBS-69. The stub receiver previews it only | needs team OK; move AC on Jira |
| Payload shape | `agentId`, `timestampUtc`, `status` | spec 004 §6 full document | **spec 004 §6**, camelCase on the wire | built |
| Status | per-signal "degraded" flags | `FR-HLT-002` one documented rule set + `FR-HLT-003` `statusReasons[]` | one `derive_status()`; only the read-lag rule has a producer today | built |

Spec wins wherever the two conflict (same policy as UBS-30's `log_read_lag_ms` call).

## Module map (`apps/agent/src/telemetry_agent/health/`)

| File | Role |
| --- | --- |
| `config.py` | `HeartbeatConfig` (interval, agent identity), `HealthThresholds` (every `FR-HLT-002` threshold, declared up front so 59/60 add a *signal*, not a config shape), `load_health_config()` for the `agent:` / `heartbeat:` / `health:` sections of `config/agent.yaml`. Missing file → defaults; malformed file → `HealthConfigError` (refuse to start, same as RE-05). Unknown keys are refused. Sibling sections (`log:`, `backend:`) are passed through untouched. |
| `reporter.py` | UBS-30's `HealthReporter`, extended. `snapshot()` samples a `HealthSignals` dataclass; `derive_status(signals)` is the `FR-HLT-002` rollup; `build_heartbeat()` assembles the spec 004 §6 document. UBS-30's `file_statuses()` / `overall_read_lag_ms()` / `degraded_reasons()` / `is_degraded()` are unchanged in behaviour (`degraded_reasons` is now the read-lag slice of `derive_status`). The `degraded_threshold_ms=` kwarg is kept for UBS-30 callers and still wins over `thresholds=`. |
| `heartbeat.py` | `BufferingHeartbeatSink` (UBS-60): bounded oldest-first retry queue in front of any sink; `len()` is the demo's queue-depth provider. `HeartbeatEmitter.tick()` (pure, testable) and `run(stop)` (asyncio loop, first tick immediate, then every `interval_seconds` regardless of log activity). Sink failures are counted and logged, never raised — a dead backend must not kill the agent (spec 002 §8.3). Sinks: `PrintHeartbeatSink`, `LoggingHeartbeatSink`, `HttpHeartbeatSink` (stdlib `urllib`, `POST /telemetry/heartbeat` per spec 007 §2.3). |
| `wire.py` | `to_ingestion_heartbeat()` — flattens our heartbeat to UBS-66's ingestion contract at the sink boundary (see "Wire compatibility with UBS-66"). |
| `demo.py` | `telemetry-agent-heartbeat` console script: tails files, runs each line through `FixParser` into `record_parse_result()`, emits heartbeats. Not the production entrypoint (that is M1.5 pipeline wiring; `main.py` is untouched). |
| `window.py` (UBS-59) | `SlidingWindowCounter`: per-bucket ints keyed by bucket index, expired on every access, so memory is bounded by `window / bucket` (300 ints for the default 5m/1s) no matter the event rate. Backs every `...Last5Min` field. |

`packages/telemetry_shared/.../models/health.py` is the wire contract
(`FR-ING-022`). It now extends `CamelModel` like the other shared models, so
`model_dump_json(by_alias=True)` is the exact spec 004 §6 shape.

## Design points

- **`None` is not `0`** (`FR-HLT-004`). Every signal the agent has no producer for
  is `null` on the wire and `None` in `HealthSignals`, and `derive_status()` skips
  it. A backend reading `parseErrorCountLast5Min: null` knows nothing is measuring
  parse errors yet; `0` would claim there are none.
- **Rules only fire on evidence.** An unread file has no lag and is never a
  reason (same call as UBS-30). Read lag exactly at the threshold is healthy
  (`>` not `>=`, per spec 011's "> 5s").
- **`uptimeSeconds`** counts from `HealthReporter` construction (the emitter is
  created right after it), using the reporter's injectable clock so tests never sleep.
- **`files[].state`** is `reading` once a line has been read, else `waiting`.
  `LogMonitor` exposes no rotation count or error state, so `rotationsDetected`
  stays `0` and `error` is never emitted. That is Mitch's file (UBS-22/24); not
  extended here.
- **Thread/async model.** `run()` is a plain asyncio coroutine and `tick()` is
  synchronous; the HTTP sink blocks the loop for at most `timeout_seconds` (5s).
  Fine for a demo transport; the real Publisher owns buffering/retry (`FR-PUB-004/005`).

## UBS-59: parse-error window

- **Intake, not subscription.** The ticket says "subscribes to parse-error events";
  there is no event bus (M1.5). The reporter exposes `record_parse_result(result)`,
  `record_parse_error()` and `record_lines_read(n)`; whoever owns the parser loop
  calls them. The demo does exactly that with `FixParser`.
- **What counts as a parse error** — `is_parse_error()` in `reporter.py` — is the
  Metrics Aggregator's convention (`metrics/demo_sink.py`): a closed-set
  `ParseResult.error` (`line_truncated`, frame errors, `internal_error`) or a framed
  message with `bad_timestamp` / `unknown_msg_type`. Warnings such as
  `body_length_mismatch` are not errors. Chosen so `parseErrorCountLast5Min` and the
  aggregator's `parseErrorRate` can never disagree about the same line.
- **Rate needs a denominator.** `lines_read` is tracked in a second window of the same
  length, so `parse_error_rate = errors / lines` over the same 5 minutes (spec 004
  §4.5). Zero lines in the window → rate `None` (not 0, not 100%), and no rule fires.
- **`null` until the first line.** All three parse fields stay `None` until a
  producer has called in once (`_parse_signal_seen`), so an agent nobody has wired
  a parser into does not claim a clean parse record (FR-HLT-004).
- **Rules** (spec 011 §2, strict `>`): rate > 25% → `unhealthy`, > 1% → `degraded`,
  both with a reason like `parse error rate 2.0% (2/100 lines in last 300s) exceeds 1%`.
  Thresholds and window come from `health.parseErrorRateDegraded` /
  `parseErrorRateUnhealthy` / `rollingWindow` in `config/agent.yaml`.
- **Bucketed, so approximate at the edge.** The window is the current (partial) 1s
  bucket plus the 299 before it, so an event leaves the count up to 1s *early*
  (recorded at t=0.9s, gone at t=300.0s) and is never held past 300s. Acceptable for
  a health gauge; the same trade-off the Metrics Aggregator makes with 10s buckets.

## UBS-60: publish queue depth

- **Provider, not Publisher.** The Backend Publisher (spec 002 §6) is M4 and not
  started. The reporter takes a `queue_depth_provider: Callable[[], int]` (ctor or
  `set_queue_depth_provider()`); the Publisher registers `lambda: len(its_queue)` when
  it exists. Until then `publishQueueDepth` is `null` (FR-HLT-004), never 0.
- **Watermarks** (spec 011 §1.1 "< 10" healthy): depth ≥ `publishQueueHighWatermark`
  (10) → `degraded`, ≥ `publishQueueCriticalWatermark` (100) → `unhealthy`. `≥` because
  a watermark is a level you reach. The critical value is a placeholder — spec gives
  none — and needs team review.
- **Trend** is derived, not sent. Spec 004 §6 has no trend field, and the ticket allows
  "derivable from consecutive snapshots", so `HealthSignals.publish_queue_trend`
  (`rising` / `draining` / `flat`, `None` on the first sample) is computed from the
  previous snapshot and appended to the reason text
  (`publish queue depth 12, rising at or above high watermark 10`). The backend can
  derive the same from consecutive heartbeats.
- **Demo queue.** `BufferingHeartbeatSink` queues heartbeats the downstream sink
  rejects, retries oldest-first on the next tick, drops oldest when full
  (`FR-PUB-004`'s shape, none of its sizing/backoff). It exists so
  `publishQueueDepth` can be exercised end to end; the Publisher replaces it.
- **Not covered:** `FR-PIP-005`'s pipeline line/event queue depths and drop
  counters — those queues are M1.5 and don't exist yet. `publishBufferBytes` stays
  `null` (the demo buffer counts items, not bytes).

## Wire compatibility with UBS-66 (decided 2026-09-22 — revisit)

UBS-66 landed `telemetry_shared.models.ingestion.Heartbeat` on `main` while this
branch was in review. Both models implement spec 004 §6, written independently
(`models/ingestion.py` is new in `9bdac55`; nobody edited `models/health.py`), and
they disagree in one way that matters:

| | `models.health.AgentHeartbeat` (ours) | `models.ingestion.Heartbeat` (UBS-66) |
| --- | --- | --- |
| Unmeasured signal | `null` — FR-HLT-004: a gap is never a zero | required, `int`, `ge=0` |
| `statusReasons` (FR-HLT-003) | present | **no such field**, and the model is `extra="forbid"` |
| `uptimeSeconds` | `float` | `int` |
| `resourceUsage` | optional | required |
| `files[].instanceId` | optional (the Log Monitor has no file→instance map) | required, `min_length=1` |

**Decision: the agent adapts.** Downstream consumers are waiting on a working
`POST /telemetry/heartbeat`, and only one shape can be on the wire. Verified
against the merged endpoint: our own shape returns **400**
(`uptimeSeconds: Input should be a valid integer`), the adapted shape returns
**202**.

`AgentHeartbeat` remains the agent's internal truth — the reporter keeps its
`None`s, so no status rule ever fires on a fabricated zero — and
`health/wire.py:to_ingestion_heartbeat()` flattens it inside the sink at the last
moment. `HttpHeartbeatSink` defaults to `wire="ingestion"`.

**What the adaptation costs** (the reasons to revisit):

1. **`statusReasons` is dropped on the wire.** The backend receives `status:
   degraded` with no explanation, so `GET /telemetry/health/agents/{id}` cannot
   answer "degraded *why*" — the operator has to read agent logs instead. This is
   the biggest loss; FR-HLT-003 exists precisely so nobody has to guess.
2. **Unmeasured signals arrive as `0`**, indistinguishable from a measured zero.
   An agent with no parser wired reports `parseErrorCountLast5Min: 0` — "perfectly
   clean" — which is the exact misreading FR-HLT-004 forbids.
3. **`resourceUsage` is fabricated as zeros** because the agent does not measure
   RSS/CPU yet (no `psutil` decision). A dashboard would plot 0 MB RSS.

**How to reverse it**, once the team settles the contract (preferred: make the
optional signal fields `| None = None` and add `statusReasons` in
`ingestion.Heartbeat`, keeping `uptimeSeconds` as `float`):

1. Pass `wire="health"` to `HttpHeartbeatSink` (one argument), or
2. delete `health/wire.py` and its test, and send `AgentHeartbeat` directly.

`tests/unit/agent/health/test_wire_compat.py` pins every one of these costs, so
the tests fail loudly if the upstream contract changes — that failure is the
signal to reverse.

## Missing downstream / upstream (what this branch cannot prove)

| Gap | Effect here | Owned by |
| --- | --- | --- |
| No Ingestion Service / `POST /telemetry/heartbeat` on the backend | Heartbeats go to stdout or to `scripts/heartbeat_receiver_stub.py`; `HttpHeartbeatSink` has never talked to the real backend | UBS-66 (ingestion), UBS-87 (registry write-through) |
| No backend health read side | `lastHeartbeatUtc`, `unresponsive`/`missing`, `/telemetry/health/agents` exist only in the stub | UBS-69 |
| No Backend Publisher | `HttpHeartbeatSink` + `BufferingHeartbeatSink` are stand-ins: no backoff, gzip, auth, `batchSeq`; `publishQueueDepth` is populated only when something registers a provider (the demo does), `publishBufferBytes` stays `null` | Publisher (M4) |
| No pipeline bridge (M1.5) | Nothing in production calls the reporter from a parser loop; the demo polls files itself | M1.5 |
| No parse-error producer wired in production | `parseErrorCountLast5Min` is `null` outside the demo/tests; the reporter's intake exists (UBS-59) but nothing in a real agent process calls it | M1.5 pipeline bridge |
| Callback Dispatcher branch (UBS-32–34) unmerged | `callbackFailuresLast5Min` is `null` | UBS-32–34 + a follow-up to wire it |
| No resource sampling | `resourceUsage` is `null`; adding `psutil` is a team decision | M7 |
| `activeAlertCount` | `null`; the Rule Engine exists but is not wired into a running agent | M1.5 / M5 |

## Placeholder receiver — `scripts/heartbeat_receiver_stub.py`

A stdlib `http.server` stand-in for the two missing backend pieces, so the agent's
output can be checked end to end today. It validates every `POST /telemetry/heartbeat`
body against `AgentHeartbeat` (400 + pydantic errors on drift, 202 otherwise), keeps
`{agentId: lastHeartbeatUtc, status}` in memory, serves it on
`GET /telemetry/health/agents`, and prints `STALE <agentId>` after `--stale-after`
seconds without a heartbeat. It is labelled a stub in its docstring, is not a
package module, and is deleted when UBS-66/69 land. Its `/telemetry/health/agents`
output is *not* the UBS-69 contract.

## How to see it

```bash
# terminal 1
uv run python scripts/heartbeat_receiver_stub.py --stale-after 6
# terminal 2
uv run telemetry-agent-heartbeat --interval 2 --sink http://127.0.0.1:8000/telemetry/heartbeat
#   append lines to demo_logs/Fix.log -> readLag appears; stop appending > 5s -> degraded
#   Ctrl-C terminal 2 -> terminal 1 prints STALE after 6s
```

Automated coverage: `tests/unit/agent/health/{test_heartbeat,test_status,test_health_config}.py`
plus the updated UBS-30 tests; UBS-59: `test_window.py`, `test_parse_errors.py`;
UBS-60: `test_queue_depth.py`. To see UBS-60 live, run the demo with an http sink,
stop the stub receiver for a while (queue rises past the watermarks), then start it
again (queue drains oldest-first, status recovers).
To see UBS-59 live, append a FIX line with an unknown MsgType, e.g.
`8=FIX.4.2|9=61|35=ZZ|11=ORD-9|10=072|`, and watch `parseErrorCountLast5Min` and the
status reason on the next heartbeat.

## Also touched, and why

- `tests/unit/agent/health/test_reporter.py`, `tests/integration/agent/test_ubs30_health_integration.py`:
  `FileReadHealth.last_read_at` → `last_line_at_utc` (spec 004 §6 name). Their
  `write_text` / `open(..., "a")` calls now pass `newline="\n"` — on Windows the
  default translated `\n` to `\r\n`, so every offset assertion was off by one per
  line. Two integration tests still fail on Windows for the open-handle-during-rename
  reason already recorded in `ubs30-notes.md`; CI is Linux.
- `config/agent.yaml`: commented example `agent:` / `heartbeat:` / `health:` keys.
- `apps/agent/pyproject.toml`: `telemetry-agent-heartbeat` console script.
- `tests/unit/agent/health/test_reporter.py:81`: `assert baseline is not None` so
  mypy stops flagging the `datetime | None + timedelta`.
