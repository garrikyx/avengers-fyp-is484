"""UBS-103: `BackendPublisher.publish_once()` against the full spec 007
§2.1 response table, driven with a scripted fake sink (single serial loop,
so responses are consumed in deterministic call order).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

import pytest
from publish_fixtures import AGENT_ID, APPLICATION, make_snapshot
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import PublishResult

_NOW = datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)
_ENDPOINT = "https://telemetry.internal.example/telemetry/batch"


class _FakeSink:
    def __init__(self, script: list[PublishResult]) -> None:
        self._script = deque(script)
        self.calls = 0

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> PublishResult:
        self.calls += 1
        if self._script:
            return self._script.popleft()
        return PublishResult(status_code=202, latency_ms=1.0)


def _publisher(sink: _FakeSink, **config_overrides: object) -> BackendPublisher:
    config = parse_publish_config({"endpoint": _ENDPOINT, **config_overrides})
    return BackendPublisher(sink, config, agent_id=AGENT_ID, application=APPLICATION)


def test_202_commits_and_empties_buffer() -> None:
    import asyncio

    sink = _FakeSink([PublishResult(status_code=202, latency_ms=1.0)])
    publisher = _publisher(sink)
    publisher.enqueue_snapshot(make_snapshot())

    action = asyncio.run(publisher.publish_once(now=_NOW))

    assert action is PublishAction.COMMIT
    assert publisher.queue_depth() == 0
    assert publisher.counters.snapshot()["publish_delivered"] == 1


def test_400_drops_the_whole_batch_as_one_rejection() -> None:
    import asyncio

    sink = _FakeSink([PublishResult(status_code=400, latency_ms=1.0)])
    publisher = _publisher(sink)
    publisher.enqueue_snapshot(make_snapshot())
    publisher.enqueue_snapshot(make_snapshot())  # both items go in ONE batch

    action = asyncio.run(publisher.publish_once(now=_NOW))

    assert action is PublishAction.DROP_REJECTED
    assert publisher.queue_depth() == 0  # the whole rejected batch was dropped
    assert publisher.counters.snapshot()["publish_rejected"] == 1


def test_400_logs_once_across_repeated_rejections(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Two separate batches both getting 400'd (e.g. a persistent schema
    bug) increments the counter each time but only logs the first -- a
    log flood is not the point, a rising counter is."""
    import asyncio

    caplog.set_level("ERROR", logger="telemetry_agent.publishing.publisher")
    sink = _FakeSink(
        [
            PublishResult(status_code=400, latency_ms=1.0),
            PublishResult(status_code=400, latency_ms=1.0),
        ]
    )
    publisher = _publisher(sink)
    publisher.enqueue_snapshot(make_snapshot())
    asyncio.run(publisher.publish_once(now=_NOW))
    publisher.enqueue_snapshot(make_snapshot())
    asyncio.run(publisher.publish_once(now=_NOW + timedelta(seconds=10)))

    assert publisher.counters.snapshot()["publish_rejected"] == 2
    assert len(caplog.records) == 1


def test_401_halts_alerts_and_probes_slowly_then_recovers() -> None:
    import asyncio

    sink = _FakeSink(
        [
            PublishResult(status_code=401, latency_ms=1.0),
            PublishResult(status_code=202, latency_ms=1.0),
        ]
    )
    reasons: list[str] = []
    config = parse_publish_config({"endpoint": _ENDPOINT, "haltProbeInterval": "20s"})
    publisher = BackendPublisher(
        sink,
        config,
        agent_id=AGENT_ID,
        application=APPLICATION,
        on_backend_unreachable=reasons.append,
    )
    publisher.enqueue_snapshot(make_snapshot())

    first = asyncio.run(publisher.publish_once(now=_NOW))
    too_soon = asyncio.run(publisher.publish_once(now=_NOW + timedelta(seconds=10)))
    recovered = asyncio.run(publisher.publish_once(now=_NOW + timedelta(seconds=20)))

    assert first is PublishAction.HALT
    assert too_soon is None  # skipped: probe interval not elapsed
    assert recovered is PublishAction.COMMIT
    assert sink.calls == 2  # the "too soon" tick never called the sink at all
    assert reasons == ["status=401"]
    assert publisher.queue_depth() == 0


