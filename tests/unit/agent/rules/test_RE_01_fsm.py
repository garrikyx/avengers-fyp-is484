"""RE-01/02: the generic alert lifecycle FSM (spec 005 §2), isolated from
any specific evaluator using one simple synthetic threshold rule.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from rule_fixtures import make_snapshot
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import (
    AlertStatus,
    RuleConfig,
    RuleKind,
    SeverityTier,
    ValueSource,
)
from telemetry_shared.models.metrics import MetricsSnapshot

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)

_RULE = RuleConfig(
    name="TestRule",
    kind=RuleKind.THRESHOLD,
    source=ValueSource.COUNTER,
    metric="widgets_broken",
    operator=">",
    tiers=(SeverityTier(severity="warning", threshold=Decimal(5)),),
    window="1m",
    for_seconds=60,
    resolve_after_seconds=120,
)


def _engine(**overrides: object) -> RuleEngine:
    kwargs: dict[str, object] = dict(
        rules=(_RULE,),
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),  # well past startup grace by default
        startup_grace_seconds=60,
        renotify_interval_seconds=1800,
    )
    kwargs.update(overrides)
    return RuleEngine(**kwargs)  # type: ignore[arg-type]


def _snapshot(now: datetime, broken: int) -> MetricsSnapshot:
    return make_snapshot(
        now=now, window="1m", counters={"widgets_broken": Decimal(broken)}
    )


def test_condition_true_enters_pending_with_no_event() -> None:
    engine = _engine()
    events = engine.evaluate(_snapshot(_T0, 10), _T0)
    assert events == []
    # `pending` isn't yet "active alert output" (FR-RUL-017) — it hasn't
    # cleared `for` or been notified — but it must be tracked internally.
    assert engine.active_alert_count() == 0
    assert engine.status_of("TestRule") is AlertStatus.PENDING


def test_pending_reverts_to_inactive_if_condition_clears_before_for_elapsed() -> None:
    engine = _engine()
    engine.evaluate(_snapshot(_T0, 10), _T0)
    engine.evaluate(
        _snapshot(_T0 + timedelta(seconds=30), 0), _T0 + timedelta(seconds=30)
    )
    assert engine.active_alert_count() == 0
    assert engine.status_of("TestRule") is None


def test_pending_fires_after_for_elapsed() -> None:
    engine = _engine()
    engine.evaluate(_snapshot(_T0, 10), _T0)
    t1 = _T0 + timedelta(seconds=61)
    events = engine.evaluate(_snapshot(t1, 10), t1)
    assert len(events) == 1
    alert = events[0]
    assert alert.status == "firing"
    assert alert.rule_name == "TestRule"
    assert alert.notification_count == 1
    assert alert.first_observed_utc == _T0


def test_firing_to_resolving_to_resolved() -> None:
    engine = _engine()
    engine.evaluate(_snapshot(_T0, 10), _T0)
    t1 = _T0 + timedelta(seconds=61)
    fired = engine.evaluate(_snapshot(t1, 10), t1)[0]

    t2 = t1 + timedelta(seconds=10)
    resolving = engine.evaluate(_snapshot(t2, 0), t2)
    assert resolving == []  # firing -> resolving emits nothing
    assert engine.active_alert_count() == 1

    t3 = t2 + timedelta(seconds=121)
    resolved = engine.evaluate(_snapshot(t3, 0), t3)
    assert len(resolved) == 1
    assert resolved[0].status == "resolved"
    assert resolved[0].alert_id == fired.alert_id
    assert resolved[0].resolved_at_utc == t3
    assert engine.active_alert_count() == 0


def test_condition_true_again_while_resolving_returns_to_firing_no_notification() -> (
    None
):
    engine = _engine()
    engine.evaluate(_snapshot(_T0, 10), _T0)
    t1 = _T0 + timedelta(seconds=61)
    engine.evaluate(_snapshot(t1, 10), t1)

    t2 = t1 + timedelta(seconds=10)
    engine.evaluate(_snapshot(t2, 0), t2)  # -> resolving

    t3 = t2 + timedelta(seconds=10)
    rebound = engine.evaluate(_snapshot(t3, 10), t3)  # condition true again
    assert rebound == []
    assert engine.active_alert_count() == 1  # back to firing, same occurrence


def test_alert_id_rotates_after_a_fresh_occurrence() -> None:
    engine = _engine()
    engine.evaluate(_snapshot(_T0, 10), _T0)
    t1 = _T0 + timedelta(seconds=61)
    first = engine.evaluate(_snapshot(t1, 10), t1)[0]

    t2 = t1 + timedelta(seconds=10)
    engine.evaluate(_snapshot(t2, 0), t2)
    t3 = t2 + timedelta(seconds=121)
    engine.evaluate(_snapshot(t3, 0), t3)  # resolved, key freed

    # A brand new occurrence of the same rule.
    engine.evaluate(_snapshot(t3, 10), t3)
    t4 = t3 + timedelta(seconds=61)
    second = engine.evaluate(_snapshot(t4, 10), t4)[0]

    assert second.alert_id != first.alert_id


def test_renotify_interval_repeats_notification_while_firing() -> None:
    engine = _engine(renotify_interval_seconds=100)
    engine.evaluate(_snapshot(_T0, 10), _T0)
    t1 = _T0 + timedelta(seconds=61)
    engine.evaluate(_snapshot(t1, 10), t1)

    t2 = t1 + timedelta(seconds=50)  # before renotify interval
    assert engine.evaluate(_snapshot(t2, 10), t2) == []

    t3 = t1 + timedelta(seconds=101)  # past renotify interval
    renotified = engine.evaluate(_snapshot(t3, 10), t3)
    assert len(renotified) == 1
    assert renotified[0].notification_count == 2


def test_renotify_disabled_when_interval_is_zero() -> None:
    engine = _engine(renotify_interval_seconds=0)
    engine.evaluate(_snapshot(_T0, 10), _T0)
    t1 = _T0 + timedelta(seconds=61)
    engine.evaluate(_snapshot(t1, 10), t1)

    t2 = t1 + timedelta(days=1)
    assert engine.evaluate(_snapshot(t2, 10), t2) == []


def test_startup_grace_suppresses_all_evaluation() -> None:
    engine = _engine(started_at=_T0, startup_grace_seconds=60)
    events = engine.evaluate(_snapshot(_T0, 10), _T0 + timedelta(seconds=30))
    assert events == []
    assert engine.status_of("TestRule") is None  # not even tracked as pending yet
