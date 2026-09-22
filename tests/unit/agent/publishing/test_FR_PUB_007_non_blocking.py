"""FR-PUB-007: publishing MUST NOT block aggregation or rule evaluation --
`enqueue_*` must be a plain synchronous call that never awaits and never
blocks, even while the buffer is full (it drops the oldest item instead).
"""

from __future__ import annotations

import inspect
from typing import NoReturn

from publish_fixtures import (
    AGENT_ID,
    APPLICATION,
    make_alert,
    make_event,
    make_snapshot,
)
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher

_ENDPOINT = "https://telemetry.internal.example/telemetry/batch"


class _NeverCalledSink:
    async def send(  # pragma: no cover
        self, *, body: bytes, headers: object
    ) -> NoReturn:
        raise AssertionError("enqueue_* must never reach the sink")


def _publisher(**overrides: object) -> BackendPublisher:
    config = parse_publish_config({"endpoint": _ENDPOINT, **overrides})
    return BackendPublisher(
        _NeverCalledSink(), config, agent_id=AGENT_ID, application=APPLICATION
    )


def test_enqueue_methods_are_plain_sync_functions() -> None:
    publisher = _publisher()
    assert not inspect.iscoroutinefunction(publisher.enqueue_snapshot)
    assert not inspect.iscoroutinefunction(publisher.enqueue_event)
    assert not inspect.iscoroutinefunction(publisher.enqueue_alert)


def test_enqueue_never_touches_the_sink_even_when_the_buffer_overflows() -> None:
    publisher = _publisher(maxBufferItems=2)

    for _ in range(10):
        publisher.enqueue_snapshot(make_snapshot())
    publisher.enqueue_event(make_event())
    publisher.enqueue_alert(make_alert())

    assert publisher.queue_depth() == 2  # drop-oldest, never grows past the cap
