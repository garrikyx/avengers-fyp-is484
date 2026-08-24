# 011 — Observability and Runbooks

Status: Draft · Owner: TBD · Last updated: 2026-07-31

A telemetry system that cannot be trusted is worse than none, because it produces confident
wrong answers. This spec defines how the system reports on itself and how operators respond.

## 1. Health signals

### 1.1 Agent

| Signal | Source | Healthy | Investigate |
| --- | --- | --- | --- |
| Heartbeat age | Backend agent registry | < 30s | > 60s → `AgentHeartbeatMissing` |
| Log read lag | `log_read_lag_ms` | < 1s | > 5s sustained |
| Offset progress | Heartbeat `files[].offset` | increasing during trading hours | static while file grows |
| Parse success rate | `parse_errors` / `log_lines_read` | > 99% | < 99% → `ParseErrorRate` |
| Unsupported line ratio | `unsupported_lines` / `log_lines_read` | stable | sudden rise = log format change |
| Stage drops | `dropped_stage_events` | 0 | any sustained non-zero |
| Publish queue depth | `publish_queue_depth` | < 10 | growing monotonically |
| Publish buffer | `publishBufferBytes` | < 25% of cap | > 75% of cap |
| Callback success | `callback_failures` | 0 | > 3 in 5m → `CallbackFailing` |
| Cardinality folding | `cardinality_folded` | 0 | non-zero = caps hit, dimensions incomplete |
| Latency correlation | `latency_uncorrelated` | < 5% of orders | higher = ClOrdID mismatch or missed lines |
| RSS / CPU | Heartbeat `resourceUsage` | within spec 009 §1 | approaching limits |
| Recovered panics | `agent.panics_recovered` | 0 | any occurrence is a bug to file |

### 1.2 Backend

Ingest rate, validation failure rate, dedupe hit rate, ingest queue depth, store memory
percent, buckets evicted early, query p95, fan-out failures, stale agent count, NL intent
match rate and LLM fallback rate — all exposed on `/metrics` (`FR-HLT-010`).

## 2. Derived agent status

`FR-HLT-002`: `status` in the heartbeat is computed, not hand-set:

- **`unhealthy`** — any monitored file has not progressed while growing, OR parse error rate
  > 25%, OR publish buffer > 90% of cap, OR RSS > `memoryLimitMb`.
- **`degraded`** — read lag > 5s, OR parse error rate > 1%, OR any stage drops in the last
  5 minutes, OR callback failures > 0 in the last 5 minutes, OR cardinality folding active.
- **`healthy`** — otherwise.

`FR-HLT-003`: The heartbeat MUST include a `statusReasons: []` list naming each condition that
contributed, so an operator never has to guess why the agent says `degraded`.

`FR-HLT-004`: Known data gaps (restart re-reads, dropped batches, dropped stage events,
folded cardinality) MUST be reported to the backend and surfaced through
`dataCompleteness` (`FR-QRY-015`). The system MUST NOT present a gap as a zero.

## 3. Runbooks

Each runbook is referenced by rule `runbook` links (`FR-RUL-003`).

### High reject rate

`HighRejectRate` / `RejectSpike`.

1. Confirm it is real, not a data artefact: `GET /telemetry/health/agents/{id}` — if the agent
   is `degraded` for parse errors, suspect a log format change before a trading problem.
2. Query rejections grouped by `rejectReason`, then by `symbol` and `session`.
3. If one reason dominates: `UnknownSymbol` → reference data or symbology; `OrderExceedsLimit`
   / `risk_limit_breach` → risk configuration; `market_closed` → session or calendar;
   `throttled` → rate limiting upstream.
4. If spread evenly across reasons and sessions, suspect the counterparty or venue.
5. Escalate to the Magic application team with the alert `alertId` and the grouped query.

### No log activity

`NoLogActivity`.

1. Check whether Magic is running and whether it is trading — an idle instance outside trading
   hours is expected, which is why the rule is schedule-bound (`FR-RUL-007`).
2. Check the file: does it exist, is its mtime advancing, has it rotated to a path the glob no
   longer matches?
3. Check agent file state in the heartbeat: `state: reading` vs `waiting` vs `error`.
4. Check permissions — a permission change on the log directory is the most common cause.
5. Remember trading rules are suppressed for that instance while this fires (`FR-RUL-021`);
   absence of reject alerts means nothing until this clears.

