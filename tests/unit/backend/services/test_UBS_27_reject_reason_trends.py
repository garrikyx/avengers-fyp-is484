"""UBS-27: reject reasons whose occurrence rate rises against the preceding
equal-length window."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.main import create_app
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine, QueryValidationError
from telemetry_backend.services.reject_reason_trends import (
    RejectReasonTrendService,
    classify,
)
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.trends import RejectReasonTrendsRequest

from tests.unit.backend.services.query_fixtures import make_snapshot

# Aligned to the 10s canonical bucket, an hour in, so a 5m window has history.
NOW = datetime.now(UTC).replace(microsecond=0)
NOW -= timedelta(seconds=NOW.second % 10)
WINDOW = timedelta(minutes=5)


def _service(
    previous: dict[str, int], current: dict[str, int], *, with_history: bool = True
) -> RejectReasonTrendService:
    store = MetricStore(StreamProcessorConfig())
    # A quiet bucket at the very start so the store's oldest bucket predates
    # the preceding window (the store can then vouch for it being complete).
    anchor = NOW - 2 * WINDOW - timedelta(seconds=30)
    if with_history:
        store.merge(
            make_snapshot(counters={"orders_submitted": 1}, bucket_start=anchor),
            canonical_start=anchor,
            now=NOW,
        )
    for start, counts in (
        (NOW - 2 * WINDOW + timedelta(seconds=60), previous),
        (NOW - WINDOW + timedelta(seconds=60), current),
    ):
        for reason, count in counts.items():
            store.merge(
                make_snapshot(
                    counters={"orders_rejected": count},
                    dimensions={"session_id": "S", "reject_reason": reason},
                    bucket_start=start,
                ),
                canonical_start=start,
                now=NOW,
            )
    processor = StreamProcessor(StreamProcessorConfig(), store=store)
    engine = QueryEngine(
        processor.store, stream_processor=processor, agent_registry=AgentRegistry()
    )
    return RejectReasonTrendService(engine)


def _analyse(service: RejectReasonTrendService, **overrides: object):
    request = RejectReasonTrendsRequest.model_validate({"window": "5m", **overrides})
    return asyncio.run(service.analyse(request, now=NOW))


def test_a_reason_up_more_than_the_threshold_is_increasing() -> None:
    service = _service(
        previous={"UnknownSymbol": 10, "OrderExceedsLimit": 20},
        current={"UnknownSymbol": 16, "OrderExceedsLimit": 20},
    )

    response = _analyse(service)

    assert response.previous_window_complete
    [trend] = response.increasing
    assert trend.reject_reason == "UnknownSymbol"
    assert (trend.previous_count, trend.current_count) == (10, 16)
    assert trend.change_ratio == pytest.approx(0.6)
    steady = {t.reject_reason: t.trend for t in response.reasons}
    assert steady["OrderExceedsLimit"] == "steady"


def test_a_rise_of_exactly_the_threshold_is_not_a_trend() -> None:
    service = _service(previous={"UnknownSymbol": 10}, current={"UnknownSymbol": 15})
    assert (_analyse(service)).increasing == []  # +50% is not "> 50%"


def test_threshold_is_configurable() -> None:
    service = _service(previous={"UnknownSymbol": 10}, current={"UnknownSymbol": 13})
    assert (_analyse(service)).increasing == []
    [trend] = (_analyse(service, threshold=0.2)).increasing
    assert trend.reject_reason == "UnknownSymbol"


def test_a_reason_absent_before_is_emerging_and_listed_first() -> None:
    service = _service(
        previous={"UnknownSymbol": 10},
        current={"UnknownSymbol": 30, "StaleOrder": 8},
    )

    response = _analyse(service)

    assert [(t.reject_reason, t.trend) for t in response.increasing] == [
        ("StaleOrder", "emerging"),
        ("UnknownSymbol", "increasing"),
    ]
    assert response.increasing[0].change_ratio is None


def test_small_counts_are_not_a_trend() -> None:
    service = _service(previous={"UnknownSymbol": 1}, current={"UnknownSymbol": 4})
    assert (_analyse(service)).increasing == []  # 4 < min_occurrences (5)


def test_falling_reasons_are_reported_as_decreasing() -> None:
    service = _service(previous={"UnknownSymbol": 20}, current={"UnknownSymbol": 5})
    response = _analyse(service)
    assert response.increasing == []
    assert response.reasons[0].trend == "decreasing"


def test_nothing_is_flagged_when_the_preceding_window_is_not_covered() -> None:
    service = _service(previous={}, current={"UnknownSymbol": 50}, with_history=False)

    response = _analyse(service)

    assert not response.previous_window_complete
    assert response.increasing == []
    assert response.caveats


def test_the_boundary_bucket_is_counted_once() -> None:
    service = _service(previous={"UnknownSymbol": 10}, current={"UnknownSymbol": 10})
    # A burst in the first bucket of the current window.
    store = service._engine.store
    start = NOW - WINDOW
    store.merge(
        make_snapshot(
            counters={"orders_rejected": 40},
            dimensions={"session_id": "S", "reject_reason": "UnknownSymbol"},
            bucket_start=start,
        ),
        canonical_start=start,
        now=NOW,
    )

    [trend] = _analyse(service).reasons

    assert (trend.previous_count, trend.current_count) == (10, 50)


@pytest.mark.parametrize("window", ["soon", "0m", "45s"])
def test_a_bad_window_names_the_window_field(window: str) -> None:
    service = _service(previous={}, current={})
    with pytest.raises(QueryValidationError) as exc:
        _analyse(service, window=window)
    assert exc.value.field == "window"


def test_classify_boundaries() -> None:
    assert classify(16, 10, threshold=0.5, min_occurrences=5) == ("increasing", 0.6)
    assert classify(0, 0, threshold=0.5, min_occurrences=5) == ("steady", None)
    assert classify(5, 0, threshold=0.5, min_occurrences=5) == ("emerging", None)
    assert classify(4, 0, threshold=0.5, min_occurrences=5)[0] == "steady"


def test_endpoint_rejects_a_malformed_window() -> None:
    client = TestClient(create_app(enable_heartbeat_monitor=False))
    response = client.post(
        "/telemetry/query/reject-reason-trends", json={"window": "soon"}
    )
    assert response.status_code == 400


def test_endpoint_returns_a_response_for_an_empty_store() -> None:
    client = TestClient(create_app(enable_heartbeat_monitor=False))
    response = client.post(
        "/telemetry/query/reject-reason-trends", json={"window": "5m"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["increasing"] == [] and body["previousWindowComplete"] is False
