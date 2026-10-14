"""Shared fixtures for metrics query tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_shared.models.snapshot import SeriesEntry, Snapshot

INSTANCE_ID = "magic-prod-01"


def _aligned_now() -> datetime:
    now = datetime.now(UTC)
    epoch = int(now.timestamp())
    aligned = (epoch // 10) * 10
    return datetime.fromtimestamp(aligned, tz=UTC)


BASE_TIME = _aligned_now() - timedelta(minutes=2)
NOW = BASE_TIME + timedelta(seconds=30)


def make_snapshot(
    *,
    agent_id: str = "agent-a",
    instance_id: str = INSTANCE_ID,
    application: str = "Magic",
    counters: dict[str, int] | None = None,
    dimensions: dict[str, str] | None = None,
    bucket_start: datetime | None = None,
) -> Snapshot:
    dims = dimensions or {"session_id": "MAGIC->EXCH1", "symbol": "ABC"}
    return Snapshot(
        schema_version=1,
        agent_id=agent_id,
        application=application,
        instance_id=instance_id,
        bucket_start_utc=bucket_start or BASE_TIME,
        bucket_seconds=10,
        series=[
            SeriesEntry(
                dimensions=dims,
                counters={k: Decimal(v) for k, v in (counters or {}).items()},
            )
        ],
    )
