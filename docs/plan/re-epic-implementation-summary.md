# Rule Engine — Implementation Summary

Last updated: 2026-09-07 · Spec: [`005-alerting-and-callbacks.md`](../specs/005-alerting-and-callbacks.md)

The Rule Engine is a pure consumer of MA-04's `MetricsSnapshot` — it never
touches `MetricsAggregator`/`LatencyCorrelator` directly, so it's testable
purely from hand-built snapshot fixtures (`tests/unit/agent/rules/
rule_fixtures.py`). Callback dispatch (spec 005 §3, HTTP/HMAC delivery) is
separate, later scope — `evaluate()` returns the `AlertEvent`s that changed
or were re-notified this tick; wiring those to a `CallbackSink` is a
follow-up ticket.

## 1. Rule shape

Every rule (`telemetry_agent.rules.types.RuleConfig`) declares one or more
**severity tiers** sharing a single condition shape — same metric/window/
operator, different threshold. Two conditions differing only in threshold
are one rule with multiple tiers, not two separate rules: operationally
one incident escalating or de-escalating, not two co-existing alerts (spec
005 §1.1, updated as part of this work). The engine reads whichever value
the rule's `source` names — a counter sum, a gauge, a latency p95, or an
MA-04 indicator — and picks the *highest* tier whose condition holds.

## 2. The 14 default rules

| Rule | Kind | Tiers | Window | Status |
| --- | --- | --- | --- | --- |
| `HighRejectRate` | rate | warning@3%, critical@5% | 5m | wired |
| `RejectSpike` | threshold | warning@50 | 1m | wired |
| `CancelRejectSpike` | threshold | warning@20 | 5m | wired |
| `SessionRejects` | threshold | critical@5 | 5m | wired |
| `PendingOrderTimeout` | threshold (gauge) | warning@30s | — | wired |
| `AckLatencyBreach` | latency | warning@500ms, critical@1000ms | 5m | wired |
| `ParseErrorRate` | rate | warning@1%, critical@25% | 5m | wired (UBS-18) |
| `NoLogActivity` | absence | critical@0 (`messages_total`) | 1m | wired |
| `NoExecutions` | absence (guarded) | warning@0 while `orders_submitted`>0 | 15m | wired |
| `FixSessionDown` | threshold | critical@1 (`logouts` or `heartbeat_timeouts`) | 1m | wired (UBS-73, `logouts` only) |
| `SeqGapDetected` | threshold | warning@0 | 1m | wired (UBS-73) |
| `ClockSkew` | threshold | warning@10 | 5m | wired (UBS-73) |
| `CallbackFailing` | threshold | warning@3 | 5m | wired (UBS-74) |
| `BackendUnreachable` | threshold | warning@5 | 1m | no Backend Publisher yet |

"No producer" rules read as 0/no-fire structurally rather than raising —
same posture MA-04 established for `parseErrorRate`. `HighRejectRate`,
`AckLatencyBreach`, and `ParseErrorRate`'s thresholds are client-confirmed;
`PendingOrderTimeout`'s 30s has no spec or client number — see its
docstring in `defaults.py` for the domain reasoning.

`config/rules.yaml` is the live source of these 14 rules, parsed by
`telemetry_agent.rules.config_loader.load_rules` (`FR-RUL-008`/`009`);
`DEFAULT_RULES` is the fallback used only when that file is absent — see
§6 below.

## 3. Alert lifecycle

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

A tier change while `firing` updates `severity` and notifies immediately —
independent of `renotifyInterval` — without changing `alertId` or
`firstObservedUtc` (spec 005 `FR-RUL-022`, added as part of this work).
`active_alert_count()` counts `firing`/`resolving` only — `pending` is
internal bookkeeping for a condition that hasn't cleared `for` yet, not yet
"active alert output" for the `maxActiveAlerts` cap.

One `MetricsSnapshot` is built for one window; `DEFAULT_RULES` spans three
(1m/5m/15m). `evaluate()` filters to the rules matching the snapshot's own
window each call — the caller invokes it once per window needed. Gauge-
sourced rules (`window=None`) are evaluated on every call since MA-04's
gauges don't vary by window.

## 4. Safety and suppression (spec 005 §4)

- **Silences**: state still transitions, notification is suppressed.
- **Startup grace** (default 60s): no evaluation at all, broader than
  spec's literal "self-health rules only" wording — a simpler, strictly
  safer blanket suppression during cold start.
- **Dependent suppression** (`FR-RUL-021`): while `NoLogActivity` is firing,
  every rule with `depends_on_log_activity=True` reads as insufficient
  data instead of evaluating its raw condition. This is read once per tick
  from the *previous* tick's state, so it lags `NoLogActivity`'s own
  transition to firing by exactly one tick — order-independent, but not
  same-tick.
