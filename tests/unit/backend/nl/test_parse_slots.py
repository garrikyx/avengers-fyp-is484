"""LLM slot JSON normalization (Ollama-shaped payloads)."""

from __future__ import annotations

import pytest
from telemetry_backend.config import NlConfig
from telemetry_backend.nl.compiler import merge_interpreted_query
from telemetry_backend.nl.llm.parse_slots import parse_llm_slot_payload
from telemetry_backend.nl.llm.protocol import LlmSlotFillError
from telemetry_shared.models.metrics_query import QueryTimeRange
from telemetry_shared.models.nl_query import NlQueryContext


def test_coerce_duration_in_from_utc_to_last() -> None:
    result = parse_llm_slot_payload(
        {
            "intent": "latency_summary",
            "timeRange": {"fromUtc": "15m", "toUtc": "30m"},
            "filters": {"instanceId": "Magic"},
        }
    )
    assert result.time_range == QueryTimeRange(last="15m")
    assert result.filters == {"instanceId": "Magic"}


def test_valid_last_passthrough() -> None:
    result = parse_llm_slot_payload(
        {
            "intent": "alert_status",
            "timeRange": {"last": "30m"},
        }
    )
    assert result.time_range == QueryTimeRange(last="30m")


def test_invalid_time_range_dropped() -> None:
    result = parse_llm_slot_payload(
        {
            "intent": "latency_summary",
            "timeRange": {"fromUtc": "not-a-date", "toUtc": "also-not"},
        }
    )
    assert result.time_range is None


def test_sanitize_filters_drops_booleans_and_unknown_keys() -> None:
    result = parse_llm_slot_payload(
        {
            "intent": "alert_status",
            "timeRange": {
                "fromUtc": "2023-12-01T00:00:00Z",
                "toUtc": "2023-12-01T23:59:59Z",
            },
            "filters": {"magic": True, "application": "Magic"},
        }
    )
    assert result.filters == {"application": "Magic"}


def test_merge_succeeds_after_sanitize() -> None:
    parsed = parse_llm_slot_payload(
        {
            "intent": "alert_status",
            "filters": {"magic": True},
        }
    )
    merged = merge_interpreted_query(
        intent=parsed.intent,
        time_range=parsed.time_range,
        filters=parsed.filters,
        group_by=parsed.group_by,
        metrics=parsed.metrics,
        series=parsed.series,
        step=parsed.step,
        percentiles=parsed.percentiles,
        context=NlQueryContext(default_application="Magic"),
        config=NlConfig(),
    )
    assert merged.filters["application"] == "Magic"


def test_unsupported_intent_raises() -> None:
    with pytest.raises(LlmSlotFillError, match="not supported"):
        parse_llm_slot_payload({"intent": "weather_forecast"})


def test_placeholder_metrics_and_group_by_use_catalogue_defaults() -> None:
    parsed = parse_llm_slot_payload(
        {
            "intent": "latency_summary",
            "timeRange": {"last": "15m"},
            "filters": {"application": "Magic"},
            "groupBy": ["dimension"],
            "metrics": ["metric", "response_time"],
            "series": True,
            "step": "invalid",
        }
    )
    merged = merge_interpreted_query(
        intent=parsed.intent,
        time_range=parsed.time_range,
        filters=parsed.filters,
        group_by=parsed.group_by,
        metrics=parsed.metrics,
        series=parsed.series,
        step=parsed.step,
        percentiles=parsed.percentiles,
        context=NlQueryContext(default_application="Magic"),
        config=NlConfig(),
    )
    assert merged.metrics == ["throughput"]
    assert merged.group_by == ["instanceId"]
    assert merged.series is False
    assert merged.step == "1m"
