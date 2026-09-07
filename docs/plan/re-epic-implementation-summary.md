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
| `ParseErrorRate` | rate | warning@1%, critical@25% | 5m | formula-ready, no producer |
| `NoLogActivity` | absence | critical@0 (`messages_total`) | 1m | wired |
| `NoExecutions` | absence (guarded) | warning@0 while `orders_submitted`>0 | 15m | wired |
| `FixSessionDown` | threshold | critical@1 (`logouts` or `heartbeat_timeouts`) | 1m | no producer |
| `SeqGapDetected` | threshold | warning@0 | 1m | no producer |
| `ClockSkew` | threshold | warning@10 | 5m | no producer |
| `CallbackFailing` | threshold | warning@3 | 5m | no Callback Dispatcher yet |
| `BackendUnreachable` | threshold | warning@5 | 1m | no Backend Publisher yet |

"No producer" rules read as 0/no-fire structurally rather than raising —
same posture MA-04 established for `parseErrorRate`. `HighRejectRate`,
`AckLatencyBreach`, and `ParseErrorRate`'s thresholds are client-confirmed;
`PendingOrderTimeout`'s 30s has no spec or client number — see its
docstring in `defaults.py` for the domain reasoning.

`DEFAULT_RULES` is Python-level config, not YAML — wiring to
`config/rules.yaml` (real parsing, SIGHUP reload) is a separate,
pre-existing gap (`config.py` is empty for every config file in the agent,
not a rules-specific one).

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

## 5. Verified — what 45 new tests prove

| File | Proves |
| --- | --- |
| `test_RE_01_fsm.py` | All five transitions, `for`/`resolveAfter` timing, renotify + `notificationCount`, `alertId` stability through one occurrence and rotation after resolution, startup grace. |
| `test_RE_02_evaluators.py` | All 5 `RuleKind` evaluators, tier selection (highest crossed tier wins), insufficient-data paths recomputed from `denominator`/`count` against *this rule's* `min_samples` (not MA-04's own default), `NoExecutions`'s guard, absent counters as zero, a cold window crashing nothing. |
| `test_RE_03_safety.py` | `maxActiveAlerts`/`AlertStorm` (one notification, suppression persists, clears once under cap), silence suppressing notification but not state, dependent suppression's one-tick lag, schedule-inactive skip. |
| `test_RE_04_default_rules.py` | Each of the 14 default rules at its own threshold boundary, `HighRejectRate` escalating warning→critical on the same `alertId`, rules with unwired counters reading as no-fire. |
| `tests/integration/agent/test_RE_integration.py` | Real `MetricsAggregator`/`LatencyCorrelator`/`snapshot()` output actually drives `RuleEngine.evaluate()` correctly — one rule per snapshot substructure (indicator, latency, gauge, counter), not the hand-built `MetricsSnapshot` fixtures the rest of this suite uses. Caught a real gap: `snapshot()`'s `min_sample_size` nulls latency percentiles independent of what a given rule's own `min_samples` would accept. |

Run: `uv run pytest tests/unit tests/integration -v` (161 tests, whole repo)
· lint/types: `uv run ruff check .` and `uv run mypy apps/agent/src` clean on
this package (pre-existing issues in `parser/cli.py`, `logs/
offset_tracker.py`, `run_streamer.py`, `demo_suite.py`, and the still-broken
`telemetry.py`/`health.py` shared-model stubs are untouched, out of scope
here).

**Known gaps, not closed here**: consecutive-failure streak tracking
(client alert 3's "≥10 consecutive failures") has no rule kind or data
producer; session-message counters (`logouts`, `heartbeat_timeouts`,
`seq_gaps`, `clock_skew_events`) aren't derived anywhere yet; Callback
Dispatcher and Backend Publisher don't exist, so their self-health rules
have no data; `config/rules.yaml` YAML loading and SIGHUP reload aren't
built. All are documented, deliberate deferrals, not oversights.