### Parser error spike

`ParseErrorRate` / `ParserBroken`.

1. Query `parse_errors` grouped by `reason`.
2. `no_begin_string` or `malformed_field` in bulk → the log format or delimiter changed; check
   `fixDelimiter` and whether the logging framework was reconfigured.
3. `incomplete_message` → multi-line splitting; consider raising `maxJoinLines`.
4. `line_truncated` → raise `maxLineBytes`.
5. `bad_timestamp` plus `ClockSkew` → host clock or NTP.
6. `unknown_msg_type` / `unknown_enum_values` → new message types in use; update spec 003 §6.
7. Treat `internal_error` as a defect: capture the reason counts, file a bug. Do not attempt to
   reproduce by copying production log lines into a ticket (`NFR-SEC-001`).

### Backend unreachable

`BackendUnreachable`.

1. Alerting and callbacks are unaffected (`NFR-REL-003`) — say so before anyone escalates.
2. Compute survivable outage duration: `publish.bufferBytes` ÷ current publish rate. Record it
   in the incident so the deadline for data loss is explicit.
3. Check backend health, TLS validity and token expiry (a rotated token shows as 401, not a
   connection failure).
4. After recovery, expect a burst of buffered batches oldest-first and briefly elevated ingest.
5. If the buffer overflowed, `publish.dropped_batches` is non-zero and affected windows MUST be
   treated as `partial`.

### Callback failures

`CallbackFailing`.

1. Inspect `delivery` on recent alerts (`GET /telemetry/alerts`) for status codes.
2. 401/403 → the HMAC secret or auth model changed on Magic's side.
3. 404 → endpoint path changed. 5xx/timeout → Magic-side availability.
4. The alerts themselves are still in the backend; use `GET /telemetry/alerts` as the interim
   notification channel and tell the on-call that push is down but state is intact.
5. Use `dryRun: true` when testing a new endpoint.

### Agent heartbeat missing

`AgentHeartbeatMissing` (backend-owned).

1. Distinguish agent death from network partition: is the host reachable, is the process alive?
2. If the process is dead, restart it; expect `restarted: true` buckets and at most
   `checkpointInterval` of re-read data (`NFR-REL-004`).
3. If the state file was lost, the agent starts at EOF and emits `agent.state_reset`; the gap
   is permanent and MUST be noted in the incident.
4. Assume **all** telemetry for that instance is missing during the gap. No alert firing during
   a heartbeat gap is not evidence of health.

### Memory pressure

Agent RSS approaching `memoryLimitMb`, or backend `store` memory above `memoryWarnPercent`.

1. Agent: check `maxPendingOrders` utilisation and `cardinality_folded` — an unexpected symbol
   explosion is the usual cause. Reduce `maxSymbols` or `localRetentionBuckets`.
2. Backend: reduce `store.retentionWindow`, or add a replica and switch to `colocated` routing.
3. Neither component may exceed its cap; if shedding is occurring, `dataCompleteness` will show
   it, and that is the correct behaviour, not a bug to suppress.

## 4. Deployment operations

| Operation | Procedure |
| --- | --- |
| Install agent | Place binary, write config, `--check-config`, install service unit, start, confirm heartbeat in `/telemetry/health/agents` |
| Upgrade agent | Stop (SIGTERM, flushes and checkpoints), replace binary, start. Expect a sub-5s gap. Never upgrade during a market open window. |
| Change thresholds | Edit config, `--check-config`, SIGHUP. Alert state is preserved (`NFR-CFG-003`). |
| Add a log file | Edit `logs[]`, `--check-config`, restart the agent (path changes require restart). |
| Rotate callback secret | Add the new secret on Magic's verifier first (accept both), then update the agent env and restart. |
| Rotate ID hash key | Deliberate and disruptive: correlation across the rotation boundary is lost. Schedule outside trading hours. |
| Backend deploy | Rolling replica replacement. Each replaced replica starts empty and reports `warming`; queries during the roll may return `partial`. |
| Decommission an agent | Remove from the registry so `AgentHeartbeatMissing` does not fire forever. |

## 5. What operators must never do

- Never enable a raw-log debug mode in production (`NFR-SEC-013` makes it impossible in release
  builds; do not work around it).
- Never paste production log lines into tickets, chat, or prompts.
- Never raise a cap without recording the memory implication.
- Never treat "no alerts" as "healthy" without checking agent health first.
