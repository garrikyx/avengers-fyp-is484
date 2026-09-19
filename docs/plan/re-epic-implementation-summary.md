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

Run: `uv run pytest tests/unit tests/integration -v` (183 tests, whole repo)
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
have no data; `SighupRuleReloader.install()` has no real process to be
called from yet (M1 Log Monitor / an agent supervisor loop). All are
documented, deliberate deferrals, not oversights.