- **`maxActiveAlerts`/`AlertStorm`**: past the cap, new pending→firing
  transitions are suppressed (state stays `pending`, retried next tick)
  and one `AlertStorm` meta-alert fires once, not on every tick over cap.
- **Schedule gating** (`FR-RUL-007`): a `ScheduleChecker` seam, default
  always-active — real trading-calendar logic (spec 010 §5) is separate,
  unbuilt scope.

## 5. Config loading and SIGHUP reload (`FR-RUL-008`/`009`)

`telemetry_agent.rules.config_loader` parses `config/rules.yaml` into
`RuleConfig`s via a local pydantic model (`_RuleYaml`/`_TierYaml`, mirroring
the file's camelCase shape), never partially applying a broken file. Two
places this loosens relative to `FR-RUL-009`'s literal "refuse to start",
both deliberate:

- **Missing file**: falls back to `DEFAULT_RULES` — `config/rules.yaml`
  not existing at all is a valid deployment state (e.g. before an operator
  has customised anything), not "malformed".
- **Malformed file on reload** (not initial load): `SighupRuleReloader.
  reload()` catches `RuleConfigError`, logs it, and keeps serving the
  last-known-good rule set rather than crashing an already-running agent
  over an operator's YAML typo. `FR-RUL-009`'s "refuse to start" governs
  boot; a live process shouldn't die from a bad SIGHUP.

`RuleEngine.apply_rules(new_rules, now=...)` (`FR-RUL-008`) is what a
reload actually swaps in. Since `_states` is keyed by rule *name*, not
`RuleConfig` object identity, a state for a rule name present in both old
and new config carries over untouched — `alertId`/`firstObservedUtc`/
`notificationCount` all survive a threshold change with no special-casing.
A state whose rule disappeared from the new config is force-resolved (one
synthetic `resolved` event, since a condition with no rule definition
can't legitimately stay open) rather than left frozen forever.

`SighupRuleReloader.install()` registers the OS signal handler
(`signal.signal(SIGHUP, ...)`) — the call a future agent supervisor loop
makes once one exists. Nothing in this repo runs continuously yet
(`main.py` is a stub calling the parser CLI; M1 Log Monitor is unbuilt),
so that wiring itself is untested end-to-end, but the loader and the
reload mechanism are both fully unit-tested, including a real
`os.kill(os.getpid(), signal.SIGHUP)` round-trip.

## 6. Verified — what 67 new tests prove

| File | Proves |
| --- | --- |
| `test_RE_01_fsm.py` | All five transitions, `for`/`resolveAfter` timing, renotify + `notificationCount`, `alertId` stability through one occurrence and rotation after resolution, startup grace. |
| `test_RE_02_evaluators.py` | All 5 `RuleKind` evaluators, tier selection (highest crossed tier wins), insufficient-data paths recomputed from `denominator`/`count` against *this rule's* `min_samples` (not MA-04's own default), `NoExecutions`'s guard, absent counters as zero, a cold window crashing nothing. |
| `test_RE_03_safety.py` | `maxActiveAlerts`/`AlertStorm` (one notification, suppression persists, clears once under cap), silence suppressing notification but not state, dependent suppression's one-tick lag, schedule-inactive skip. |
| `test_RE_04_default_rules.py` | Each of the 14 default rules at its own threshold boundary, `HighRejectRate` escalating warning→critical on the same `alertId`, rules with unwired counters reading as no-fire. |
| `test_RE_05_config_loader.py` | Valid YAML round-trips to the same `RuleConfig`s; a missing file falls back to `DEFAULT_RULES`; `config/rules.yaml` itself matches `DEFAULT_RULES` one-for-one (catches drift between the two); every malformed shape (bad `kind`/`operator`, empty `tiers`, duplicate name, unknown field, empty rule list) raises `RuleConfigError` naming the rule, and never silently falls back once the file exists; duration-string parsing (`"30s"`/`"2m"`/`"1h"`). |
| `test_RE_06_reload.py` | `apply_rules` preserves `alertId`/`firstObservedUtc` across a reload that changes a surviving rule's threshold (proven via a post-reload renotify carrying the same `alertId`); force-resolves a `firing` alert whose rule was removed (one `resolved` event) but drops a `pending` one silently; `SighupRuleReloader.reload()` swaps in a valid file and rejects a malformed one (old rules keep firing, error logged); a real `os.kill(os.getpid(), signal.SIGHUP)` round-trip proves `install()`'s OS wiring, not just the Python method. |
| `tests/integration/agent/test_RE_integration.py` | Real `MetricsAggregator`/`LatencyCorrelator`/`snapshot()` output actually drives `RuleEngine.evaluate()` correctly — one rule per snapshot substructure (indicator, latency, gauge, counter), not the hand-built `MetricsSnapshot` fixtures the rest of this suite uses. Caught a real gap: `snapshot()`'s `min_sample_size` nulls latency percentiles independent of what a given rule's own `min_samples` would accept. |
| `tests/integration/agent/test_RE_session_integration.py` (UBS-73) | Raw FIX bytes through the real `FixParser` and the `metrics_event` bridge fire `FixSessionDown`, `SeqGapDetected` and `ClockSkew` — including that ten skewed messages stay under `ClockSkew`'s `> 10`, that `FixSessionDown` still works with no `heartbeat_timeouts` producer, and that session counters answer a `session_id` query but are correctly absent from a `symbol` one (FR-MET-030). |
| `tests/integration/agent/test_RE_callback_integration.py` (UBS-74) | Real dispatcher failures against a mock Magic endpoint reach `CallbackFailing` through `AgentCounterSampler`; three failures stay under threshold; successful deliveries never touch the failure counter; repeated sampling of the monotonic registry doesn't inflate 3 failures into a false alert; and the agent's own counters leave `secondsSinceLastEvent` null. |
| `test_MA_05_agent_counters.py` (UBS-74) | `ingest_agent_counters` dimension handling, cardinality folding, out-of-window drop, and that it leaves `_last_event_at` alone while `ingest_counters` still sets it; `AgentCounterSampler`'s first-sample baseline, delta arithmetic, registry-reset rebaselining, and per-bucket placement. |

Run: `uv run pytest tests/unit tests/integration -v` (183 tests, whole repo)
· lint/types: `uv run ruff check .` and `uv run mypy apps/agent/src` clean on
this package (pre-existing issues in `parser/cli.py`, `logs/
offset_tracker.py`, `run_streamer.py`, `demo_suite.py`, and the still-broken
`telemetry.py`/`health.py` shared-model stubs are untouched, out of scope
here).

**Known gaps, not closed here**: consecutive-failure streak tracking
(client alert 3's "≥10 consecutive failures") has no rule kind or data
producer; Backend Publisher doesn't exist, so `BackendUnreachable` has no
data; `SighupRuleReloader.install()` has no real process to be called from
yet (M1 Log Monitor / an agent supervisor loop). All are documented,
deliberate deferrals, not oversights.

## 7. Counter producers (UBS-73 / UBS-74)

The session-message and callback counters listed above as gaps now have
real producers, so five rules that could previously only read 0 fire on
live data.

| Counter | Produced by | Consumed by |
| --- | --- | --- |
| `logons`, `logouts` | `parser.metrics_event.derive_session_counters` | `FixSessionDown` |
| `seq_gaps`, `seq_gap_messages`, `seq_regressions` | same, from `FixTelemetry.seq_gap` (`SeqTracker`) | `SeqGapDetected` |
| `clock_skew_events` | same, from `FixTelemetry.clock_skew` (`parse_fix_timestamp`) | `ClockSkew` |
| `callback_failures`, `callback_delivered`, `callback_queue_dropped` | `metrics.agent_counters.AgentCounterSampler`, sampling the dispatcher's `CounterRegistry` | `CallbackFailing` |
| `log_lines_read`, `parse_errors` (dimension `reason`) | `parser.metrics_event.derive_parser_counters` (UBS-18) | `ParseErrorRate` |

Two different paths, for a reason. The session counters come off a real
parsed FIX line, so they ride the existing `ingest_counters` path with
`SESSION_DIMS` (`instance_id`, `session_id`). The callback counters have no
`ParsedMessageEvent` behind them at all and live in a monotonic
since-startup registry, so they need `ingest_agent_counters` plus a delta
sampler — and that separate write path deliberately does **not** touch
`_last_event_at`, because the agent's own dispatcher retrying is not
evidence that Magic is still producing log activity.

`heartbeat_timeouts` is still unproduced, by choice: a timeout is the
*absence* of a message, which no per-message derivation can observe. It
belongs to the Health Reporter's periodic tick. `FixSessionDown` sums it
with `logouts` and defaults a missing counter to 0, so the rule works
correctly without it.

`parse_errors` and `log_lines_read` are `parse_error_rate`'s numerator and
denominator, so they ride `ingest_agent_counters` too — every line has to be
counted, including the ones that produced no `ParsedMessageEvent` at all.
Only hard failures count: `bad_timestamp` and `unknown_msg_type` are soft
warnings on a line that parsed, and folding them in would have the rule
firing on well-formed messages.

Demo: `make rules-quickstart` walks one FIX session from healthy through a
reject burst, a rising reject rate, latency degradation, a sequence gap,
clock skew, a forced logout, the agent's own callbacks failing, and the
absence/lifecycle/safety rules — 13 of the 14 configured rules fire, each
traceable to a raw log line printed in the same run. Only
`BackendUnreachable` stays silent, correctly: nothing produces
`publish_failures` until the Backend Publisher exists. Runbook:
`docs/plan/rule-engine-demo.md`.
