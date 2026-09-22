"""FR-PUB-001/003: assembles a `TelemetryBatch` from buffered items plus
an optional heartbeat.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.ingestion import Heartbeat, TelemetryBatch, TelemetryEvent
from telemetry_shared.models.snapshot import Snapshot

from telemetry_agent.publishing.buffer import PendingItem

_SCHEMA_VERSION: Literal[1] = 1


@dataclass(slots=True)
class BatchSequencer:
    """`FR-PUB-003`: a monotonically increasing `batchSeq` per agent, and a
    stable `batchId` (UUIDv7 — time-sortable, and available natively from
    Python 3.14) so the backend can deduplicate retries idempotently.
    """

    _next_seq: int = field(default=0)

    def next_batch_id(self) -> uuid.UUID:
        return uuid.uuid7()

    def next_seq(self) -> int:
        seq = self._next_seq
        self._next_seq += 1
        return seq


def build_batch(
    items: list[PendingItem],
    *,
    agent_id: str,
    application: str,
    sequencer: BatchSequencer,
    heartbeat: Heartbeat | None,
    now: datetime,
) -> TelemetryBatch:
    """`FR-PUB-001`: one batch containing whatever snapshots/events/alerts
    were pulled from the buffer plus (optionally) a heartbeat. `items` may
    be empty when there's nothing but a heartbeat to send.
    """
    snapshots: list[Snapshot] = []
    events: list[TelemetryEvent] = []
    alerts: list[AlertEvent] = []
    for item in items:
        if isinstance(item.payload, Snapshot):
            snapshots.append(item.payload)
        elif isinstance(item.payload, TelemetryEvent):
            events.append(item.payload)
        else:
            alerts.append(item.payload)

    return TelemetryBatch(
        schema_version=_SCHEMA_VERSION,
        batch_id=sequencer.next_batch_id(),
        batch_seq=sequencer.next_seq(),
        agent_id=agent_id,
        application=application,
        sent_at_utc=now,
        snapshots=snapshots,
        events=events,
        alerts=alerts,
        heartbeat=heartbeat,
    )
