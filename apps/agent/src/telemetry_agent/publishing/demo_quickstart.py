"""Minimal walkthrough of the Backend Publisher (UBS-103/104).

    uv run python -m telemetry_agent.publishing.demo_quickstart

Six batches through the publisher: one delivers cleanly, one gets a
permanent 400 rejection, one is met with a 401 (watch it halt, alert, and
recover once the backend "fixes itself"), one is too big and gets 413'd
(watch `maxBatchItems` halve and a smaller retry succeed), one hits a
sustained 503 outage (watch the backoff delay grow between attempts --
UBS-104), and one overflows a tiny buffer (watch drop-oldest, counted, and
those counts show up in a real Health Reporter heartbeat). No real
network calls — a small scripted sink stands in for the backend, and
since the Publisher runs one serial loop (not concurrent workers like the
Callback Dispatcher), its responses are consumed in a simple, deterministic
order — the same idea as `callbacks/demo_quickstart.py`.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from collections import deque
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from telemetry_shared.models.snapshot import Snapshot

from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import PublishResult

sys.stdout.reconfigure(line_buffering=True)  # type: ignore[union-attr]
logging.basicConfig(level=logging.INFO, format="  %(message)s", stream=sys.stdout)

_AGENT_ID = "magic-agent-sg-01"
_APPLICATION = "Magic"
_ENDPOINT = "https://telemetry.internal.example/telemetry/batch"


class _ScriptedSink:
    """Stands in for the backend: returns responses from a fixed script,
    one per call, in order."""

    def __init__(self, script: list[PublishResult]) -> None:
        self._script = deque(script)

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> PublishResult:
        print(f"  >> POST {_ENDPOINT}")
        print(f"     Content-Encoding: {headers.get('Content-Encoding', '(none)')}")
        print(f"     body ({len(body)} bytes)")
        result = (
            self._script.popleft()
            if self._script
            else PublishResult(status_code=202, latency_ms=5.0)
        )
        print(f"  << {result.status_code}")
        return result


def _step(title: str) -> None:
    print(f"\n--- {title} ---")


def _make_snapshot(**overrides: object) -> Snapshot:
    defaults: dict[str, object] = dict(
        schema_version=1,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
        instance_id="magic-prod-01",
        bucket_start_utc=datetime.now(UTC),
        bucket_seconds=10,
    )
    defaults.update(overrides)
    return Snapshot(**defaults)  # type: ignore[arg-type]


def _print_state(publisher: BackendPublisher) -> None:
    print(f"  counters: {publisher.counters.snapshot()}")
    print(
        f"  queue depth: {publisher.queue_depth()}, "
        f"buffer bytes: {publisher.buffer_bytes()}"
    )


async def _drain(publisher: BackendPublisher, *, ticks: int, now: datetime) -> None:
    for i in range(ticks):
        action = await publisher.publish_once(now=now + timedelta(seconds=10 * i))
        print(f"  tick {i}: {action}")


def main() -> None:
    print("=" * 60)
    print("BACKEND PUBLISHER — accepted, rejected, halted, split")
    print("=" * 60)

    config = parse_publish_config({"endpoint": _ENDPOINT})
    now = datetime.now(UTC)

    _step("1. Snapshot batch -> backend accepts it")
    publisher_1 = BackendPublisher(
        _ScriptedSink([PublishResult(status_code=202, latency_ms=5.0)]),
        config,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
    )
    publisher_1.enqueue_snapshot(_make_snapshot())
    asyncio.run(_drain(publisher_1, ticks=1, now=now))
    _print_state(publisher_1)

    _step("2. Malformed batch -> backend rejects with 400 (dropped, logged once)")
    publisher_2 = BackendPublisher(
        _ScriptedSink([PublishResult(status_code=400, latency_ms=5.0)]),
        config,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
    )
    publisher_2.enqueue_snapshot(_make_snapshot())
    asyncio.run(_drain(publisher_2, ticks=1, now=now))
    _print_state(publisher_2)

    _step("3. Backend returns 401 -> publisher halts, alerts, then recovers on probe")
    fast_probe_config = parse_publish_config(
        {"endpoint": _ENDPOINT, "haltProbeInterval": "20s"}
    )
    unreachable_reasons: list[str] = []
    publisher_3 = BackendPublisher(
        _ScriptedSink(
            [
                PublishResult(status_code=401, latency_ms=5.0),
                PublishResult(status_code=202, latency_ms=5.0),
            ]
        ),
        fast_probe_config,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
        on_backend_unreachable=unreachable_reasons.append,
    )
    publisher_3.enqueue_snapshot(_make_snapshot())
    # tick 0: 401 -> halt. tick 1 (+10s): too soon to probe (20s interval),
    # skipped entirely. tick 2 (+20s): probe due -> 202 -> recovers.
    asyncio.run(_drain(publisher_3, ticks=3, now=now))
    print(f"  on_backend_unreachable fired with: {unreachable_reasons}")
    _print_state(publisher_3)

    _step(
        "4. Oversized batch -> backend 413s, publisher halves maxBatchItems and resends"
    )
    small_batch_config = parse_publish_config(
        {"endpoint": _ENDPOINT, "maxBatchItems": 4}
    )
    publisher_4 = BackendPublisher(
        _ScriptedSink(
            [
                PublishResult(status_code=413, latency_ms=5.0),
                PublishResult(status_code=202, latency_ms=5.0),
            ]
        ),
        small_batch_config,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
    )
    for i in range(4):
        publisher_4.enqueue_snapshot(
            _make_snapshot(bucket_start_utc=now + timedelta(seconds=i))
        )
    # tick 0: sends all 4 -> 413 -> halves maxBatchItems to 2, requeues all 4.
    # tick 1: sends 2 -> 202 -> accepted; 2 items remain buffered for next tick.
    asyncio.run(_drain(publisher_4, ticks=2, now=now))
    _print_state(publisher_4)

    _step(
        "5. Sustained 503 outage -> backoff grows each attempt (UBS-104), then recovers"
    )
    fast_backoff_config = parse_publish_config(
        {
            "endpoint": _ENDPOINT,
            "retry": {"base": "1s", "factor": 2, "cap": "60s", "jitter": 0},
        }
    )
    publisher_5 = BackendPublisher(
        _ScriptedSink(
            [
                PublishResult(status_code=503, latency_ms=5.0),
                PublishResult(status_code=503, latency_ms=5.0),
                PublishResult(status_code=503, latency_ms=5.0),
                PublishResult(status_code=202, latency_ms=5.0),
            ]
        ),
        fast_backoff_config,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
    )
    publisher_5.enqueue_snapshot(_make_snapshot())
    # Each 503 grows the backoff delay (1s, 2s, 4s...); a 10s tick interval
    # always clears it, so every tick here actually attempts a send.
    asyncio.run(_drain(publisher_5, ticks=4, now=now))
    _print_state(publisher_5)

    _step(
        "6. Buffer overflow -> drop-oldest, counted, and visible in a real heartbeat"
    )
    health_reporter = HealthReporter(
        monitors={},
        heartbeat=HeartbeatConfig(
            agent_id=_AGENT_ID,
            instance_ids=("magic-prod-01",),
            agent_version="0.1.0",
        ),
    )
    tiny_buffer_config = parse_publish_config(
        {"endpoint": _ENDPOINT, "bufferBytes": 500}
    )
    publisher_6 = BackendPublisher(
        _ScriptedSink([]),  # never drained in this step -- purely an enqueue demo
        tiny_buffer_config,
        agent_id=_AGENT_ID,
        application=_APPLICATION,
        on_drop=lambda: health_reporter.record_dropped_events(1),
    )
    health_reporter.set_queue_depth_provider(publisher_6.queue_depth)
    health_reporter.set_buffer_bytes_provider(publisher_6.buffer_bytes)

    for i in range(5):
        publisher_6.enqueue_snapshot(
            _make_snapshot(bucket_start_utc=now + timedelta(seconds=i))
        )
    print(
        f"  enqueued 5 snapshots into a {tiny_buffer_config.buffer_bytes}-byte buffer"
    )
    _print_state(publisher_6)

    heartbeat = health_reporter.build_heartbeat(now=now)
    print(f"  heartbeat.publishQueueDepth = {heartbeat.publish_queue_depth}")
    print(f"  heartbeat.publishBufferBytes = {heartbeat.publish_buffer_bytes}")
    print(f"  heartbeat.droppedEventsLast5Min = {heartbeat.dropped_events_last5_min}")


if __name__ == "__main__":
    main()
