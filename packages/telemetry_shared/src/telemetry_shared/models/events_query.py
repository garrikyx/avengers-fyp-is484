"""Event query response models (UBS-118)."""

from __future__ import annotations

from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.ingestion import TelemetryEvent


class EventsListResponse(CamelModel):
    """Response for `GET /telemetry/events`."""

    events: list[TelemetryEvent]
    truncated: bool = False
