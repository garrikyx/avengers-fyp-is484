"""UBS-104: offline buffering and backoff on publish failure.

- Real exponential backoff (`FR-PUB-005`) drives the `BACKOFF` action,
  replacing UBS-103's "just wait for the next external tick" placeholder.
- The buffer's drop-oldest eviction (`FR-PUB-004`) is counted, both on the
  Publisher's own `CounterRegistry` and through an external `on_drop` hook
  (what a supervisor would wire to `HealthReporter.record_dropped_events`).
"""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from publish_fixtures import AGENT_ID, APPLICATION, make_snapshot
from telemetry_agent.publishing.config import PublishConfig, parse_publish_config
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


def _config(**overrides: object) -> PublishConfig:
    return parse_publish_config(
        {
            "endpoint": _ENDPOINT,
            "retry": {"base": "1s", "factor": 2, "cap": "60s", "jitter": 0},
            **overrides,
        }
    )


# --- FR-PUB-005: real exponential backoff -------------------------------------------


def test_backoff_delay_grows_with_consecutive_failures_and_gates_retries() -> None:
    sink = _FakeSink(
        [
            PublishResult(status_code=503, latency_ms=1.0),
            PublishResult(status_code=503, latency_ms=1.0),
            PublishResult(status_code=202, latency_ms=1.0),
        ]
    )
    publisher = BackendPublisher(
        sink, _config(), agent_id=AGENT_ID, application=APPLICATION
    )
    publisher.enqueue_snapshot(make_snapshot())

    # attempt 1 fails -> backoff ~1s
    first = asyncio.run(publisher.publish_once(now=_NOW))
    assert first is PublishAction.BACKOFF
    assert sink.calls == 1

    # +0.5s: still within the 1s backoff window -> skipped, sink untouched
    too_soon = asyncio.run(
        publisher.publish_once(now=_NOW + timedelta(milliseconds=500))
    )
    assert too_soon is None
    assert sink.calls == 1

    # +1.1s: backoff elapsed -> attempt 2 fails -> backoff grows to ~2s
    second = asyncio.run(publisher.publish_once(now=_NOW + timedelta(seconds=1.1)))
    assert second is PublishAction.BACKOFF
    assert sink.calls == 2

    # +2s more (still short of the doubled ~2s delay) -> skipped again
    still_too_soon = asyncio.run(
        publisher.publish_once(now=_NOW + timedelta(seconds=2.1))
    )
    assert still_too_soon is None
    assert sink.calls == 2

    # +2.1s more: second backoff elapsed -> attempt 3 succeeds
    third = asyncio.run(publisher.publish_once(now=_NOW + timedelta(seconds=4.2)))
    assert third is PublishAction.COMMIT
    assert sink.calls == 3


def test_backoff_resets_after_a_successful_commit() -> None:
    # 4th call has no scripted response -> _FakeSink's default (202) fires,
    # which is exactly what lets this test prove the reset unambiguously:
    # if the ~1s delay after the commit had continued growing toward ~2s
    # instead of resetting, the 4th publish_once below would still be
    # gated (return None) rather than reaching the sink at all.
    sink = _FakeSink(
        [
            PublishResult(status_code=503, latency_ms=1.0),
            PublishResult(status_code=202, latency_ms=1.0),
            PublishResult(status_code=503, latency_ms=1.0),
        ]
    )
    publisher = BackendPublisher(
        sink, _config(), agent_id=AGENT_ID, application=APPLICATION
    )
    publisher.enqueue_snapshot(make_snapshot())
    asyncio.run(publisher.publish_once(now=_NOW))  # fails, backoff ~1s
    asyncio.run(publisher.publish_once(now=_NOW + timedelta(seconds=1.1)))  # commits

    publisher.enqueue_snapshot(make_snapshot())
    now2 = _NOW + timedelta(seconds=20)
    action = asyncio.run(publisher.publish_once(now=now2))  # fails again -> backoff ~1s
    assert action is PublishAction.BACKOFF
    assert sink.calls == 3

    recovered = asyncio.run(publisher.publish_once(now=now2 + timedelta(seconds=1.1)))

    assert recovered is PublishAction.COMMIT
    assert sink.calls == 4


def test_data_stays_buffered_through_repeated_backoff() -> None:
    sink = _FakeSink(
        [PublishResult(status_code=503, latency_ms=1.0) for _ in range(3)]
    )
    publisher = BackendPublisher(
        sink, _config(), agent_id=AGENT_ID, application=APPLICATION
    )
    publisher.enqueue_snapshot(make_snapshot())

    asyncio.run(publisher.publish_once(now=_NOW))

    assert publisher.queue_depth() == 1  # never lost, just backing off
    assert publisher.counters.snapshot()["publish_failed"] == 1


# --- FR-PUB-004: counted drop-oldest, both internally and externally ---------------


def test_buffer_overflow_counts_on_both_the_internal_counter_and_the_hook() -> None:
    dropped_via_hook = 0

    def on_drop() -> None:
        nonlocal dropped_via_hook
        dropped_via_hook += 1

    config = parse_publish_config({"endpoint": _ENDPOINT, "bufferBytes": 420})
    publisher = BackendPublisher(
        _FakeSink([]),
        config,
        agent_id=AGENT_ID,
        application=APPLICATION,
        on_drop=on_drop,
    )

    for _ in range(5):  # each ~208 bytes; 420 bytes fits 2
        publisher.enqueue_snapshot(make_snapshot())

    assert publisher.queue_depth() == 2
    assert dropped_via_hook == 3
    assert publisher.counters.snapshot()["publish_dropped_items"] == 3


def test_age_eviction_runs_on_each_publish_tick() -> None:
    config = parse_publish_config(
        {"endpoint": _ENDPOINT, "bufferMaxAge": "60s"}
    )
    dropped = 0

    def on_drop() -> None:
        nonlocal dropped
        dropped += 1

    publisher = BackendPublisher(
        _FakeSink([]),
        config,
        agent_id=AGENT_ID,
        application=APPLICATION,
        on_drop=on_drop,
    )
    publisher.enqueue_snapshot(make_snapshot(), now=_NOW)

    # Nothing else to send and 90s > the 60s max age -> expire() drops it
    # even though publish_once finds an empty buffer afterwards.
    action = asyncio.run(publisher.publish_once(now=_NOW + timedelta(seconds=90)))

    assert action is None  # nothing left to send once expiry ran
    assert dropped == 1
    assert publisher.queue_depth() == 0
