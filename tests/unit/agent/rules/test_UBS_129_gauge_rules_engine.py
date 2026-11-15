"""UBS-129 engine behaviour for gauge-sourced rules.

* `_metric_context` reports the real gauge value (FR-RUL-016), not a fabricated
  `0.0` counter, for every gauge rule (`BackendUnreachable`,
  `PendingOrderTimeout`, the host rules) and even when no group was ingested.
* A firing alert on a Host Monitor gauge is held while that gauge is missing
  (FR-MET-034: unreadable is "no data", never "condition clear"). Other gauge
  rules, where a missing value genuinely means "clear", are unchanged.
"""

from datetime import timedelta

import pytest
from rule_fixtures import (
    T0,
    make_gauges,
    make_snapshot,
    shipped_rule,
    single_rule_engine,
)
from telemetry_agent.rules.engine import RuleEngine, _metric_context
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.metrics import Gauges


def _step(
    engine: RuleEngine, seconds: float, gauges: Gauges, *, empty: bool = False
) -> list[AlertEvent]:
    now = T0 + timedelta(seconds=seconds)
    return engine.evaluate(make_snapshot(now=now, gauges=gauges, empty=empty), now)


def _fire(engine: RuleEngine, rule_for_seconds: int, gauges: Gauges) -> AlertEvent:
    assert _step(engine, 0, gauges) == []
    fired = _step(engine, rule_for_seconds, gauges)
    assert len(fired) == 1
    return fired[0]


# --- _metric_context regression ---------------------------------------------------


@pytest.mark.parametrize("source", ["defaults", "yaml"])
def test_fr_rul_016_backend_unreachable_context_is_the_real_gauge(source: str) -> None:
    rule = shipped_rule(source, "BackendUnreachable")
    alert = _fire(
        single_rule_engine(rule),
        rule.for_seconds,
        make_gauges(consecutive_publish_failures=7),
    )
    assert alert.metric_context == {"consecutive_publish_failures": 7.0}
    assert alert.observed_value == 7.0


@pytest.mark.parametrize("source", ["defaults", "yaml"])
def test_fr_rul_016_pending_order_timeout_context_is_the_real_gauge(
    source: str,
) -> None:
    rule = shipped_rule(source, "PendingOrderTimeout")
    alert = _fire(
        single_rule_engine(rule),
        rule.for_seconds,
        make_gauges(pending_orders=3, oldest_pending_age_seconds=45.0),
    )
    assert alert.metric_context == {"oldest_pending_age_seconds": 45.0}


def test_fr_rul_016_gauge_context_survives_a_window_with_no_ingested_events() -> None:
    """Magic down means silent logs, so no group: the gauge is still reported."""
    rule = shipped_rule("defaults", "ApplicationDown")
    engine = single_rule_engine(rule)
    gauges = make_gauges(magic_process_up=0.0)
    _step(engine, 0, gauges, empty=True)
    (alert,) = _step(engine, rule.for_seconds, gauges, empty=True)
    assert alert.metric_context == {"magic_process_up": 0.0}


def test_fr_rul_016_an_unread_gauge_adds_nothing_to_the_context() -> None:
    rule = shipped_rule("defaults", "HostDiskFull")
    engine = single_rule_engine(rule)
    _fire(engine, rule.for_seconds, make_gauges(host_disk_used_ratio=0.96))
    snap = make_snapshot(now=T0, gauges=make_gauges())
    assert _metric_context(rule, snap) == {}


# --- unreadable host gauge holds a live alert -------------------------------------

_HOST_CASES = [
    ("HostDiskFull", "host_disk_used_ratio", 0.96, 0.40),
    ("HostMemoryHigh", "host_memory_used_ratio", 0.97, 0.40),
    ("ApplicationDown", "magic_process_up", 0.0, 1.0),
]


@pytest.mark.parametrize(("name", "metric", "bad", "good"), _HOST_CASES)
def test_fr_met_034_a_missing_host_gauge_does_not_resolve_a_firing_alert(
    name: str, metric: str, bad: float, good: float
) -> None:
    rule = shipped_rule("defaults", name)
    engine = single_rule_engine(rule)
    _fire(engine, rule.for_seconds, make_gauges(**{metric: bad}))
    start = rule.for_seconds

    # Well past resolveAfter with nothing readable: still firing, no event.
    resolve = rule.resolve_after_seconds
    for extra in (0, 10, resolve + 1, 3 * resolve):
        assert _step(engine, start + extra, make_gauges()) == []
    assert engine.active_alert_count() == 1


