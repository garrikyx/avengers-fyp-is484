"""Parse structured slot JSON from LLM responses (FR-NLQ-007)."""

from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError
from telemetry_shared.models.metrics_query import QueryTimeRange

from telemetry_backend.nl.catalogue import SUPPORTED_INTENTS
from telemetry_backend.nl.llm.protocol import (
    NO_INTENT,
    LlmSlotFillError,
    LlmSlotResult,
)

_RELATIVE_DURATION_RE = re.compile(r"^(\d+)(s|m|h)$", re.IGNORECASE)
_ALLOWED_FILTER_KEYS = frozenset({"application", "instanceId", "symbol", "session"})

SLOT_FILL_SYSTEM_PROMPT = (
    "You map telemetry questions about the Magic trading application to JSON slots. "
    "Return JSON only, with keys: intent, timeRange, filters, reply. "
    'intent must be one of the catalogue intents, or "none" when the question is '
    "not about telemetry. "
    'timeRange: {"last": "15m"} for relative windows (15m, 30m, 1h); '
    "ISO-8601 UTC fromUtc and toUtc only for absolute ranges; omit when not stated. "
    "filters: string values only, keys application, instanceId, symbol, session. "
    'reply: only when intent is "none": one or two short, friendly sentences. '
    "Say you only answer questions about Magic telemetry (order flow, rejects, "
    "latency, alerts, agent health). Never offer help with anything else, never "
    "include numbers and never state facts about telemetry, orders, alerts or "
    "system status."
)


def parse_llm_slot_payload(payload: dict[str, Any]) -> LlmSlotResult:
    intent = payload.get("intent")
    if not isinstance(intent, str):
        raise LlmSlotFillError("LLM response missing intent")
    if intent == NO_INTENT:
        reply = payload.get("reply")
        return LlmSlotResult(
            intent=NO_INTENT, reply=reply if isinstance(reply, str) else None
        )
    if intent not in SUPPORTED_INTENTS:
        raise LlmSlotFillError(f"LLM intent {intent!r} is not supported")

    parsed_range = _normalize_time_range(payload.get("timeRange"))
    filters = _sanitize_filters(payload.get("filters"))
    group_by = payload.get("groupBy")
    metrics = payload.get("metrics")
    return LlmSlotResult(
        intent=intent,
        time_range=parsed_range,
        filters=filters,
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


def _normalize_time_range(raw: object) -> QueryTimeRange | None:
    if not isinstance(raw, dict):
        return None
    try:
        return QueryTimeRange.model_validate(raw)
    except ValidationError:
        pass

    last = raw.get("last")
    if isinstance(last, str) and _RELATIVE_DURATION_RE.match(last.strip()):
        try:
            return QueryTimeRange.model_validate({"last": last.strip().lower()})
        except ValidationError:
            pass

    from_val = raw.get("fromUtc")
    if from_val is None:
        from_val = raw.get("from_utc")
    to_val = raw.get("toUtc")
    if to_val is None:
        to_val = raw.get("to_utc")
    if isinstance(from_val, str) and _RELATIVE_DURATION_RE.match(from_val.strip()):
        duration = from_val.strip().lower()
        if to_val is None or (
            isinstance(to_val, str) and _RELATIVE_DURATION_RE.match(to_val.strip())
        ):
            try:
                return QueryTimeRange.model_validate({"last": duration})
            except ValidationError:
                pass

    if isinstance(from_val, str) and isinstance(to_val, str):
        try:
            return QueryTimeRange.model_validate({"fromUtc": from_val, "toUtc": to_val})
        except ValidationError:
            pass

    return None


def _sanitize_filters(raw: object) -> dict[str, str | list[str]] | None:
    if not isinstance(raw, dict):
        return None
    out: dict[str, str | list[str]] = {}
    for key, value in raw.items():
        if key not in _ALLOWED_FILTER_KEYS:
            continue
        if isinstance(value, str) and value.strip():
            out[key] = value.strip()
        elif isinstance(value, list):
            strings = [item for item in value if isinstance(item, str) and item.strip()]
            if strings:
                out[key] = strings
    return out or None


def slot_json_schema() -> dict[str, Any]:
    """JSON Schema for constrained decoding (Ollama `format`); slot schema is the
    security boundary (FR-NLQ-023), so only these keys can come back."""
    return {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": [*SUPPORTED_INTENTS, NO_INTENT]},
            "timeRange": {
                "type": "object",
                "properties": {
                    "last": {"type": "string"},
                    "fromUtc": {"type": "string"},
                    "toUtc": {"type": "string"},
                },
            },
            "filters": {
                "type": "object",
                "properties": {
                    key: {"type": "string"} for key in sorted(_ALLOWED_FILTER_KEYS)
                },
            },
            "reply": {"type": "string"},
        },
        "required": ["intent"],
    }
