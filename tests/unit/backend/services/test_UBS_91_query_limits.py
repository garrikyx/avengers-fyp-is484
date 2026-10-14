"""UBS-91: query clamping, timeouts, and dataCompleteness envelope."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest
from telemetry_backend.config import QueryConfig, StreamProcessorConfig
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import (
    QueryEngine,
    QueryTimeoutError,
    QueryValidationError,
)
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.metrics_query import MetricsQueryRequest, QueryTimeRange

from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot


def _engine(*, query_config: QueryConfig | None = None) -> QueryEngine:
    processor = StreamProcessor(StreamProcessorConfig(), store=MetricStore())
    processor.store.merge(
        make_snapshot(counters={"orders_submitted": 5}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    return QueryEngine(
        processor.store,
        stream_processor=processor,
        query_config=query_config or QueryConfig(),
    )


def _request(**overrides: object) -> MetricsQueryRequest:
    payload = {
        "time_range": QueryTimeRange(
            from_utc=BASE_TIME,
            to_utc=BASE_TIME + timedelta(minutes=5),
        ),
        "filters": {"instanceId": "magic-prod-01"},
        "metrics": ["orders"],
        **overrides,
    }
    return MetricsQueryRequest.model_validate(payload)


def test_UBS_91_max_range_seconds_returns_400() -> None:
    engine = _engine(query_config=QueryConfig(max_range_seconds=60))
    request = _request(
        time_range=QueryTimeRange(
            from_utc=BASE_TIME,
            to_utc=BASE_TIME + timedelta(hours=2),
        )
    )

    with pytest.raises(QueryValidationError) as exc:
        engine._execute_sync(request, now=NOW)

    assert exc.value.code == "invalid_time_range"
    assert "maxRangeSeconds" in exc.value.issue


def test_UBS_91_max_series_points_returns_400() -> None:
    engine = _engine(query_config=QueryConfig(max_series_points=2))
    request = _request(
        series=True,
        step="1m",
        time_range=QueryTimeRange(
            from_utc=BASE_TIME,
            to_utc=BASE_TIME + timedelta(minutes=10),
        ),
    )

    with pytest.raises(QueryValidationError) as exc:
        engine._execute_sync(request, now=NOW)

    assert "maxSeriesPoints" in exc.value.issue


def test_UBS_91_response_includes_data_completeness() -> None:
    engine = _engine()
    response = engine._execute_sync(_request(), now=NOW)

    assert response.query_id.startswith("q-")
    assert response.data_completeness.agents_reporting >= 1
    assert response.data_completeness.confidence in {"complete", "partial", "degraded"}


def test_UBS_91_query_timeout_returns_error() -> None:
    class SlowEngine(QueryEngine):
        def _execute_sync(self, request, *, now):  # type: ignore[no-untyped-def]
            import time

            time.sleep(0.05)
            return super()._execute_sync(request, now=now)

    processor = StreamProcessor(StreamProcessorConfig(), store=MetricStore())
    processor.store.merge(
        make_snapshot(counters={"orders_submitted": 5}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    slow = SlowEngine(
        processor.store,
        stream_processor=processor,
        query_config=QueryConfig(query_timeout_seconds=0.001),
    )

    with pytest.raises(QueryTimeoutError):
        asyncio.run(slow.query(_request(), now=NOW))
