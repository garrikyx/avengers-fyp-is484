"""LLM slot-filling protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from telemetry_shared.models.nl_query import IntentId


@dataclass(frozen=True, slots=True)
class LlmSlotResult:
    intent: IntentId
    time_range: object | None = None
    filters: dict[str, str | list[str]] | None = None
    group_by: list[str] | None = None
    metrics: list[str] | None = None
    series: bool | None = None
    step: str | None = None
    percentiles: dict[str, list[int]] | None = None


class LlmSlotFillError(Exception):
    """Structured slot fill failed or timed out."""


class LlmSlotFiller(Protocol):
    async def fill_slots(
        self,
        question: str,
        *,
        catalogue_summary: str,
        schema_json: str,
    ) -> LlmSlotResult: ...
