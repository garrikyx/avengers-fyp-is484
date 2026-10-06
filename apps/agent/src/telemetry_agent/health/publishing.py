"""Connect the Health Reporter to the Backend Publisher (UBS-58, UBS-60).

The heartbeat reaches the backend only through the Backend Publisher: it
rides in the `heartbeat` slot of every `TelemetryBatch` (UBS-58/66 contract,
`POST /telemetry/batch`). The reporter never talks to the backend itself.

Two directions, both set up here so every caller wires them the same way:

- reporter -> publisher: `heartbeat_provider(reporter)` is what the publisher
  calls once per publish tick to get the current heartbeat.
- publisher -> reporter: the publisher's outbox size, buffer bytes and drops
  feed the heartbeat's `publishQueueDepth` / `publishBufferBytes` /
  `droppedEventsLast5Min` (UBS-60).

    reporter = HealthReporter(monitors, heartbeat=cfg)
    publisher = BackendPublisher(
        sink, publish_cfg, agent_id=..., application=...,
        heartbeat_provider=heartbeat_provider(reporter),
        on_drop=drop_hook(reporter),
    )
    connect_reporter_to_publisher(reporter, publisher)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.health.wire import to_ingestion_heartbeat
from telemetry_shared.models.ingestion import Heartbeat

if TYPE_CHECKING:
    from telemetry_agent.publishing.publisher import BackendPublisher


def heartbeat_provider(
    reporter: HealthReporter, *, default_instance_id: str | None = None
) -> Callable[[], Heartbeat]:
    """The publisher's `heartbeat_provider`: a fresh, wire-shaped heartbeat on
    every call, so each batch carries the reporter's state at send time."""

    def provide() -> Heartbeat:
        return to_ingestion_heartbeat(
            reporter.build_heartbeat(), default_instance_id=default_instance_id
        )

    return provide


def drop_hook(reporter: HealthReporter) -> Callable[[], None]:
    """The publisher's `on_drop`: one item evicted from a full outbox counts
    towards `droppedEventsLast5Min`."""

    def on_drop() -> None:
        reporter.record_dropped_events(1)

    return on_drop


def connect_reporter_to_publisher(
    reporter: HealthReporter, publisher: BackendPublisher
) -> None:
    """Point the reporter's outbox signals at the publisher (UBS-60).

    Also records zero drops up front, so `droppedEventsLast5Min` reads 0
    rather than null ("not measured", FR-HLT-004) once a publisher exists.
    """
    reporter.set_queue_depth_provider(publisher.queue_depth)
    reporter.set_buffer_bytes_provider(publisher.buffer_bytes)
    reporter.record_dropped_events(0)
