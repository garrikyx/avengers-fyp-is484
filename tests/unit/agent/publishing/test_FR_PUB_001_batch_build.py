from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from publish_fixtures import (
    AGENT_ID,
    APPLICATION,
    make_alert,
    make_event,
    make_snapshot,
)
from telemetry_agent.publishing.batch import BatchSequencer, build_batch
from telemetry_agent.publishing.buffer import make_pending_item

_NOW = datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)


def test_build_batch_sorts_items_into_the_right_arrays() -> None:
    items = [
        make_pending_item("snapshot", make_snapshot(), _NOW),
        make_pending_item("event", make_event(), _NOW),
        make_pending_item("alert", make_alert(), _NOW),
    ]

    batch = build_batch(
        items,
        agent_id=AGENT_ID,
        application=APPLICATION,
        sequencer=BatchSequencer(),
        heartbeat=None,
        now=_NOW,
    )

    assert len(batch.snapshots) == 1
    assert len(batch.events) == 1
    assert len(batch.alerts) == 1
    assert batch.heartbeat is None


def test_build_batch_envelope_fields() -> None:
    batch = build_batch(
        [],
        agent_id=AGENT_ID,
        application=APPLICATION,
        sequencer=BatchSequencer(),
        heartbeat=None,
        now=_NOW,
    )

    assert batch.schema_version == 1
    assert isinstance(batch.batch_id, UUID)
    assert batch.batch_id.version == 7
    assert batch.agent_id == AGENT_ID
    assert batch.application == APPLICATION
    assert batch.sent_at_utc == _NOW


def test_batch_sequencer_seq_is_monotonic_and_ids_differ() -> None:
    sequencer = BatchSequencer()

    first = build_batch(
        [], agent_id=AGENT_ID, application=APPLICATION, sequencer=sequencer,
        heartbeat=None, now=_NOW,
    )
    second = build_batch(
        [], agent_id=AGENT_ID, application=APPLICATION, sequencer=sequencer,
        heartbeat=None, now=_NOW,
    )

    assert second.batch_seq == first.batch_seq + 1
    assert second.batch_id != first.batch_id


def test_build_batch_with_only_a_heartbeat_and_no_items() -> None:
    from telemetry_shared.models.ingestion import Heartbeat, ResourceUsage

    heartbeat = Heartbeat(
        schema_version=1,
        agent_id=AGENT_ID,
        instance_ids=["magic-prod-01"],
        sent_at_utc=_NOW,
        agent_version="0.1.0",
        uptime_seconds=100,
        status="healthy",
        parse_error_count_last5_min=0,
        callback_failures_last5_min=0,
        publish_queue_depth=0,
        publish_buffer_bytes=0,
        dropped_events_last5_min=0,
        active_alert_count=0,
        resource_usage=ResourceUsage(rss_mb=10, cpu_percent=1, active_tasks=1),
    )

    batch = build_batch(
        [], agent_id=AGENT_ID, application=APPLICATION, sequencer=BatchSequencer(),
        heartbeat=heartbeat, now=_NOW,
    )

    assert batch.snapshots == []
    assert batch.heartbeat is heartbeat
