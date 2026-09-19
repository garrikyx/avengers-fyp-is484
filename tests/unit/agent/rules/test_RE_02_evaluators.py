"""RE-02: the per-`RuleKind` evaluators, tested directly against hand-built
`MetricsSnapshot` fixtures (no engine/FSM involved).
"""

from datetime import UTC, datetime
from decimal import Decimal

from rule_fixtures import (
    make_gauges,
    make_indicator,
    make_indicators,
    make_latency,
    make_snapshot,
)
from telemetry_agent.rules.engine import _matched_tier, _read_observed
from telemetry_agent.rules.types import RuleConfig, RuleKind, SeverityTier, ValueSource

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)

_TIERS = (
    SeverityTier("warning", Decimal("0.03")),
    SeverityTier("critical", Decimal("0.05")),
)


def _rate_rule(min_samples: int = 20) -> RuleConfig:
    return RuleConfig(
        name="R",
        kind=RuleKind.RATE,
        source=ValueSource.INDICATOR,
        metric="reject_rate",
        operator=">",
        tiers=_TIERS,
        window="5m",
        min_samples=min_samples,
    )


def test_rate_evaluator_returns_value_when_sufficient() -> None:
    rule = _rate_rule(min_samples=20)
    snapshot = make_snapshot(
        now=_T0,
        indicators=make_indicators(
            reject_rate=make_indicator(0.06, denominator=25, low_confidence=False)
        ),
    )
    assert _read_observed(rule, snapshot) == Decimal("0.06")


def test_rate_evaluator_insufficient_when_denominator_below_rules_own_min_samples() -> (
    None
):
    # denominator(15) < this rule's min_samples(20) -> insufficient, even
    # though the fixture's own low_confidence flag says False.
    rule = _rate_rule(min_samples=20)
    snapshot = make_snapshot(
        now=_T0,
        indicators=make_indicators(
            reject_rate=make_indicator(0.06, denominator=15, low_confidence=False)
        ),
    )
    assert _read_observed(rule, snapshot) is None


def test_rate_evaluator_null_when_denominator_is_zero() -> None:
    rule = _rate_rule()
    snapshot = make_snapshot(
        now=_T0, indicators=make_indicators()
    )  # default: value=None
    assert _read_observed(rule, snapshot) is None


def _latency_rule(min_samples: int = 50) -> RuleConfig:
    return RuleConfig(
        name="L",
        kind=RuleKind.LATENCY,
        source=ValueSource.LATENCY_P95,
        metric="ack_latency_ms",
        operator=">",
        tiers=(
            SeverityTier("warning", Decimal(500)),
            SeverityTier("critical", Decimal(1000)),
        ),
        window="5m",
        min_samples=min_samples,
    )


def test_latency_evaluator_returns_p95_when_sufficient() -> None:
    rule = _latency_rule(min_samples=50)
    snapshot = make_snapshot(
        now=_T0, latency={"ack_latency_ms": make_latency(p95=1200, count=60)}
    )
    assert _read_observed(rule, snapshot) == Decimal("1200")


def test_latency_evaluator_insufficient_when_count_below_rules_own_min_samples() -> (
    None
):
    # count(30) is >= MA-04's own default(20) so p95 is a real, non-null
    # number in the fixture — but below this rule's min_samples(50), so the
    # rule must still treat it as insufficient rather than trusting p95.
    rule = _latency_rule(min_samples=50)
    snapshot = make_snapshot(
        now=_T0, latency={"ack_latency_ms": make_latency(p95=600, count=30)}
    )
    assert _read_observed(rule, snapshot) is None


def test_latency_evaluator_none_when_histogram_absent() -> None:
    rule = _latency_rule()
    snapshot = make_snapshot(now=_T0, latency={})
    assert _read_observed(rule, snapshot) is None


def _threshold_rule(**overrides: object) -> RuleConfig:
    kwargs: dict[str, object] = dict(
        name="T",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.COUNTER,
        metric="orders_rejected",
        operator=">",
        tiers=(SeverityTier("warning", Decimal(50)),),
        window="1m",
    )
    kwargs.update(overrides)
    return RuleConfig(**kwargs)  # type: ignore[arg-type]


