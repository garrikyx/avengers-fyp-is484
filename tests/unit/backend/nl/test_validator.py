"""Interpreted query validation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.nl.validator import (
    InterpretedValidationError,
    validate_interpreted_query,
)
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.metrics_query import QueryTimeRange
from telemetry_shared.models.nl_query import InterpretedQuery

NOW = datetime(2026, 6, 12, 4, 0, tzinfo=UTC)


def _engine() -> QueryEngine:
    processor = StreamProcessor(StreamProcessorConfig(), store=MetricStore())
    return QueryEngine(
        processor.store,
        stream_processor=processor,
        agent_registry=AgentRegistry(),
    )


def test_unknown_metric_is_rejected() -> None:
    engine = _engine()
    interpreted = InterpretedQuery(
        intent="rejection_summary",
        time_range=QueryTimeRange(last="30m"),
        metrics=["not_a_real_metric"],
    )
    with pytest.raises(InterpretedValidationError):
        validate_interpreted_query(
            interpreted, engine=engine, store=engine.store, now=NOW
        )


def test_symbol_drilldown_requires_symbol() -> None:
    engine = _engine()
    interpreted = InterpretedQuery(
        intent="symbol_drilldown",
        time_range=QueryTimeRange(last="30m"),
        metrics=["orders_rejected"],
    )
    with pytest.raises(InterpretedValidationError):
        validate_interpreted_query(
            interpreted, engine=engine, store=engine.store, now=NOW
        )
