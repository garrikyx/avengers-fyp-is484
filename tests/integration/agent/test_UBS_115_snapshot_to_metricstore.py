"""UBS-115 integration: raw FIX events -> MetricsAggregator ->
`RuleEvaluator._publish_metrics_snapshot` -> `snapshot_bridge.build_snapshot`
-> `BackendPublisher.enqueue_snapshot` -> POST /telemetry/batch ->
`IngestionService` -> `StreamProcessor` -> `MetricStore.read()`.

Before this ticket, `BackendPublisher.enqueue_snapshot()` was called nowhere
in production code -- the Metrics Aggregator's data never reached the
backend. This follows real counters all the way from the aggregator to a
`MetricStore.read()` response, through the *actual* `RuleEvaluator` tick
(not a hand-built `Snapshot`), confirming both halves of the ticket's
"Done when": real data lands in the store, and a publish retry does not
duplicate it.

Uses `httpx.ASGITransport` over `create_app()`, the pattern established in
`test_UBS_103_publisher_backend.py` / `test_UBS_109_rule_engine_to_backend.py`.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
from fastapi import FastAPI
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.pipeline.evaluator import RuleEvaluator
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import HttpsPublishSink
from telemetry_agent.publishing.snapshot_bridge import SnapshotEmitter
from telemetry_agent.rules.engine import RuleEngine
from telemetry_backend.main import create_app
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.parsed_message import NewOrderEvent
from telemetry_shared.models.snapshot import SeriesEntry, Snapshot

# `IngestionService.run()` age-checks a bucket against the *real* wall
# clock (`datetime.now(UTC)`, not an injectable one), so `_T0` must be close
# to actual now -- a fixed historical date would be silently dropped as
# `BUCKET_TOO_OLD` (`StreamProcessorConfig.max_bucket_age_seconds`, default
# 1h) even though the publish itself still reports 202/COMMIT. Floored to a
# 10s boundary so the completed bucket [_T0 - 10s, _T0) is exact.
_now = datetime.now(UTC)
_T0 = _now.replace(microsecond=0) - timedelta(seconds=int(_now.timestamp()) % 10)
_BUCKET_START = _T0 - timedelta(seconds=10)
_AGENT_ID = "magic-agent-sg-01"
_APPLICATION = "Magic"
_INSTANCE = "magic-prod-01"
_ENDPOINT = "https://backend.example/telemetry/batch"


def _aggregator() -> MetricsAggregator:
    config = AggregatorConfig(
        bucket_seconds=1,
        metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS},
    )
    return MetricsAggregator(config=config, clock=lambda: _T0.timestamp())


def _ingest_three_orders(aggregator: MetricsAggregator) -> None:
    """Three NewOrderSingle events landing inside the completed bucket
    [_BUCKET_START, _T0) that the evaluator will publish."""
    for i in range(3):
        event = NewOrderEvent(
            event_time_utc=_BUCKET_START + timedelta(seconds=i),
            instance_id=_INSTANCE,
            session_id="MAGIC->EXCH1",
            cl_ord_id_hash=f"order-{i}",
            symbol="AAPL",
            side="buy",
            ord_type="limit",
            order_qty=Decimal(100),
        )
        aggregator.ingest_counters(event, derive_counters(event))


def _evaluator(
    aggregator: MetricsAggregator, publisher: BackendPublisher
) -> RuleEvaluator:
    engine = RuleEngine(
        rules=(),
        instance_id=_INSTANCE,
        application=_APPLICATION,
        agent_id=_AGENT_ID,
        started_at=_T0,
    )
    router = AlertRouter(publisher, agent_id=_AGENT_ID, application=_APPLICATION)
    correlator = LatencyCorrelator(aggregator)
    return RuleEvaluator(
        engine,
        aggregator,
        router,
        instance_id=_INSTANCE,
        correlator=correlator,
        publisher=publisher,
        snapshot_emitter=SnapshotEmitter(
            aggregator,
            publisher,
            bucket_seconds=10,
            agent_id=_AGENT_ID,
            application=_APPLICATION,
            instance_id=_INSTANCE,
            correlator=correlator,
        ),
    )


def _publisher(app: FastAPI) -> BackendPublisher:
    sink = HttpsPublishSink(
        _ENDPOINT, "test-token", transport=httpx.ASGITransport(app=app)
    )
    config = parse_publish_config({"endpoint": _ENDPOINT, "metricsBucketSeconds": 10})
    return BackendPublisher(sink, config, agent_id=_AGENT_ID, application=_APPLICATION)


async def _drain_backend(app: FastAPI) -> None:
    """See test_UBS_109_rule_engine_to_backend.py:_drain_backend -- same
    reason `_queue.join()` is required over polling `queue_depth`."""
    service = app.state.ingestion
    worker = asyncio.create_task(service.run())
    try:
        await service._queue.join()  # noqa: SLF001
    finally:
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass


async def _publish_and_drain(
    app: FastAPI, publisher: BackendPublisher
) -> PublishAction | None:
    action = await publisher.publish_once(now=_T0)
    await _drain_backend(app)
    return action


def _read_counters(app: FastAPI) -> dict[str, Decimal]:
    rows = app.state.processor.store.read(_INSTANCE, from_utc=_BUCKET_START, to_utc=_T0)
    return {metric: value for row in rows for metric, value in row.counters.items()}


def test_real_aggregator_counters_reach_the_metric_store() -> None:
    aggregator = _aggregator()
    _ingest_three_orders(aggregator)

    app = create_app()
    publisher = _publisher(app)
    evaluator = _evaluator(aggregator, publisher)

    changed = evaluator.evaluate_once(now=_T0)
    assert changed == []  # no rules configured; this tick only publishes
    assert publisher.queue_depth() == 1  # the Snapshot the tick just built

    action = asyncio.run(_publish_and_drain(app, publisher))
    assert action is PublishAction.COMMIT
    assert publisher.queue_depth() == 0

    totals = _read_counters(app)
    assert totals["orders_submitted"] == Decimal(3)
    assert totals["messages_total"] == Decimal(3)


def test_second_tick_before_the_bucket_closes_does_not_republish() -> None:
    """The SnapshotEmitter half of "no duplicate bucket after a publish
    retry": two evaluator ticks inside the same not-yet-elapsed bucket must
    not enqueue a second Snapshot for the bucket already published."""
    aggregator = _aggregator()
    _ingest_three_orders(aggregator)

    app = create_app()
    publisher = _publisher(app)
    evaluator = _evaluator(aggregator, publisher)

    evaluator.evaluate_once(now=_T0)
    assert publisher.queue_depth() == 1
    asyncio.run(_publish_and_drain(app, publisher))
    assert publisher.queue_depth() == 0

    # A second tick one second later: still inside the bucket that just
    # closed (the *next* bucket, [_T0, _T0+10), hasn't completed yet).
    evaluator.evaluate_once(now=_T0 + timedelta(seconds=1))
    assert publisher.queue_depth() == 0  # nothing new enqueued


def test_late_tick_publishes_every_missed_bucket_to_the_store() -> None:
    """UBS-123: a tick that arrives two buckets late (a stalled loop, a
    long GC) must still land both buckets' counters in the store, each in
    its own bucket -- not just the most recent one."""
    aggregator = _aggregator()
    early = _BUCKET_START - timedelta(seconds=10)  # [_T0-20s, _T0-10s)

    app = create_app()
    publisher = _publisher(app)
    evaluator = _evaluator(aggregator, publisher)
    evaluator.evaluate_once(now=early)  # first ever tick: emits [_T0-30s, early)
    assert publisher.queue_depth() == 1

    event = NewOrderEvent(
        event_time_utc=early + timedelta(seconds=2),
        instance_id=_INSTANCE,
        session_id="MAGIC->EXCH1",
        cl_ord_id_hash="order-early",
        symbol="AAPL",
        side="buy",
        ord_type="limit",
        order_qty=Decimal(100),
    )
    aggregator.ingest_counters(event, derive_counters(event))
    _ingest_three_orders(aggregator)

    evaluator.evaluate_once(now=_T0)  # skipped the tick at _BUCKET_START
    assert publisher.queue_depth() == 3  # both missed buckets, not just one

    # One publish for all three: the in-process backend's queue is bound to
    # the first event loop that drains it.
    assert asyncio.run(_publish_and_drain(app, publisher)) is PublishAction.COMMIT
    store = app.state.processor.store

    def orders(from_utc: datetime, to_utc: datetime) -> Decimal:
        # `read` is end-inclusive, so stop at the bucket's last second.
        last = to_utc - timedelta(seconds=1)
        rows = store.read(_INSTANCE, from_utc=from_utc, to_utc=last)
        return sum(
            (row.counters.get("orders_submitted", Decimal(0)) for row in rows),
            Decimal(0),
        )

    assert orders(early, _BUCKET_START) == Decimal(1)
    assert orders(_BUCKET_START, _T0) == Decimal(3)


def test_merging_the_same_snapshot_twice_does_not_double_the_counters() -> None:
    """The other half: even if an identical Snapshot *were* merged twice
    (a publish retry resending the same buffered item), MetricStore.merge's
    replace-by-(agentId, nativeBucketEpoch) semantics keep the result
    correct -- pinned directly against the real StreamProcessor, no HTTP."""
    processor = StreamProcessor()
    snap = Snapshot(
        schema_version=1,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
        instance_id=_INSTANCE,
        bucket_start_utc=_BUCKET_START,
        bucket_seconds=10,
        series=[
            SeriesEntry(
                dimensions={"symbol": "AAPL"},
                counters={"orders_submitted": Decimal(3)},
            )
        ],
        gauges={},
    )

    processor.process_snapshot(snap, now=_T0)
    processor.process_snapshot(snap, now=_T0)  # identical retry

    rows = processor.store.read(_INSTANCE, from_utc=_BUCKET_START, to_utc=_T0)
    totals = {metric: value for row in rows for metric, value in row.counters.items()}
    assert totals["orders_submitted"] == Decimal(3)  # not 6
