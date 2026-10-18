"""Parse structured slot JSON from LLM responses (FR-NLQ-007)."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from telemetry_shared.models.metrics_query import QueryTimeRange

from telemetry_backend.nl.llm.protocol import LlmSlotFillError, LlmSlotResult

SLOT_FILL_SYSTEM_PROMPT = (
    "You map telemetry questions to structured slots only. "
    "Return JSON with keys: intent, timeRange (object with last or fromUtc/toUtc), "
    "filters (object), groupBy (array), metrics (array), series (bool), step (string). "
    "Use only intents from the provided catalogue. Never answer in prose."
)


def parse_llm_slot_payload(payload: dict[str, Any]) -> LlmSlotResult:
    intent = payload.get("intent")
    if not isinstance(intent, str):
        raise LlmSlotFillError("LLM response missing intent")
    time_range = payload.get("timeRange")
    parsed_range = None
    if isinstance(time_range, dict):
        try:
            parsed_range = QueryTimeRange.model_validate(time_range)
        except ValidationError as exc:
            raise LlmSlotFillError("LLM timeRange is invalid") from exc
    filters = payload.get("filters")
    group_by = payload.get("groupBy")
    metrics = payload.get("metrics")
    return LlmSlotResult(
        intent=intent,  # type: ignore[arg-type]
        time_range=parsed_range,
        filters=filters if isinstance(filters, dict) else None,
        group_by=group_by if isinstance(group_by, list) else None,
        metrics=metrics if isinstance(metrics, list) else None,
        series=(
            payload.get("series") if isinstance(payload.get("series"), bool) else None
        ),
        step=payload.get("step") if isinstance(payload.get("step"), str) else None,
        percentiles=(
            payload.get("percentiles")
            if isinstance(payload.get("percentiles"), dict)
            else None
        ),
    )
