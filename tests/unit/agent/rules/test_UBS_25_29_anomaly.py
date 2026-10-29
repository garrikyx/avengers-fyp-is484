"""D2 anomaly rules (UBS-25 reject rate, UBS-26 latency, UBS-28 execution
issues, UBS-29 parser failures): a metric against its rolling baseline.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from rule_fixtures import make_latency, make_snapshot
from telemetry_agent.rules.config_loader import load_anomaly_rules
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import RuleConfig, RuleKind, SeverityTier, ValueSource
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.metrics import MetricsSnapshot

_T0 = datetime(2026, 10, 29, 4, 0, 0, tzinfo=UTC)
_WINDOW = timedelta(minutes=5)


def _rule(metric: str, *, for_seconds: int = 0, min_samples: int = 20) -> RuleConfig:
    return RuleConfig(
        name=f"Abnormal-{metric}",
        kind=RuleKind.ANOMALY,
        source=(
            ValueSource.LATENCY_P95
            if metric == "ack_latency_ms"
            else ValueSource.INDICATOR
        ),
        metric=metric,
        operator=">",
        tiers=(SeverityTier("warning", Decimal("0.5")),),
        window="5m",
        min_samples=min_samples,
        for_seconds=for_seconds,
        baseline_seconds=3600,
        baseline_min_samples=100,
    )


def _engine(rule: RuleConfig) -> RuleEngine:
    return RuleEngine(
        rules=(rule,),
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0,
    )


def _ratio_snapshot(
    metric: str, *, bad: int, total: int, at: datetime
) -> MetricsSnapshot:
    good = total - bad
    counters = {
        "reject_rate": {"orders_acked": good, "orders_rejected": bad},
        "parser_failure_rate": {"log_lines_read": total, "parse_errors": bad},
        "execution_issue_rate": {"orders_submitted": total, "orders_rejected": bad},
    }[metric]
    return make_snapshot(now=at, counters={k: Decimal(v) for k, v in counters.items()})


def _warm_up(
    engine: RuleEngine, make: Callable[[datetime], MetricsSnapshot], windows: int
) -> datetime:
    """`windows` quiet 5m ticks; returns the time of the last one."""
    at = _T0
    for _ in range(windows):
        at += _WINDOW
        assert engine.evaluate(make(at), at) == []
    return at


def _fire(
    engine: RuleEngine, snapshot: MetricsSnapshot, at: datetime
) -> list[AlertEvent]:
    engine.evaluate(snapshot, at)  # -> pending
    return engine.evaluate(snapshot, at + timedelta(seconds=10))


@pytest.mark.parametrize(
    ("metric", "label"),
    [
        ("reject_rate", "reject rate"),
        ("execution_issue_rate", "execution issue rate"),
        ("parser_failure_rate", "parser failure rate"),
    ],
)
def test_ratio_deviation_fires_with_the_ticket_explanation(
    metric: str, label: str
) -> None:
    engine = _engine(_rule(metric))
    last = _warm_up(
        engine, lambda at: _ratio_snapshot(metric, bad=6, total=1000, at=at), 6
    )

    at = last + _WINDOW
    [alert] = _fire(engine, _ratio_snapshot(metric, bad=18, total=1000, at=at), at)

    assert alert.status == "firing"
    assert alert.matched_condition == (
        f"Abnormal {label} detected on magic-prod-01. "
        f"{label.capitalize()} is 1.8% compared with its 0.6% baseline "
        "(+200%) over the last 5 minutes"
    )
    assert alert.observed_value == pytest.approx(2.0)
    assert alert.threshold == 0.5
    assert alert.metric_context["baseline"] == pytest.approx(0.006)
    assert alert.metric_context["current"] == pytest.approx(0.018)


def test_deviation_at_or_below_threshold_does_not_alert() -> None:
    engine = _engine(_rule("reject_rate"))
    last = _warm_up(
        engine, lambda at: _ratio_snapshot("reject_rate", bad=10, total=1000, at=at), 6
    )
    at = last + _WINDOW
    # 1.5% is exactly 1.5x the 1.0% baseline: the AC says "more than".
    assert (
        _fire(engine, _ratio_snapshot("reject_rate", bad=15, total=1000, at=at), at)
        == []
    )


def test_no_alert_until_the_baseline_has_enough_windows() -> None:
    engine = _engine(_rule("reject_rate"))
    last = _warm_up(
        engine, lambda at: _ratio_snapshot("reject_rate", bad=6, total=1000, at=at), 2
    )
    at = last + _WINDOW  # the judged tick promotes the 2nd window: 2 < 3 in baseline
    assert (
        _fire(engine, _ratio_snapshot("reject_rate", bad=60, total=1000, at=at), at)
        == []
    )


def test_no_alert_when_the_baseline_has_too_few_events() -> None:
    engine = _engine(_rule("reject_rate"))
    last = _warm_up(
        engine, lambda at: _ratio_snapshot("reject_rate", bad=1, total=24, at=at), 4
    )
    at = last + _WINDOW  # 4 baseline windows x 24 events = 96 < 100
    assert (
        _fire(engine, _ratio_snapshot("reject_rate", bad=12, total=24, at=at), at) == []
    )


def test_a_zero_baseline_is_not_judged() -> None:
    engine = _engine(_rule("reject_rate"))
    last = _warm_up(
        engine, lambda at: _ratio_snapshot("reject_rate", bad=0, total=1000, at=at), 6
    )
    at = last + _WINDOW
    assert (
        _fire(engine, _ratio_snapshot("reject_rate", bad=50, total=1000, at=at), at)
        == []
    )


def test_a_thin_current_window_is_not_judged() -> None:
    engine = _engine(_rule("reject_rate", min_samples=50))
    last = _warm_up(
        engine, lambda at: _ratio_snapshot("reject_rate", bad=6, total=1000, at=at), 6
    )
    at = last + _WINDOW
    assert (
        _fire(engine, _ratio_snapshot("reject_rate", bad=10, total=40, at=at), at) == []
    )


def test_an_anomalous_window_does_not_become_the_baseline() -> None:
    engine = _engine(_rule("reject_rate"))
    last = _warm_up(
        engine, lambda at: _ratio_snapshot("reject_rate", bad=6, total=1000, at=at), 6
    )
    for _ in range(4):  # a long incident, longer than the whole history needs
        last += _WINDOW
        alerts = _fire(
            engine, _ratio_snapshot("reject_rate", bad=18, total=1000, at=last), last
        )
        status = engine.status_of("Abnormal-reject_rate")
        assert status is not None and status.value == "firing"
    # Still +200% against the original 0.6%, not against its own incident.
    engine.evaluate(_ratio_snapshot("reject_rate", bad=18, total=1000, at=last), last)
    assert alerts == [] or alerts[0].metric_context["baseline"] == pytest.approx(0.006)


def test_the_window_being_judged_is_not_in_its_own_baseline() -> None:
    engine = _engine(_rule("reject_rate"))
    last = _warm_up(
        engine, lambda at: _ratio_snapshot("reject_rate", bad=6, total=1000, at=at), 4
    )
    at = last + _WINDOW
    [alert] = _fire(
        engine, _ratio_snapshot("reject_rate", bad=18, total=1000, at=at), at
    )
    assert alert.metric_context["baseline"] == pytest.approx(0.006)


def test_latency_p95_against_baseline_p95() -> None:
    engine = _engine(_rule("ack_latency_ms", min_samples=50))

    def quiet(at: datetime) -> MetricsSnapshot:
        return make_snapshot(now=at, latency={"ack_latency_ms": make_latency(100, 500)})

    last = _warm_up(engine, quiet, 6)
    at = last + _WINDOW
    slow = make_snapshot(now=at, latency={"ack_latency_ms": make_latency(400, 500)})

    [alert] = _fire(engine, slow, at)

    assert alert.matched_condition == (
        "Abnormal processing latency detected on magic-prod-01. "
        "Processing latency is 400ms compared with its 100ms baseline "
        "(+300%) over the last 5 minutes"
    )


def test_latency_window_with_too_few_observations_is_not_judged() -> None:
    engine = _engine(_rule("ack_latency_ms", min_samples=50))
    last = _warm_up(
        engine,
        lambda at: make_snapshot(
            now=at, latency={"ack_latency_ms": make_latency(100, 500)}
        ),
        6,
    )
    at = last + _WINDOW
    thin = make_snapshot(now=at, latency={"ack_latency_ms": make_latency(900, 10)})
    assert _fire(engine, thin, at) == []


def test_the_alert_resolves_once_the_metric_returns_to_baseline() -> None:
    rule = _rule("reject_rate")
    engine = _engine(rule)
    last = _warm_up(
        engine, lambda at: _ratio_snapshot("reject_rate", bad=6, total=1000, at=at), 6
    )
    last += _WINDOW
    _fire(engine, _ratio_snapshot("reject_rate", bad=18, total=1000, at=last), last)

    resolved: list[AlertEvent] = []
    for _ in range(3):
        last += _WINDOW
        resolved += engine.evaluate(
            _ratio_snapshot("reject_rate", bad=6, total=1000, at=last), last
        )
    assert [a.status for a in resolved] == ["resolved"]


# --- anomaly.yaml ----------------------------------------------------------


def _write(tmp_path, text: str):
    path = tmp_path / "anomaly.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_anomaly_yaml_builds_rules_with_defaults(tmp_path) -> None:
    [rule] = load_anomaly_rules(_write(tmp_path, "reject_rate:\n  enabled: true\n"))

    assert rule.name == "AbnormalRejectRate"
    assert rule.kind is RuleKind.ANOMALY
    assert rule.window == "5m"
    assert rule.baseline_seconds == 3600
    assert rule.baseline_min_samples == 100
    assert rule.tiers == (SeverityTier("warning", Decimal("0.5")),)


def test_anomaly_yaml_honours_the_stub_keys(tmp_path) -> None:
    text = (
        "reject_rate:\n"
        "  enabled: true\n"
        "  baseline_window_minutes: 30\n"
        "  minimum_samples: 250\n"
        "  tiers: [{severity: critical, threshold: 1.0}]\n"
    )
    [rule] = load_anomaly_rules(_write(tmp_path, text))
    assert rule.baseline_seconds == 1800
    assert rule.baseline_min_samples == 250
    assert rule.tiers == (SeverityTier("critical", Decimal("1.0")),)


def test_disabled_missing_and_empty_yield_no_rules(tmp_path) -> None:
    assert (
        load_anomaly_rules(_write(tmp_path, "reject_rate:\n  enabled: false\n")) == ()
    )
    assert load_anomaly_rules(_write(tmp_path, "")) == ()
    assert load_anomaly_rules(tmp_path / "absent.yaml") == ()


@pytest.mark.parametrize(
    "text",
    [
        "no_such_metric:\n  enabled: true\n",
        "reject_rate:\n  baseline_window_minutes: 10\n",  # < 3x the 5m window
        "reject_rate:\n  unknown_key: 1\n",
    ],
)
def test_bad_anomaly_yaml_is_rejected(tmp_path, text: str) -> None:
    from telemetry_agent.rules.config_loader import RuleConfigError

    with pytest.raises(RuleConfigError):
        load_anomaly_rules(_write(tmp_path, text))


def test_anomaly_kind_is_rejected_in_rules_yaml(tmp_path) -> None:
    from telemetry_agent.rules.config_loader import (
        RuleConfigError,
        load_rules_from_yaml,
    )

    path = tmp_path / "rules.yaml"
    path.write_text(
        "rules:\n  - {name: X, kind: anomaly, source: indicator, metric: reject_rate,"
        " operator: '>', tiers: [{severity: warning, threshold: 1}]}\n",
        encoding="utf-8",
    )
    with pytest.raises(RuleConfigError, match="anomaly.yaml"):
        load_rules_from_yaml(path)


def test_shipped_config_defines_all_four_anomaly_rules() -> None:
    from pathlib import Path

    names = {r.name for r in load_anomaly_rules(Path("config/anomaly.yaml"))}
    assert names == {
        "AbnormalRejectRate",
        "AbnormalProcessingLatency",
        "AbnormalExecutionIssueRate",
        "AbnormalParserFailureRate",
    }
