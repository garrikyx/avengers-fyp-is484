"""RE-03: each of the 14 default rules (spec 005 §1.2) against a snapshot
built to sit just below/at/above its threshold.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from rule_fixtures import (
    make_gauges,
    make_indicator,
    make_indicators,
    make_latency,
    make_snapshot,
)
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import RuleConfig
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.metrics import MetricsSnapshot

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)


def _rule(name: str) -> RuleConfig:
    return next(r for r in DEFAULT_RULES if r.name == name)


def _engine(rule: RuleConfig) -> RuleEngine:
    return RuleEngine(
        rules=(rule,),
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
    )


def _fire(rule: RuleConfig, snapshot: MetricsSnapshot) -> list[AlertEvent]:
    engine = _engine(rule)
    engine.evaluate(snapshot, _T0)  # -> pending
    t1 = _T0 + timedelta(seconds=rule.for_seconds + 1)
    return engine.evaluate(snapshot, t1)


def test_default_rules_are_14_unique_names() -> None:
    assert len(DEFAULT_RULES) == 14
    assert len({r.name for r in DEFAULT_RULES}) == 14


def test_high_reject_rate_fires_warning_then_escalates_to_critical() -> None:
    rule = _rule("HighRejectRate")
    engine = _engine(rule)
    warning = make_snapshot(
        now=_T0, indicators=make_indicators(reject_rate=make_indicator(0.04, 25, False))
    )
    engine.evaluate(warning, _T0)
    t1 = _T0 + timedelta(seconds=rule.for_seconds + 1)
    fired = engine.evaluate(warning, t1)
    assert fired[0].severity == "warning"

    critical = make_snapshot(
        now=_T0, indicators=make_indicators(reject_rate=make_indicator(0.06, 25, False))
    )
    t2 = t1 + timedelta(seconds=1)
    escalated = engine.evaluate(critical, t2)
    assert len(escalated) == 1
    assert escalated[0].severity == "critical"
    assert escalated[0].status == "firing"
    assert escalated[0].alert_id == fired[0].alert_id


def test_high_reject_rate_below_warning_never_fires() -> None:
    rule = _rule("HighRejectRate")
    snapshot = make_snapshot(
        now=_T0, indicators=make_indicators(reject_rate=make_indicator(0.02, 25, False))
    )
    assert _fire(rule, snapshot) == []


def test_ack_latency_breach_warning_and_critical_tiers() -> None:
    rule = _rule("AckLatencyBreach")
    warning = make_snapshot(now=_T0, latency={"ack_latency_ms": make_latency(600, 60)})
    assert _fire(rule, warning)[0].severity == "warning"

    critical = make_snapshot(
        now=_T0, latency={"ack_latency_ms": make_latency(1500, 60)}
    )
    assert _fire(rule, critical)[0].severity == "critical"


def test_ack_latency_breach_insufficient_samples_never_fires() -> None:
    rule = _rule("AckLatencyBreach")
    snapshot = make_snapshot(
        now=_T0, latency={"ack_latency_ms": make_latency(1500, 10)}
    )
    assert _fire(rule, snapshot) == []


def test_parse_error_rate_warning_and_critical_tiers() -> None:
    rule = _rule("ParseErrorRate")
    warning = make_snapshot(
        now=_T0,
        indicators=make_indicators(parse_error_rate=make_indicator(0.02, 25, False)),
    )
    assert _fire(rule, warning)[0].severity == "warning"

    critical = make_snapshot(
        now=_T0,
        indicators=make_indicators(parse_error_rate=make_indicator(0.30, 25, False)),
    )
    assert _fire(rule, critical)[0].severity == "critical"


def test_reject_spike_fires_above_50_in_1m() -> None:
    rule = _rule("RejectSpike")
    snapshot = make_snapshot(
        now=_T0, window="1m", counters={"orders_rejected": Decimal(51)}
    )
    assert _fire(rule, snapshot)[0].severity == "warning"


def test_cancel_reject_spike_fires_above_20_in_5m() -> None:
    rule = _rule("CancelRejectSpike")
    snapshot = make_snapshot(now=_T0, counters={"cancel_rejects": Decimal(21)})
    assert _fire(rule, snapshot)[0].severity == "warning"


def test_session_rejects_fires_above_5_in_5m_as_critical() -> None:
    rule = _rule("SessionRejects")
    snapshot = make_snapshot(now=_T0, counters={"session_rejects": Decimal(6)})
    assert _fire(rule, snapshot)[0].severity == "critical"


def test_pending_order_timeout_reads_the_gauge() -> None:
    rule = _rule("PendingOrderTimeout")
    stuck = make_snapshot(now=_T0, gauges=make_gauges(oldest_pending_age_seconds=45.0))
    assert _fire(rule, stuck)[0].severity == "warning"

    fine = make_snapshot(now=_T0, gauges=make_gauges(oldest_pending_age_seconds=5.0))
    assert _fire(rule, fine) == []

    nothing_pending = make_snapshot(now=_T0, gauges=make_gauges())
    assert _fire(rule, nothing_pending) == []


def test_no_log_activity_fires_on_a_cold_window() -> None:
    rule = _rule("NoLogActivity")
    dead = make_snapshot(now=_T0, window="1m", empty=True)
    assert _fire(rule, dead)[0].severity == "critical"

    alive = make_snapshot(
        now=_T0, window="1m", counters={"messages_total": Decimal(500)}
    )
    assert _fire(rule, alive) == []


def test_no_executions_requires_the_orders_submitted_guard() -> None:
    rule = _rule("NoExecutions")
    no_orders_at_all = make_snapshot(now=_T0, window="15m", counters={})
    assert _fire(rule, no_orders_at_all) == []  # guard unmet, not a failure

    orders_but_no_fills = make_snapshot(
        now=_T0, window="15m", counters={"orders_submitted": Decimal(10)}
    )
    assert _fire(rule, orders_but_no_fills)[0].severity == "warning"


def test_fix_session_down_fires_on_either_counter() -> None:
    rule = _rule("FixSessionDown")
    only_heartbeat_timeout = make_snapshot(
        now=_T0, window="1m", counters={"heartbeat_timeouts": Decimal(1)}
    )
    assert _fire(rule, only_heartbeat_timeout)[0].severity == "critical"


def test_unwired_counter_rules_read_as_no_fire_not_crash() -> None:
    # SeqGapDetected/ClockSkew/CallbackFailing/BackendUnreachable have no
    # producer yet — an otherwise-normal snapshot simply lacks their
    # counters entirely. Must read as "doesn't fire", never raise.
    for name in (
        "SeqGapDetected",
        "ClockSkew",
        "CallbackFailing",
        "BackendUnreachable",
    ):
        rule = _rule(name)
        normal_snapshot = make_snapshot(
            now=_T0,
            window=rule.window,
            counters={"orders_submitted": Decimal(5), "orders_acked": Decimal(5)},
        )
        assert _fire(rule, normal_snapshot) == []
