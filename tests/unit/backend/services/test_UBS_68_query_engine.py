"""UBS-68: metrics query engine filters, grouping, and retention errors."""

from __future__ import annotations

from datetime import timedelta

import pytest
from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine, QueryValidationError
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.metrics_query import MetricsQueryRequest, QueryTimeRange

from tests.unit.backend.services.query_fixtures import (
    BASE_TIME,
    INSTANCE_ID,
    NOW,
    make_snapshot,
)


def _engine(store: MetricStore | None = None) -> QueryEngine:
    processor = StreamProcessor(StreamProcessorConfig(), store=store or MetricStore())
    return QueryEngine(
        processor.store,
        stream_processor=processor,
        agent_registry=AgentRegistry(),
    )


def _request(**overrides: object) -> MetricsQueryRequest:
    payload = {
        "time_range": QueryTimeRange(
            from_utc=BASE_TIME,
            to_utc=BASE_TIME + timedelta(minutes=5),
        ),
        "filters": {"instanceId": INSTANCE_ID},
        "metrics": ["orders", "rejections", "rejectRate"],
        **overrides,
    }
    return MetricsQueryRequest.model_validate(payload)


def test_UBS_68_totals_and_reject_rate_from_two_agents() -> None:
    store = MetricStore(StreamProcessorConfig())
    store.merge(
        make_snapshot(
            agent_id="agent-a",
            counters={
                "orders_submitted": 100,
                "orders_acked": 90,
                "orders_rejected": 10,
            },
        ),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    store.merge(
        make_snapshot(
            agent_id="agent-b",
            counters={
                "orders_submitted": 100,
                "orders_acked": 80,
                "orders_rejected": 20,
            },
        ),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    engine = _engine(store)

    response = engine._execute_sync(_request(), now=NOW)

    assert response.totals["orders"] == 200
    assert response.totals["rejections"] == 30
    assert response.totals["rejectRate"] == pytest.approx(30 / 200)


def test_UBS_68_group_by_reject_reason() -> None:
    store = MetricStore(StreamProcessorConfig())
    store.merge(
        make_snapshot(
            counters={"orders_rejected": 5},
            dimensions={
                "session_id": "MAGIC->EXCH1",
                "symbol": "ABC",
                "reject_reason": "OrderExceedsLimit",
            },
        ),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    store.merge(
        make_snapshot(
            counters={"orders_rejected": 3},
            dimensions={
                "session_id": "MAGIC->EXCH1",
                "symbol": "ABC",
                "reject_reason": "UnknownSymbol",
            },
        ),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    engine = _engine(store)
    request = _request(
        metrics=["rejections"],
        group_by=["rejectReason"],
    )

    response = engine._execute_sync(request, now=NOW)

    assert len(response.groups) == 2
    reasons = {group.dimensions["rejectReason"] for group in response.groups}
    assert reasons == {"OrderExceedsLimit", "UnknownSymbol"}


def test_UBS_68_retention_outside_window_returns_clear_error() -> None:
    store = MetricStore(StreamProcessorConfig())
    store.merge(
        make_snapshot(counters={"orders_submitted": 1}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    engine = _engine(store)
    request = _request(
        time_range=QueryTimeRange(
            from_utc=BASE_TIME - timedelta(hours=8),
            to_utc=BASE_TIME - timedelta(hours=7),
        )
    )

    with pytest.raises(QueryValidationError) as exc:
        engine._execute_sync(request, now=NOW)

    assert exc.value.code == "invalid_time_range"
    assert "available range is" in exc.value.issue


def test_UBS_68_application_filter_selects_instances() -> None:
    store = MetricStore(StreamProcessorConfig())
    store.merge(
        make_snapshot(
            instance_id="magic-prod-01",
            application="Magic",
            counters={"orders_submitted": 10},
        ),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    store.merge(
        make_snapshot(
            instance_id="other-prod-01",
            application="Other",
            counters={"orders_submitted": 99},
        ),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    engine = _engine(store)
    request = MetricsQueryRequest.model_validate(
        {
            "time_range": QueryTimeRange(
                from_utc=BASE_TIME,
                to_utc=BASE_TIME + timedelta(minutes=5),
            ),
            "filters": {"application": "Magic"},
            "metrics": ["orders"],
        }
    )

    response = engine._execute_sync(request, now=NOW)

    assert response.totals["orders"] == 10
