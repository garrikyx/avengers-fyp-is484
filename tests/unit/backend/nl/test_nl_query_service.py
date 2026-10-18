"""End-to-end NL service tests."""

from __future__ import annotations

import asyncio

from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.nl.compiler import to_metrics_query
from telemetry_backend.nl.llm.mock import MockLlmSlotFiller
from telemetry_backend.nl.service import NlQueryService
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.nl_query import NlQueryContext

from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot


def _service() -> NlQueryService:
    store = MetricStore(StreamProcessorConfig())
    store.merge(
        make_snapshot(
            counters={"orders_submitted": 100, "orders_rejected": 10},
        ),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    processor = StreamProcessor(StreamProcessorConfig(), store=store)
    engine = QueryEngine(
        store,
        stream_processor=processor,
        agent_registry=AgentRegistry(),
    )
    config = NlConfig(enabled=True, llm=LlmConfig(provider="mock"))
    return NlQueryService(
        config=config,
        query_engine=engine,
        alert_store=AlertStore(),
        llm=MockLlmSlotFiller({}),
        max_range_seconds=21_600,
    )


def test_rule_path_skips_llm_and_matches_direct_query() -> None:
    service = _service()
    outcome = asyncio.run(
        service.interpret_and_query(
            "Why are orders rejecting in the last 30 minutes?",
            context=NlQueryContext(default_application="Magic"),
            now=NOW,
        )
    )
    assert outcome.kind == "answer"
    response = outcome.answer  # type: ignore[union-attr]
    assert response.source == "rule"
    assert response.intent == "rejection_summary"

    direct = asyncio.run(
        service._engine.query(  # noqa: SLF001
            to_metrics_query(response.interpreted_query),
            now=NOW,
        )
    )
    assert response.data.totals.get("orders_rejected") == direct.totals.get(
        "orders_rejected"
    )
