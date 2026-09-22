"""UBS-74 integration: CallbackDispatcher -> CounterRegistry ->
AgentCounterSampler -> MetricsAggregator -> snapshot() -> RuleEngine.

`CallbackFailing` shipped with UBS-7 reading a `callback_failures` counter
that nothing produced. The Callback Dispatcher does produce it — but into
its own since-startup `CounterRegistry`, which is a different shape from
the windowed store the rule reads. This proves the sampler closes that gap:
real delivery failures against a mock Magic endpoint end up firing the
rule, which is the agent noticing that its own alerts aren't getting out.

Uses `httpx.MockTransport` and the zero-backoff config convention from
`test_FR_CBK_004_006_007_dispatcher.py` — the transport and backoff maths
are that file's subject, not this one's.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import HttpsCallbackSink
from telemetry_agent.metrics.agent_counters import AgentCounterSampler
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import RuleConfig
from telemetry_shared.models.alerts import AlertEvent

_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_INSTANCE = "magic-prod-01"
_ENDPOINT = "https://magic.example/callbacks"
_CONFIG = parse_callbacks_config(
    {"endpoint": _ENDPOINT, "retry": {"base": "0s", "cap": "0s"}, "maxAttempts": 3}
)


def _rule(name: str) -> RuleConfig:
    return next(r for r in DEFAULT_RULES if r.name == name)


def _alert(alert_id: str) -> AlertEvent:
    return AlertEvent(
        alert_id=alert_id,
        rule_name="FixSessionDown",
        severity="critical",
        status="firing",
        application="Magic",
        instance_id=_INSTANCE,
        agent_id="agent-sg-01",
        matched_condition="logouts >= 1",
        observed_value=1.0,
        threshold=1.0,
        first_observed_utc=_T0,
        last_observed_utc=_T0,
        notification_count=1,
    )


async def _drain(dispatcher: CallbackDispatcher, alerts: list[AlertEvent]) -> None:
    for alert in alerts:
        dispatcher.enqueue(alert)
    task = asyncio.create_task(dispatcher.run())
    await asyncio.sleep(0.3)
    task.cancel()


def _dispatch(status: int, *, count: int) -> CallbackDispatcher:
    """Send `count` alerts to a Magic endpoint that always answers
    `status`, and return the dispatcher holding the resulting counters.
    """

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status)

    sink = HttpsCallbackSink(_ENDPOINT, transport=httpx.MockTransport(handler))
    dispatcher = CallbackDispatcher(sink, _CONFIG, b"test-secret")
    alerts = [_alert(f"alert-{i}") for i in range(count)]
    asyncio.run(_drain(dispatcher, alerts))
    return dispatcher


def _aggregator() -> MetricsAggregator:
    config = AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS))
    return MetricsAggregator(config=config, clock=lambda: _T0.timestamp())


def _fire(aggregator: MetricsAggregator) -> list[AlertEvent]:
    rule = _rule("CallbackFailing")
    engine = RuleEngine(
        rules=(rule,),
        instance_id=_INSTANCE,
        application="Magic",
        agent_id="agent-sg-01",
        started_at=_T0 - timedelta(hours=1),
    )
    snap = snapshot(aggregator, "5m", group_by=(), now=_T0)
    engine.evaluate(snap, _T0)  # -> pending
    return engine.evaluate(snap, _T0 + timedelta(seconds=rule.for_seconds + 1))


def test_four_permanent_failures_fire_callback_failing() -> None:
    dispatcher = _dispatch(400, count=4)
    assert dispatcher.counters.snapshot()["callback_failures"] == 4

    aggregator = _aggregator()
    sampler = AgentCounterSampler(aggregator, instance_id=_INSTANCE)
    sampler.sample(dispatcher.counters.snapshot(), at=_T0)

    row = aggregator.snapshot("5m", group_by=())[()]
    assert row.counters["callback_failures"] == Decimal(4)

    alerts = _fire(aggregator)
    assert [alert.rule_name for alert in alerts] == ["CallbackFailing"]
    assert alerts[0].severity == "warning"
    assert alerts[0].observed_value == 4.0


def test_three_failures_stay_under_the_threshold() -> None:
    dispatcher = _dispatch(400, count=3)
    aggregator = _aggregator()
    AgentCounterSampler(aggregator, instance_id=_INSTANCE).sample(
        dispatcher.counters.snapshot(), at=_T0
    )
    assert _fire(aggregator) == []


def test_successful_deliveries_never_reach_the_failure_counter() -> None:
    dispatcher = _dispatch(200, count=6)
    counters = dispatcher.counters.snapshot()
    assert counters["callback_delivered"] == 6
    assert "callback_failures" not in counters

    aggregator = _aggregator()
    AgentCounterSampler(aggregator, instance_id=_INSTANCE).sample(counters, at=_T0)
    row = aggregator.snapshot("5m", group_by=())[()]
    assert row.counters["callback_delivered"] == Decimal(6)
    assert "callback_failures" not in row.counters
    assert _fire(aggregator) == []


def test_repeated_sampling_does_not_inflate_the_counter_toward_a_false_alert() -> None:
    """The registry is monotonic, so re-ingesting its absolute value on
    every tick would turn 3 real failures into 9 after three samples and
    trip `CallbackFailing` on a session that never breached it.
    """
    dispatcher = _dispatch(400, count=3)
    aggregator = _aggregator()
    sampler = AgentCounterSampler(aggregator, instance_id=_INSTANCE)
    for _ in range(3):
        sampler.sample(dispatcher.counters.snapshot(), at=_T0)

    row = aggregator.snapshot("5m", group_by=())[()]
    assert row.counters["callback_failures"] == Decimal(3)
    assert _fire(aggregator) == []


def test_callback_failures_do_not_make_a_log_starved_agent_look_alive() -> None:
    """`secondsSinceLastEvent` must stay untouched by the agent's own
    counters — otherwise a Magic instance that stopped logging entirely
    would look healthy purely because its dispatcher was failing.
    """
    dispatcher = _dispatch(400, count=4)
    aggregator = _aggregator()
    AgentCounterSampler(aggregator, instance_id=_INSTANCE).sample(
        dispatcher.counters.snapshot(), at=_T0
    )
    assert aggregator.seconds_since_last_event() is None
    assert snapshot(aggregator, "5m", now=_T0).gauges.seconds_since_last_event is None
