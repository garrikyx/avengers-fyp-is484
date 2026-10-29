# UBS-25–29 implementation notes (D2 anomaly detection)

Epic UBS-6 "[D2] Anomaly Detection & Trend Analysis". Spec:
[005 §7](../specs/005-alerting-and-callbacks.md),
[007 §3.1](../specs/007-api-contracts.md).

## Conflict with spec 000 §3.2

Spec 000 lists "anomaly detection and adaptive thresholds" as Day-2/out of scope. The
tickets are scheduled (Sprint 5), so the scope note in 000 now says what was pulled
forward. Adaptive thresholds, durable baselines and seasonality are still out.

## Ticket wording problems (Jira text not edited)

- **UBS-28 / UBS-29 narratives are swapped.** UBS-28 is titled "Execution Issues" and
  its formula/example is `execution_issue_rate`, but its story sentence says "FIX parser
  failures"; UBS-29 is the reverse. Built to the titles and formulas: 28 = execution
  issues, 29 = parser failures.
- **UBS-26's example arithmetic.** 400ms against a 100ms baseline is +300%, not +400%.
  The code reports +300%.
- **UBS-28's "execution issue" has no definition** in spec 004. Working definition:
  rejected orders + rejected cancel/replace + expired orders, over orders submitted +
  cancel requests + replaces. It overlaps UBS-25's reject rate, so a reject spike will
  raise both alerts. Confirm with the sponsor; the definition is one table in
  `rules/baseline.py` (`ANOMALY_METRICS`).
- UBS-29's `messages_processed` is `log_lines_read` (the existing `parse_error_rate`
  denominator).

## Design decisions

- **Reuse the Rule Engine** (new `RuleKind.ANOMALY`) rather than a separate detector:
  tiers, `for`/resolve hysteresis, silences, callbacks, backend publishing and the Teams
  push all apply with no new wiring. The engine's observed value is the deviation.
- **Config in `config/anomaly.yaml`**, the scaffold's stub, keeping its
  `baseline_window_minutes` / `minimum_samples` keys. `load_rules()` appends its rules,
  and the reloader watches its mtime.
- **Baseline strictly precedes the judged window** (a sample sits pending one window
  before joining history) and excludes anomalous windows. Cost: a permanent shift keeps
  alerting until reload/restart.
- **UBS-27 is backend-side**: the agent only holds 15 minutes, the Metric Store holds 6
  hours and already groups by `rejectReason`. It does not alert; it answers "which
  reasons are rising".

## Not done / follow-ups

- No NL intent for UBS-27 yet (catalogue, rule matcher, renderer); Teams and MCP reach
  it only once that exists. The REST endpoint is ready for it.
- Test mode (`--test-rule`) replays too few minutes to warm a 60-minute baseline;
  anomaly rules need a long replay to show a verdict.
- Baseline state is in agent memory and restarts empty (about `4 x window` of warm-up).
