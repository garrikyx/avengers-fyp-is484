"""NL answers surface alert callback delivery (UBS-102, FR-NLQ-029)."""

from __future__ import annotations

import asyncio

from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.nl.llm.mock import MockLlmSlotFiller
from telemetry_backend.nl.service import NlQueryService
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.alerts_query import AlertDelivery
from telemetry_shared.models.nl_query import NlQueryContext

from tests.unit.backend.services.alert_fixtures import make_alert_event
from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot


def test_alert_status_answer_includes_callback_delivery() -> None:
    store = MetricStore(StreamProcessorConfig())
    store.merge(
        make_snapshot(counters={"orders_submitted": 1}),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    processor = StreamProcessor(StreamProcessorConfig(), store=store)
    engine = QueryEngine(
        store,
        stream_processor=processor,
        agent_registry=AgentRegistry(),
    )
    alert_store = AlertStore()
    alert_store.merge(
        make_alert_event(alert_id="alert-int-1").model_copy(
            update={
                "callback_delivery": AlertDelivery(
                    status="failed", attempts=3, correlation_id="cb-int"
                )
            }
        )
    )
    service = NlQueryService(
        config=NlConfig(enabled=True, llm=LlmConfig(provider="mock")),
        query_engine=engine,
        alert_store=alert_store,
        llm=MockLlmSlotFiller({}),
        max_range_seconds=21_600,
    )
    outcome = asyncio.run(
        service.interpret_and_query(
            "Any alerts open for Magic?",
            context=NlQueryContext(),
            now=NOW,
        )
    )
    assert outcome.kind == "answer"
    response = outcome.answer  # type: ignore[union-attr]
    assert "failed" in response.answer
    assert response.alert_summaries[0].delivery.attempts == 3
