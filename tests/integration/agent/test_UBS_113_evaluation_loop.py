"""UBS-113 integration: raw FIX bytes -> FixParser -> MetricsAggregator /
LatencyCorrelator -> RuleEvaluator.run() -> AlertRouter -> {BackendPublisher
buffer, CallbackDispatcher}.

The UBS-109 test's FIX builders and reject-burst aggregator are reused, so the
alert asserted on is one the engine derived from real log lines, delivered by
the loop rather than by a hand-called `evaluate()`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime, timedelta

from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import CallbackResult
from telemetry_agent.callbacks.status import DeliveryStatus
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.metrics_event import build_parsed_message_event
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.pipeline.evaluator import RuleEvaluator
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import DryRunPublishSink
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import RuleConfig
from test_UBS_109_rule_engine_to_backend import (
    _AGENT_ID,
    _APPLICATION,
    _ENDPOINT,
    _INSTANCE,
    _KEY,
    _T0,
    _aggregator_with_a_reject_burst,
    _order,
)


class _NullCallbackSink:
    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> CallbackResult:
        return CallbackResult(status_code=200, latency_ms=1.0)


def _rule(name: str) -> RuleConfig:
    rule = next(r for r in DEFAULT_RULES if r.name == name)
    return replace(rule, for_seconds=0)


def _wire(
    rule: RuleConfig,
    aggregator: MetricsAggregator,
    *,
    correlator: LatencyCorrelator | None = None,
) -> tuple[RuleEvaluator, BackendPublisher, CallbackDispatcher]:
    publisher = BackendPublisher(
        DryRunPublishSink(),
        parse_publish_config({"endpoint": _ENDPOINT}),
        agent_id=_AGENT_ID,
        application=_APPLICATION,
    )
    dispatcher = CallbackDispatcher(
        _NullCallbackSink(),
        parse_callbacks_config({"endpoint": "https://magic.example/cb"}),
        b"secret",
    )
    router = AlertRouter(
        publisher,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
        dispatcher=dispatcher,
    )
    engine = RuleEngine(
        rules=(rule,),
        instance_id=_INSTANCE,
        application=_APPLICATION,
        agent_id=_AGENT_ID,
        started_at=_T0 - timedelta(hours=1),
    )
    evaluator = RuleEvaluator(
        engine,
        aggregator,
        router,
        instance_id=_INSTANCE,
        correlator=correlator,
        publisher=publisher,
        dispatcher=dispatcher,
        interval_seconds=0.01,
        clock=_stepping_clock(),
    )
    return evaluator, publisher, dispatcher


def _stepping_clock() -> Callable[[], datetime]:
    """Each tick is one second later, so pending -> firing happens on tick 2
    without the test sleeping through a real `for` delay."""
    ticks = 0

    def now() -> datetime:
        nonlocal ticks
        ticks += 1
        return _T0 + timedelta(seconds=ticks)

    return now


def _run_ticks(evaluator: RuleEvaluator, count: int) -> None:
    async def drive() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(evaluator.run(stop))
        while (
            evaluator.counters.snapshot().get("evaluations", 0) < count
            and not task.done()  # a dead loop fails, not hangs
        ):
            await asyncio.sleep(0.005)
        stop.set()
        await asyncio.wait_for(task, timeout=1.0)

    asyncio.run(drive())


def test_the_loop_delivers_a_real_reject_spike_to_both_paths() -> None:
    evaluator, publisher, dispatcher = _wire(
        _rule("RejectSpike"), _aggregator_with_a_reject_burst()
    )

    _run_ticks(evaluator, 3)

    assert publisher.queue_depth() == 1
    alert_ids = list(dispatcher.tracker.snapshot())
    assert len(alert_ids) == 1
    record = dispatcher.tracker.status_of(alert_ids[0])
    assert record is not None and record.status is DeliveryStatus.PENDING


def test_the_loop_feeds_the_correlator_gauge_to_pending_order_timeout() -> None:
    """An order with no ack, its age read off the correlator each tick."""
    correlator_now = [_T0.timestamp()]
    aggregator = MetricsAggregator(
        config=AggregatorConfig(
            metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS}
        ),
        clock=lambda: _T0.timestamp(),
    )
    correlator = LatencyCorrelator(aggregator, clock=lambda: correlator_now[0])
    meta = SourceMeta(
        instance_id=_INSTANCE, path="Fix.log", log_type="fix", read_at=_T0
    )
    event = build_parsed_message_event(
        FixParser(hash_key=_KEY).parse(_order(1, 1), meta), meta
    )
    assert event is not None
    correlator.ingest(event)
    correlator_now[0] += 31  # past PendingOrderTimeout's 30s

    evaluator, publisher, _ = _wire(
        _rule("PendingOrderTimeout"), aggregator, correlator=correlator
    )
    _run_ticks(evaluator, 3)

    assert publisher.queue_depth() == 1
