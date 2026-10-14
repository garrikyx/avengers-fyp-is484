"""UBS-75 integration: BackendPublisher -> consecutive_publish_failures
gauge -> snapshot() -> RuleEngine, plus the publisher's CounterRegistry ->
AgentCounterSampler -> MetricsAggregator path for `publish_failures`.

`BackendUnreachable` shipped with UBS-7 reading a `publish_failures`
counter that nothing produced. The Backend Publisher (UBS-103/104) produces
it now — but the rule reads the *gauge*, not that counter, and the reason
why is worth pinning down in a test rather than only in prose: see
`test_a_full_minute_of_outage_yields_exactly_five_failures` below.

Drives `publish_once(now=...)` directly rather than `run()`, per that
method's own docstring ("public and side-effect-free to call repeatedly, so
tests can drive it deterministically instead of sleeping through real ticks
or real backoff delays").
"""

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_agent.metrics.agent_counters import (
    PUBLISH_AGENT_METRICS,
    AgentCounterSampler,
)
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import PublishResult
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import RuleConfig
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.snapshot import Snapshot

_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_INSTANCE = "magic-prod-01"
_AGENT = "magic-agent-sg-01"
_ENDPOINT = "https://backend.example/telemetry/batch"


class _ScriptedSink:
    """A backend that returns whatever `status` currently says. Flipping
    the attribute mid-test is how the outage "ends"."""

    def __init__(self, status: int) -> None:
        self.status = status

    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> PublishResult:
        return PublishResult(status_code=self.status, latency_ms=1.0)


def _rule(name: str) -> RuleConfig:
    return next(r for r in DEFAULT_RULES if r.name == name)


def _publisher(sink: _ScriptedSink, **overrides: object) -> BackendPublisher:
    config = parse_publish_config({"endpoint": _ENDPOINT, **overrides})
    return BackendPublisher(
        sink, config, agent_id=_AGENT, application="Magic"
    )


def _snapshot_payload() -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id=_AGENT,
        application="Magic",
        instance_id=_INSTANCE,
        bucket_start_utc=_T0,
        bucket_seconds=10,
    )


def _engine(rule: RuleConfig) -> RuleEngine:
    return RuleEngine(
        rules=(rule,),
        instance_id=_INSTANCE,
        application="Magic",
        agent_id=_AGENT,
        started_at=_T0 - timedelta(hours=1),
    )


def _aggregator() -> MetricsAggregator:
    # Pinned clock, as in test_RE_callback_integration.py: `_T0` is a fixed
    # past date, so on a real clock every ingest would fall outside the
    # retained window and be dropped.
    config = AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS))
    return MetricsAggregator(config=config, clock=lambda: _T0.timestamp())


def _fail_n_times(publisher: BackendPublisher, n: int) -> None:
    """Drive `n` failed attempts, stepping `now` past each backoff window
    so every call actually attempts rather than returning early.

    One `asyncio.run` per attempt is fine: the publisher keeps no
    loop-bound state (its buffer is a plain deque and its waits are
    driven by the injected `now`, not by sleeping).
    """
    now = _T0
    for _ in range(n):
        publisher.enqueue_snapshot(_snapshot_payload(), now=now)
        asyncio.run(publisher.publish_once(now=now))
        now += timedelta(seconds=120)  # past the 60s backoff cap


# --- the gauge the rule actually reads ------------------------------------


def test_five_consecutive_failures_fire_backend_unreachable() -> None:
    publisher = _publisher(_ScriptedSink(503))
    _fail_n_times(publisher, 5)
    assert publisher.consecutive_failures == 5

    rule = _rule("BackendUnreachable")
    engine = _engine(rule)
    snap = snapshot(
        _aggregator(),
        "1m",
        now=_T0,
        consecutive_publish_failures=publisher.consecutive_failures,
    )
    engine.evaluate(snap, _T0)  # -> pending
    fired = engine.evaluate(snap, _T0 + timedelta(seconds=rule.for_seconds + 1))

    assert [a.rule_name for a in fired] == ["BackendUnreachable"]
    assert fired[0].severity == "warning"
    assert fired[0].observed_value == 5


def test_four_failures_do_not_fire() -> None:
    publisher = _publisher(_ScriptedSink(503))
    _fail_n_times(publisher, 4)

    rule = _rule("BackendUnreachable")
    engine = _engine(rule)
    snap = snapshot(
        _aggregator(),
        "1m",
        now=_T0,
        consecutive_publish_failures=publisher.consecutive_failures,
    )
    engine.evaluate(snap, _T0)
    assert engine.evaluate(snap, _T0 + timedelta(seconds=rule.for_seconds + 1)) == []


