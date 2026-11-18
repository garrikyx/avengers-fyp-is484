"""FR-QRY-034: queries resolve dimensions against what the agent publishes.

The snapshot comes from the real agent path (`MetricsAggregator` ->
`build_snapshot`), so its series carry wire names (`rejectReason`, `instanceId`,
`session`). Test fixtures that seed the store by hand cannot catch a mismatch.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.publishing.snapshot_bridge import build_snapshot
from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.metrics_query import (
    MetricsQueryRequest,
    MetricsQueryResponse,
    QueryTimeRange,
)
from telemetry_shared.models.parsed_message import ExecutionReportEvent

_INSTANCE = "magic-prod-01"
_now = datetime.now(UTC)
_T0 = _now.replace(microsecond=0) - timedelta(seconds=int(_now.timestamp()) % 10)
_BUCKET_START = _T0 - timedelta(seconds=10)

# (symbol, reject reason, count)
_REJECTS = (
    ("AAPL", "OrderExceedsLimit", 3),
    ("AAPL", "UnknownSymbol", 1),
    ("MSFT", "UnknownSymbol", 2),
)


def _engine() -> QueryEngine:
    aggregator = MetricsAggregator(
        config=AggregatorConfig(bucket_seconds=1, metric_dimensions=COUNTER_DIMENSIONS),
        clock=lambda: _T0.timestamp(),
    )
    n = 0
    for symbol, reason, count in _REJECTS:
        for _ in range(count):
            event = ExecutionReportEvent(
                event_time_utc=_BUCKET_START + timedelta(seconds=n % 10),
                instance_id=_INSTANCE,
                session_id="MAGIC->EXCH1",
                cl_ord_id_hash=f"c{n}",
                order_id_hash=f"o{n}",
                exec_id_hash=f"e{n}",
                exec_type="Rejected",
                ord_status="Rejected",
                symbol=symbol,
                side="buy",
                reject_reason_code=reason,
            )
            aggregator.ingest_counters(event, derive_counters(event))
            n += 1

    snapshot = build_snapshot(
        aggregator,
        int(_BUCKET_START.timestamp()),
        10,
        agent_id="agent-a",
        application="Magic",
        instance_id=_INSTANCE,
    )
    store = MetricStore(StreamProcessorConfig())
    store.merge(snapshot, canonical_start=_BUCKET_START, now=_T0)
    processor = StreamProcessor(StreamProcessorConfig(), store=store)
    return QueryEngine(
        store, stream_processor=processor, agent_registry=AgentRegistry()
    )


def _query(
    group_by: list[str], filters: dict[str, str] | None = None
) -> MetricsQueryResponse:
    request = MetricsQueryRequest.model_validate(
        {
            "time_range": QueryTimeRange(from_utc=_BUCKET_START, to_utc=_T0),
            "filters": {"instanceId": _INSTANCE, **(filters or {})},
            "metrics": ["rejections"],
            "group_by": group_by,
        }
    )
    return _engine()._execute_sync(request, now=_T0)


def _by(response: MetricsQueryResponse, dim: str) -> dict[str, int | float]:
    # Series without `dim` (e.g. messages_total) group as "unspecified" with no
    # reject counter.
    return {
        g.dimensions[dim]: g.counters["rejections"]
        for g in response.groups
        if "rejections" in g.counters
    }


def test_FR_QRY_034_group_by_reject_reason_returns_real_reasons() -> None:
    response = _query(["rejectReason"])

    assert _by(response, "rejectReason") == {"OrderExceedsLimit": 3, "UnknownSymbol": 3}


def test_FR_QRY_034_group_by_instance_returns_instance_id() -> None:
    response = _query(["instanceId"])

    assert _by(response, "instanceId") == {_INSTANCE: 6}


def test_symbol_filter_applies_to_an_ungrouped_dimension() -> None:
    response = _query(["rejectReason"], filters={"symbol": "AAPL"})

    assert _by(response, "rejectReason") == {"OrderExceedsLimit": 3, "UnknownSymbol": 1}
    assert response.totals["rejections"] == 4


def test_symbol_filter_without_a_match_returns_no_rejects() -> None:
    response = _query(["rejectReason"], filters={"symbol": "GOOG"})

    assert _by(response, "rejectReason") == {}


def test_FR_QRY_034_snake_case_group_by_is_accepted() -> None:
    response = _query(["reject_reason"])

    assert _by(response, "rejectReason") == {"OrderExceedsLimit": 3, "UnknownSymbol": 3}
