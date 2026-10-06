"""Metrics Aggregator -> SnapshotEmitter -> BackendPublisher -> the *real*
backend (`POST /telemetry/batch` -> IngestionService -> StreamProcessor ->
MetricStore), over `httpx.ASGITransport`.

The end-to-end claim: what the backend's Metric Store holds for an instance
equals what the agent's own aggregator counted — no double counting across
publish ticks, a bucket re-published after a late event replaces its earlier
contribution rather than adding to it, and nothing is lost or duplicated
across a backend outage.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.metrics.emitter import SnapshotEmitter
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import HttpsPublishSink
from telemetry_backend.main import create_app
from telemetry_backend.services.ingestion import IngestionService
from telemetry_shared.models.parsed_message import (
    ExecutionReportEvent,
    NewOrderEvent,
    ParsedMessageEvent,
)

_AGENT_ID = "magic-agent-sg-01"
_APPLICATION = "Magic"
_INSTANCE = "magic-prod-01"
_ENDPOINT = "https://backend.example/telemetry/batch"


class _Clock:
    def __init__(self, start: float) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


class _OutageTransport(httpx.AsyncBaseTransport):
    """Answers 503 while `down`, otherwise forwards to the real app."""

    def __init__(self, app: object) -> None:
        self._inner = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
        self.down = False

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if self.down:
            return httpx.Response(503)
        return await self._inner.handle_async_request(request)


def _order(at: datetime, n: int, *, symbol: str = "AAPL") -> NewOrderEvent:
    return NewOrderEvent(
        event_time_utc=at,
        instance_id=_INSTANCE,
        session_id="MAGIC->EXCH1",
        cl_ord_id_hash=f"ORD-{n}",
        symbol=symbol,
        side="Buy",
        ord_type="Limit",
        order_qty=Decimal(100),
    )


def _exec_report(at: datetime, n: int, *, rejected: bool) -> ExecutionReportEvent:
    return ExecutionReportEvent(
        event_time_utc=at,
        instance_id=_INSTANCE,
        session_id="MAGIC->EXCH1",
        cl_ord_id_hash=f"ORD-{n}",
        order_id_hash=f"OID-{n}",
        exec_id_hash=f"EXEC-{n}",
        exec_type="Rejected" if rejected else "New",
        ord_status="Rejected" if rejected else "New",
        symbol="AAPL",
        side="Buy",
        ord_type="Limit",
        reject_reason_code="OrderExceedsLimit" if rejected else None,
    )


class _Harness:
    """One agent (aggregator + correlator + emitter + publisher) wired to
    one real backend app, with a controllable agent clock."""

    def __init__(self, bucket_seconds: int) -> None:
        # Recent enough for the backend's maxBucketAge; on the 10s grid.
        self.base_epoch = (time.time() // 10) * 10 - 60
        self.base = datetime.fromtimestamp(self.base_epoch, tz=UTC)
        self.bucket_seconds = bucket_seconds
        self.clock = _Clock(self.base_epoch)
        self.aggregator = MetricsAggregator(
            AggregatorConfig(
                bucket_seconds=bucket_seconds,
                metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS},
            ),
            clock=self.clock,
        )
        self.correlator = LatencyCorrelator(self.aggregator, clock=self.clock)
        self.service = IngestionService()
        self.transport = _OutageTransport(create_app(service=self.service))
        self.publisher = BackendPublisher(
            HttpsPublishSink(_ENDPOINT, "test-token", transport=self.transport),
            parse_publish_config({"endpoint": _ENDPOINT}),
            agent_id=_AGENT_ID,
            application=_APPLICATION,
        )
        self.emitter = SnapshotEmitter(
            self.aggregator,
            agent_id=_AGENT_ID,
            application=_APPLICATION,
            instance_ids=(_INSTANCE,),
            correlator=self.correlator,
            consecutive_publish_failures=lambda: self.publisher.consecutive_failures,
            publish_queue_depth=lambda: self.publisher.queue_depth(),
        )
        # Publish ticks step a minute apart so any backoff delay has always
        # elapsed; the agent clock moves independently.
        self._publish_now = datetime.now(UTC)

    def ingest(self, event: ParsedMessageEvent) -> None:
        self.aggregator.ingest_counters(event, derive_counters(event))
        self.correlator.ingest(event)

    def at(self, seconds: float) -> datetime:
        return self.base + timedelta(seconds=seconds)

    def close_buckets_through(self, seconds: float) -> None:
        self.clock.now = self.base_epoch + seconds

    async def tick(self) -> PublishAction | None:
        for snapshot in self.emitter.collect():
            self.publisher.enqueue_snapshot(snapshot)
        self._publish_now += timedelta(minutes=1)
        return await self.publisher.publish_once(now=self._publish_now)

    async def run(self, scenario: Callable[[], object]) -> None:
        consumer = asyncio.create_task(self.service.run())
        try:
            await scenario()  # type: ignore[misc]
            await self._wait_until_store_matches_aggregator()
        finally:
            consumer.cancel()

    def store_counters(self) -> dict[str, Decimal]:
        groups = self.service.stream_processor.store.read(
            _INSTANCE,
            from_utc=self.base - timedelta(minutes=1),
            to_utc=self.base + timedelta(minutes=5),
        )
        return groups[0].counters if groups else {}

    async def _wait_until_store_matches_aggregator(self) -> None:
        self.expected = self.aggregator.snapshot("15m")[()].counters
        # Ingestion merges on a background consumer; give it a moment.
        deadline = time.monotonic() + 5
        while self.store_counters() != self.expected and time.monotonic() < deadline:
            await asyncio.sleep(0.05)
        self.actual = self.store_counters()


@pytest.mark.parametrize("bucket_seconds", [10, 1])
def test_backend_store_matches_the_agent_aggregator(bucket_seconds: int) -> None:
    """`bucket_seconds=1` also covers FR-STM-001: ten 1s agent buckets per
    backend canonical 10s bucket, each a separate contribution that must
    accumulate, while a re-published one must still replace."""
    h = _Harness(bucket_seconds)

    async def scenario() -> None:
        # Bucket A: 3 orders, one acked 30ms later, one rejected.
        for n in range(3):
            h.ingest(_order(h.at(0), n))
        h.ingest(_exec_report(h.at(0.03), 0, rejected=False))
        h.ingest(_exec_report(h.at(0.05), 1, rejected=True))
        h.close_buckets_through(10)
        assert await h.tick() is PublishAction.COMMIT

        # Bucket B (and, at 1s width, a second bucket in the same canonical
        # 10s slot as A): 2 orders on another symbol.
        h.ingest(_order(h.at(5), 3, symbol="MSFT"))
        h.ingest(_order(h.at(10), 4, symbol="MSFT"))
        h.close_buckets_through(20)
        assert await h.tick() is PublishAction.COMMIT

        # Late event for bucket A: A is re-published in full, and the
        # backend must replace — not add to — its earlier contribution.
        h.ingest(_order(h.at(0.5), 5))
        assert await h.tick() is PublishAction.COMMIT

    asyncio.run(h.run(scenario))

    assert h.actual == h.expected
    assert h.actual["orders_submitted"] == Decimal(6)  # 3 + 2 + 1 late
    assert h.actual["orders_rejected"] == Decimal(1)
    assert h.actual["orders_acked"] == Decimal(1)


def test_snapshots_survive_a_backend_outage_without_loss_or_duplication() -> None:
    """FR-PUB-004/005 and the push model: while the backend is down the
    publisher backs off, the emitter keeps collecting, and every bucket is
    delivered exactly once in effect after recovery."""
    h = _Harness(bucket_seconds=10)

    async def scenario() -> None:
        h.transport.down = True
        for second in range(0, 40, 10):  # four buckets, one per tick
            h.ingest(_order(h.at(second), second))
            h.close_buckets_through(second + 10)
            assert await h.tick() is PublishAction.BACKOFF
        assert h.publisher.consecutive_failures == 4
        assert h.publisher.queue_depth() == 4  # buffered, not dropped

        h.transport.down = False
        while h.publisher.queue_depth():
            assert await h.tick() is PublishAction.COMMIT
        assert h.publisher.consecutive_failures == 0

    asyncio.run(h.run(scenario))

    assert h.actual == h.expected
    assert h.actual["orders_submitted"] == Decimal(4)
    # The last bucket collected mid-outage reports the outage as it stood:
    # three earlier snapshots still buffered, three failed attempts.
    gauges = h.service.stream_processor.store.gauges(_INSTANCE, at=h.at(30))
    assert gauges["publish_queue_depth"] == 3
    assert gauges["consecutive_publish_failures"] == 3


def test_idle_buckets_keep_the_backends_gauges_current() -> None:
    """FR-MET-024/028: through a quiet period the backend still receives a
    snapshot per bucket, so the gauges for the latest bucket are there and
    `seconds_since_last_event` keeps rising — while counters stay exactly
    what the busy bucket counted."""
    h = _Harness(bucket_seconds=10)
    store = h.service.stream_processor.store

    async def scenario() -> None:
        h.ingest(_order(h.at(0), 0))
        for closed_through in (10, 20, 30, 40):
            h.close_buckets_through(closed_through)
            assert await h.tick() is PublishAction.COMMIT

    asyncio.run(h.run(scenario))

    assert h.actual == h.expected
    assert h.actual["orders_submitted"] == Decimal(1)
    ages = [
        store.gauges(_INSTANCE, at=h.at(start))["seconds_since_last_event"]
        for start in (0, 10, 20, 30)
    ]
    assert ages == sorted(ages) and ages[0] < ages[-1]
    # Healthy publishing: each tick's batch commits, so the queue is empty
    # whenever the next bucket's gauges are read.
    assert store.gauges(_INSTANCE, at=h.at(30))["publish_queue_depth"] == 0