def test_a_successful_publish_resolves_the_alert() -> None:
    """The whole reason this is a gauge: recovery is observable. A windowed
    failure count would keep the alert up until the window aged out.
    """
    sink = _ScriptedSink(503)
    publisher = _publisher(sink)
    _fail_n_times(publisher, 5)

    rule = _rule("BackendUnreachable")
    engine = _engine(rule)

    def evaluate(at: datetime) -> list[AlertEvent]:
        snap = snapshot(
            _aggregator(),
            "1m",
            now=at,
            consecutive_publish_failures=publisher.consecutive_failures,
        )
        return engine.evaluate(snap, at)

    evaluate(_T0)
    firing = evaluate(_T0 + timedelta(seconds=rule.for_seconds + 1))
    assert firing[0].status == "firing"

    # Backend comes back.
    sink.status = 202
    recovered_at = _T0 + timedelta(seconds=600)
    publisher.enqueue_snapshot(_snapshot_payload(), now=recovered_at)
    asyncio.run(publisher.publish_once(now=recovered_at))
    assert publisher.consecutive_failures == 0

    # firing -> resolving on the first clear evaluation, then -> resolved
    # once `resolveAfter` has elapsed (FR-RUL-004).
    assert evaluate(recovered_at) == []
    resolved = evaluate(
        recovered_at + timedelta(seconds=rule.resolve_after_seconds + 1)
    )
    assert [a.status for a in resolved] == ["resolved"]


def test_no_publisher_wired_reads_as_none_not_zero() -> None:
    """FR-MET-031. An agent with no publisher must not look like an agent
    that is publishing cleanly."""
    snap = snapshot(_aggregator(), "1m", now=_T0)
    assert snap.gauges.consecutive_publish_failures is None

    rule = _rule("BackendUnreachable")
    engine = _engine(rule)
    engine.evaluate(snap, _T0)
    assert engine.evaluate(snap, _T0 + timedelta(seconds=rule.for_seconds + 1)) == []


# --- why it is not a windowed counter -------------------------------------


def test_a_full_minute_of_outage_yields_exactly_five_failures() -> None:
    """Regression guard on spec 005 §1.2's withdrawn approximation.

    `BackendUnreachable` used to read `publish_failures > 5` within `1m`.
    Under default config (interval 10s, base 1s, factor 2) the publisher's
    own backoff spaces attempts at t=0,10,20,30,40 and pushes the sixth
    past the minute boundary — so the counter tops out at exactly 5 and
    `> 5` could never fire. Anyone re-tuning this back to a windowed
    counter rule should land here first.
    """
    publisher = _publisher(_ScriptedSink(503))
    config = publisher._config

    now = _T0
    end = _T0 + timedelta(seconds=60)
    while now < end:
        publisher.enqueue_snapshot(_snapshot_payload(), now=now)
        asyncio.run(publisher.publish_once(now=now))
        now += timedelta(seconds=config.interval_seconds)

    assert publisher.counters.snapshot()["publish_failures"] == 5
    # The gauge, by contrast, is unaffected by attempt spacing.
    assert publisher.consecutive_failures == 5


# --- the counter path (spec 004 §4.3 trend view) --------------------------


def test_publish_failures_counter_reaches_the_aggregator() -> None:
    publisher = _publisher(_ScriptedSink(503))
    _fail_n_times(publisher, 3)

    aggregator = _aggregator()
    sampler = AgentCounterSampler(
        aggregator, instance_id=_INSTANCE, metrics=PUBLISH_AGENT_METRICS
    )
    sampler.sample(publisher.counters.snapshot(), at=_T0)

    row = aggregator.snapshot("5m", group_by=()).get(())
    assert row is not None
    assert row.counters["publish_failures"] == Decimal(3)


def test_publish_failures_do_not_make_a_log_starved_agent_look_alive() -> None:
    """Same property UBS-74 pinned for callbacks: a publisher retrying is
    not evidence that Magic is still writing logs, so this write path must
    not touch `_last_event_at` (which `NoLogActivity`'s sibling gauge
    reads).
    """
    publisher = _publisher(_ScriptedSink(503))
    _fail_n_times(publisher, 3)

    aggregator = _aggregator()
    assert aggregator.seconds_since_last_event() is None
    AgentCounterSampler(
        aggregator, instance_id=_INSTANCE, metrics=PUBLISH_AGENT_METRICS
    ).sample(publisher.counters.snapshot(), at=_T0)
    assert aggregator.seconds_since_last_event() is None