def test_403_also_halts() -> None:
    import asyncio

    sink = _FakeSink([PublishResult(status_code=403, latency_ms=1.0)])
    publisher = _publisher(sink)
    publisher.enqueue_snapshot(make_snapshot())

    action = asyncio.run(publisher.publish_once(now=_NOW))

    assert action is PublishAction.HALT
    assert publisher.queue_depth() == 1  # item was requeued, not dropped


def test_413_halves_max_batch_items_and_requeues_for_a_smaller_retry() -> None:
    import asyncio

    sink = _FakeSink(
        [
            PublishResult(status_code=413, latency_ms=1.0),
            PublishResult(status_code=202, latency_ms=1.0),
        ]
    )
    publisher = _publisher(sink, maxBatchItems=4)
    for _ in range(4):
        publisher.enqueue_snapshot(make_snapshot())

    first = asyncio.run(publisher.publish_once(now=_NOW))
    second = asyncio.run(publisher.publish_once(now=_NOW + timedelta(seconds=10)))

    assert first is PublishAction.SPLIT
    assert second is PublishAction.COMMIT
    assert publisher.counters.snapshot()["publish_split"] == 1
    # first attempt sent all 4 (413'd, requeued); second sent only 2 (the
    # halved cap) and committed them, leaving 2 still buffered.
    assert publisher.queue_depth() == 2


def test_429_honours_retry_after() -> None:
    import asyncio

    sink = _FakeSink(
        [
            PublishResult(status_code=429, latency_ms=1.0, retry_after_seconds=30.0),
            PublishResult(status_code=202, latency_ms=1.0),
        ]
    )
    publisher = _publisher(sink)
    publisher.enqueue_snapshot(make_snapshot())

    first = asyncio.run(publisher.publish_once(now=_NOW))
    too_soon = asyncio.run(publisher.publish_once(now=_NOW + timedelta(seconds=10)))
    after_wait = asyncio.run(publisher.publish_once(now=_NOW + timedelta(seconds=31)))

    assert first is PublishAction.RETRY_AFTER
    assert too_soon is None
    assert after_wait is PublishAction.COMMIT
    assert sink.calls == 2


def test_5xx_and_transport_error_are_backoff_and_keep_data_buffered() -> None:
    import asyncio

    sink = _FakeSink([PublishResult(status_code=503, latency_ms=1.0)])
    publisher = _publisher(sink)
    publisher.enqueue_snapshot(make_snapshot())

    action = asyncio.run(publisher.publish_once(now=_NOW))

    assert action is PublishAction.BACKOFF
    assert publisher.queue_depth() == 1
    assert publisher.counters.snapshot()["publish_failed"] == 1


def test_nothing_to_send_returns_none_without_calling_sink() -> None:
    import asyncio

    sink = _FakeSink([])
    publisher = _publisher(sink)

    action = asyncio.run(publisher.publish_once(now=_NOW))

    assert action is None
    assert sink.calls == 0


def test_heartbeat_only_batch_is_sent_even_with_an_empty_buffer() -> None:
    import asyncio

    from telemetry_shared.models.ingestion import Heartbeat, ResourceUsage

    heartbeat = Heartbeat(
        schema_version=1,
        agent_id=AGENT_ID,
        instance_ids=["magic-prod-01"],
        sent_at_utc=_NOW,
        agent_version="0.1.0",
        uptime_seconds=10,
        status="healthy",
        parse_error_count_last5_min=0,
        callback_failures_last5_min=0,
        publish_queue_depth=0,
        publish_buffer_bytes=0,
        dropped_events_last5_min=0,
        active_alert_count=0,
        resource_usage=ResourceUsage(rss_mb=1, cpu_percent=1, active_tasks=1),
    )
    sink = _FakeSink([PublishResult(status_code=202, latency_ms=1.0)])
    config = parse_publish_config({"endpoint": _ENDPOINT})
    publisher = BackendPublisher(
        sink,
        config,
        agent_id=AGENT_ID,
        application=APPLICATION,
        heartbeat_provider=lambda: heartbeat,
    )

    action = asyncio.run(publisher.publish_once(now=_NOW))

    assert action is PublishAction.COMMIT
    assert sink.calls == 1
