"""UBS-92: multi-replica scatter-gather query merge."""

from __future__ import annotations

from datetime import timedelta

from telemetry_backend.config import QueryConfig, StreamProcessorConfig
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine
from telemetry_backend.services.replica_fanout import ReplicaFanout
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.metrics_query import (
    DataCompleteness,
    EffectiveTimeRange,
    MetricsQueryRequest,
    MetricsQueryResponse,
    QueryInterpretation,
    QueryTimeRange,
)

from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot


def _request() -> MetricsQueryRequest:
    return MetricsQueryRequest.model_validate(
        {
            "time_range": QueryTimeRange(
                from_utc=BASE_TIME,
                to_utc=BASE_TIME + timedelta(minutes=5),
            ),
            "filters": {"instanceId": "magic-prod-01"},
            "metrics": ["orders"],
        }
    )


class _StubPeerClient:
    def __init__(self, peer_response: MetricsQueryResponse | None) -> None:
        self._peer_response = peer_response

    async def post_query(
        self, peer: str, request: MetricsQueryRequest
    ) -> MetricsQueryResponse | None:
        return self._peer_response


def test_UBS_92_fanout_merges_peer_totals() -> None:
    import asyncio
    processor = StreamProcessor(StreamProcessorConfig(), store=MetricStore())
    processor.store.merge(
        make_snapshot(counters={"orders_submitted": 10}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    local_engine = QueryEngine(processor.store, stream_processor=processor)

    peer_response = MetricsQueryResponse(
        query_id="q-peer",
        evaluated_at_utc=NOW,
        effective_time_range=EffectiveTimeRange(
            from_utc=BASE_TIME,
            to_utc=BASE_TIME + timedelta(minutes=5),
        ),
        interpretation=QueryInterpretation(
            metrics=["orders_submitted"],
            group_by=[],
            filters={"instanceId": "magic-prod-01"},
        ),
        totals={"orders": 15},
        data_completeness=DataCompleteness(
            agents_expected=1,
            agents_reporting=1,
        ),
    )

    fanout = ReplicaFanout(
        local=local_engine,
        config=QueryConfig(
            query_mode="fanout",
            replica_registry=("http://peer-1",),
        ),
        client=_StubPeerClient(peer_response),
    )

    merged = asyncio.run(fanout.query(_request(), now=NOW))

    assert merged.totals["orders"] == 25


def test_UBS_92_peer_failure_marks_partial() -> None:
    import asyncio
    processor = StreamProcessor(StreamProcessorConfig(), store=MetricStore())
    processor.store.merge(
        make_snapshot(counters={"orders_submitted": 4}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    local_engine = QueryEngine(processor.store, stream_processor=processor)

    fanout = ReplicaFanout(
        local=local_engine,
        config=QueryConfig(
            query_mode="fanout",
            replica_registry=("http://peer-down",),
            fanout_timeout_seconds=0.01,
        ),
        client=_StubPeerClient(None),
    )

    merged = asyncio.run(fanout.query(_request(), now=NOW))

    assert merged.totals["orders"] == 4
    assert merged.data_completeness.confidence == "partial"
    assert merged.data_completeness.failed_peers == ["http://peer-down"]
