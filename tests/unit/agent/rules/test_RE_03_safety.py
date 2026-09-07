"""RE-02: suppression and safety (spec 005 §4) — maxActiveAlerts/AlertStorm,
silences, dependent-alert suppression, schedule gating.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from rule_fixtures import make_snapshot
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import (
    RuleConfig,
    RuleKind,
    SeverityTier,
    Silence,
    ValueSource,
)

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)


def _counter_rule(
    name: str, metric: str, threshold: int = 5, **overrides: object
) -> RuleConfig:
    kwargs: dict[str, object] = dict(
        name=name,
        kind=RuleKind.THRESHOLD,
        source=ValueSource.COUNTER,
        metric=metric,
        operator=">",
        tiers=(SeverityTier("warning", Decimal(threshold)),),
        window="5m",  # matches fixtures.make_snapshot's default window
        for_seconds=0,
        resolve_after_seconds=0,
    )
    kwargs.update(overrides)
    return RuleConfig(**kwargs)  # type: ignore[arg-type]


def test_max_active_alerts_emits_one_alertstorm_and_suppresses_further() -> None:
    rules = tuple(_counter_rule(f"Rule{i}", f"metric_{i}") for i in range(3))
    engine = RuleEngine(
        rules=rules,
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
        max_active_alerts=2,
    )
    counters = {f"metric_{i}": Decimal(10) for i in range(3)}
    snapshot = make_snapshot(now=_T0, counters=counters)

    engine.evaluate(snapshot, _T0)  # tick1: all 3 conditions true -> pending

    events = engine.evaluate(snapshot, _T0 + timedelta(seconds=1))  # tick2: promote
    fired = [e for e in events if e.rule_name != "AlertStorm"]
    storms = [e for e in events if e.rule_name == "AlertStorm"]
    assert len(fired) == 2
    assert len(storms) == 1

    # The next tick: still over cap, no second AlertStorm notification.
    events3 = engine.evaluate(snapshot, _T0 + timedelta(seconds=2))
    assert all(e.rule_name != "AlertStorm" for e in events3)


def test_storm_clears_once_under_cap_and_the_suppressed_rule_fires() -> None:
    rules = tuple(_counter_rule(f"Rule{i}", f"metric_{i}") for i in range(2))
    engine = RuleEngine(
        rules=rules,
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
        max_active_alerts=1,
    )
    both_breached = make_snapshot(
        now=_T0, counters={"metric_0": Decimal(10), "metric_1": Decimal(10)}
    )
    engine.evaluate(both_breached, _T0)  # tick1: both -> pending
    engine.evaluate(
        both_breached, _T0 + timedelta(seconds=1)
    )  # tick2: Rule0 fires, Rule1 storm-blocked

    one_resolved = make_snapshot(
        now=_T0 + timedelta(seconds=2),
        counters={"metric_0": Decimal(0), "metric_1": Decimal(10)},
    )
    engine.evaluate(
        one_resolved, _T0 + timedelta(seconds=2)
    )  # tick3: Rule0 -> resolving

    # tick4: Rule0 resolves (frees the cap) and Rule1 fires within the same tick.
    events = engine.evaluate(one_resolved, _T0 + timedelta(seconds=3))
    assert any(e.rule_name == "Rule1" and e.status == "firing" for e in events)


def test_silence_suppresses_notification_but_still_tracks_state() -> None:
    rule = _counter_rule("Rule0", "metric_0")
    engine = RuleEngine(
        rules=(rule,),
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
    )
    engine.add_silence(
        Silence(
            rule_name="Rule0",
            instance_id="magic-prod-01",
            starts_at=_T0 - timedelta(minutes=1),
            ends_at=_T0 + timedelta(minutes=10),
        )
    )
    snapshot = make_snapshot(now=_T0, counters={"metric_0": Decimal(10)})
    engine.evaluate(snapshot, _T0)  # tick1: pending
    events = engine.evaluate(
        snapshot, _T0 + timedelta(seconds=1)
    )  # tick2: fires internally
    assert events == []
    assert (
        engine.active_alert_count() == 1
    )  # state recorded as firing, just not notified


def test_dependent_suppression_when_no_log_activity_is_firing() -> None:
    # `log_activity_firing` is read once at the start of each evaluate()
    # call, from the *previous* tick's state — order-independent, but it
    # means suppression itself lags NoLogActivity's own transition to
    # firing by exactly one tick. Three ticks exercise that precisely:
    # tick1 NoLogActivity enters pending; tick2 it fires (RejectSpike not
    # yet suppressed, so it independently enters pending); tick3
    # suppression is active, so RejectSpike's own pending progress is
    # reset rather than firing.
    no_log_activity = RuleConfig(
        name="NoLogActivity",
        kind=RuleKind.ABSENCE,
        source=ValueSource.COUNTER,
        metric="messages_total",
        operator="==",
        tiers=(SeverityTier("critical", Decimal(0)),),
        window="5m",  # matches fixtures.make_snapshot's default window
        for_seconds=0,
        resolve_after_seconds=0,
        depends_on_log_activity=False,
    )
    reject_spike = _counter_rule(
        "RejectSpike",
        "orders_rejected",
        threshold=50,
        depends_on_log_activity=True,
        for_seconds=60,  # stays pending through tick2, so it hasn't fired yet either
    )
    engine = RuleEngine(
        rules=(no_log_activity, reject_spike),
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
    )

    stale_but_orders_rejected = make_snapshot(
        now=_T0, counters={"orders_rejected": Decimal(100)}
    )
    t1 = _T0
    t2 = _T0 + timedelta(seconds=1)
    t3 = _T0 + timedelta(seconds=2)

    engine.evaluate(stale_but_orders_rejected, t1)  # NoLogActivity -> pending
    tick2 = engine.evaluate(stale_but_orders_rejected, t2)  # NoLogActivity fires
    assert any(e.rule_name == "NoLogActivity" and e.status == "firing" for e in tick2)
    # RejectSpike is only pending here (not yet "active" output) — its own
    # condition became true this same tick, so it hasn't cleared `for` yet.
    assert engine.active_alert_count() == 1

    tick3 = engine.evaluate(stale_but_orders_rejected, t3)
    assert all(e.rule_name != "RejectSpike" for e in tick3)
    # RejectSpike's own pending progress was reset by the suppression, not
    # promoted to firing, even though its raw condition is still true.
    assert engine.active_alert_count() == 1  # NoLogActivity only


def test_schedule_inactive_skips_rule_entirely() -> None:
    class NeverActive:
        def is_active(self, schedule_ref: str, instance_id: str, now: datetime) -> bool:
            return False

    rule = _counter_rule("Rule0", "metric_0", schedule_ref="trading-hours")
    engine = RuleEngine(
        rules=(rule,),
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
        schedule_checker=NeverActive(),
    )
    snapshot = make_snapshot(now=_T0, counters={"metric_0": Decimal(10)})
    events = engine.evaluate(snapshot, _T0)
    assert events == []
    assert engine.active_alert_count() == 0