@pytest.mark.parametrize(("name", "metric", "bad", "good"), _HOST_CASES)
def test_fr_met_034_the_alert_resolves_normally_once_data_returns_clear(
    name: str, metric: str, bad: float, good: float
) -> None:
    rule = shipped_rule("defaults", name)
    engine = single_rule_engine(rule)
    _fire(engine, rule.for_seconds, make_gauges(**{metric: bad}))
    t = rule.for_seconds + 10_000
    assert _step(engine, t, make_gauges()) == []  # a long outage of the reading

    assert _step(engine, t + 1, make_gauges(**{metric: good})) == []  # resolving
    resolved = _step(
        engine, t + 1 + rule.resolve_after_seconds, make_gauges(**{metric: good})
    )
    assert [(a.rule_name, a.status) for a in resolved] == [(name, "resolved")]


@pytest.mark.parametrize(("name", "metric", "bad", "good"), _HOST_CASES)
def test_fr_met_034_data_returning_still_bad_keeps_the_same_alert_silently(
    name: str, metric: str, bad: float, good: float
) -> None:
    rule = shipped_rule("defaults", name)
    engine = single_rule_engine(rule)
    first = _fire(engine, rule.for_seconds, make_gauges(**{metric: bad}))
    t = rule.for_seconds + 1000
    _step(engine, t, make_gauges())
    assert _step(engine, t + 1, make_gauges(**{metric: bad})) == []
    assert engine.active_alert_count() == 1
    assert first.status == "firing"


def test_fr_met_034_missing_data_while_resolving_does_not_finish_the_resolve() -> None:
    rule = shipped_rule("defaults", "HostDiskFull")
    engine = single_rule_engine(rule)
    ok = make_gauges(host_disk_used_ratio=0.40)
    _fire(engine, rule.for_seconds, make_gauges(host_disk_used_ratio=0.96))
    t = rule.for_seconds
    assert _step(engine, t + 1, ok) == []  # FIRING -> RESOLVING

    # Reading lost for longer than resolveAfter: must not resolve on silence.
    assert _step(engine, t + 1 + rule.resolve_after_seconds + 50, make_gauges()) == []
    assert engine.active_alert_count() == 1

    # Back and clear: the resolve window is counted from the readable reading.
    back = t + 1 + rule.resolve_after_seconds + 60
    assert _step(engine, back, ok) == []
    assert _step(engine, back + rule.resolve_after_seconds - 1, ok) == []
    (resolved,) = _step(engine, back + rule.resolve_after_seconds, ok)
    assert resolved.status == "resolved"


def test_fr_met_034_a_pending_alert_on_a_missing_gauge_is_dropped_not_held() -> None:
    """Only a live (firing) alert is held; a hold that never fired just resets."""
    rule = shipped_rule("defaults", "HostDiskFull")
    engine = single_rule_engine(rule)
    bad = make_gauges(host_disk_used_ratio=0.96)
    assert _step(engine, 0, bad) == []  # pending
    assert _step(engine, 30, make_gauges()) == []  # gauge lost: pending dropped
    assert _step(engine, 31, bad) == []  # a fresh hold starts
    assert _step(engine, 31 + rule.for_seconds - 1, bad) == []
    assert len(_step(engine, 31 + rule.for_seconds, bad)) == 1


# --- other gauge rules are unchanged ----------------------------------------------


def test_fr_met_031_a_missing_non_host_gauge_still_reads_as_clear() -> None:
    """`oldest_pending_age_seconds` is None when no order is pending: that is
    "condition clear", so PendingOrderTimeout still resolves after resolveAfter."""
    rule = shipped_rule("defaults", "PendingOrderTimeout")
    engine = single_rule_engine(rule)
    _fire(
        engine,
        rule.for_seconds,
        make_gauges(pending_orders=1, oldest_pending_age_seconds=45.0),
    )
    t = rule.for_seconds
    assert _step(engine, t + 1, make_gauges()) == []
    (resolved,) = _step(engine, t + 1 + rule.resolve_after_seconds, make_gauges())
    assert resolved.status == "resolved"
    assert engine.active_alert_count() == 0