def test_threshold_evaluator_reads_counter() -> None:
    rule = _threshold_rule()
    snapshot = make_snapshot(now=_T0, counters={"orders_rejected": Decimal(75)})
    assert _read_observed(rule, snapshot) == Decimal(75)


def test_threshold_evaluator_treats_absent_counter_as_zero() -> None:
    rule = _threshold_rule()
    snapshot = make_snapshot(now=_T0, counters={})
    assert _read_observed(rule, snapshot) == Decimal(0)


def test_threshold_evaluator_sums_extra_counters_for_or_semantics() -> None:
    # FixSessionDown-shaped: logouts OR heartbeat_timeouts, either >= 1.
    rule = _threshold_rule(
        metric="logouts", extra_counters=("heartbeat_timeouts",), operator=">="
    )
    snapshot = make_snapshot(
        now=_T0, counters={"logouts": Decimal(0), "heartbeat_timeouts": Decimal(1)}
    )
    assert _read_observed(rule, snapshot) == Decimal(1)


def _gauge_rule() -> RuleConfig:
    return RuleConfig(
        name="G",
        kind=RuleKind.THRESHOLD,
        source=ValueSource.GAUGE,
        metric="oldest_pending_age_seconds",
        operator=">",
        tiers=(SeverityTier("warning", Decimal(30)),),
        window=None,
    )


def test_gauge_evaluator_reads_gauge_value() -> None:
    rule = _gauge_rule()
    snapshot = make_snapshot(
        now=_T0, gauges=make_gauges(oldest_pending_age_seconds=45.0)
    )
    assert _read_observed(rule, snapshot) == Decimal("45.0")


def test_gauge_evaluator_none_when_gauge_is_none() -> None:
    rule = _gauge_rule()
    snapshot = make_snapshot(
        now=_T0, gauges=make_gauges(oldest_pending_age_seconds=None)
    )
    assert _read_observed(rule, snapshot) is None


def _absence_rule(guard_metric: str | None = None) -> RuleConfig:
    return RuleConfig(
        name="A",
        kind=RuleKind.ABSENCE,
        source=ValueSource.COUNTER,
        metric="executions",
        operator="==",
        tiers=(SeverityTier("warning", Decimal(0)),),
        window="15m",
        guard_metric=guard_metric,
    )


def test_absence_evaluator_fires_when_guard_satisfied_and_metric_is_zero() -> None:
    rule = _absence_rule(guard_metric="orders_submitted")
    snapshot = make_snapshot(now=_T0, counters={"orders_submitted": Decimal(10)})
    assert _read_observed(rule, snapshot) == Decimal(0)


def test_absence_evaluator_guard_unmet_returns_none_not_zero() -> None:
    # No orders submitted at all -> "no executions" is meaningless, not a failure.
    rule = _absence_rule(guard_metric="orders_submitted")
    snapshot = make_snapshot(now=_T0, counters={})
    assert _read_observed(rule, snapshot) is None


def test_absence_evaluator_without_guard_reads_metric_directly() -> None:
    rule = _absence_rule(guard_metric=None)
    snapshot = make_snapshot(now=_T0, counters={})
    assert _read_observed(rule, snapshot) == Decimal(0)


def test_matched_tier_picks_the_highest_crossed_tier() -> None:
    tiers = (SeverityTier("warning", Decimal(3)), SeverityTier("critical", Decimal(5)))
    assert _matched_tier(Decimal(2), tiers, ">") is None
    assert _matched_tier(Decimal(4), tiers, ">").severity == "warning"
    assert _matched_tier(Decimal(6), tiers, ">").severity == "critical"


def test_observed_is_none_for_all_kinds_when_no_groups_at_all() -> None:
    # A cold window (nothing ingested) must not crash any evaluator.
    empty = make_snapshot(now=_T0, empty=True)
    assert _read_observed(_rate_rule(), empty) is None
    assert _read_observed(_latency_rule(), empty) is None
    assert _read_observed(_threshold_rule(), empty) == Decimal(0)
    assert _read_observed(_absence_rule("orders_submitted"), empty) is None
