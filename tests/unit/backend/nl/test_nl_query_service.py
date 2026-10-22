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
from telemetry_shared.models.alerts_query import AlertDelivery
from telemetry_shared.models.nl_query import NlQueryContext

from tests.unit.backend.services.alert_fixtures import make_alert_event
from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot


def _service(alert_store: AlertStore | None = None) -> NlQueryService:
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
        alert_store=alert_store or AlertStore(),
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


def test_executive_audience_omits_alert_ids_in_prose() -> None:
    service = _service()
    outcome = asyncio.run(
        service.interpret_and_query(
            "Why are orders rejecting in the last 30 minutes?",
            context=NlQueryContext(audience="executive"),
            now=NOW,
        )
    )
    assert outcome.kind == "answer"
    response = outcome.answer  # type: ignore[union-attr]
    assert "alert-" not in response.answer


def test_alert_status_includes_delivery_and_citations() -> None:
    store = MetricStore(StreamProcessorConfig())
    processor = StreamProcessor(StreamProcessorConfig(), store=store)
    engine = QueryEngine(
        store,
        stream_processor=processor,
        agent_registry=AgentRegistry(),
    )
    alerts = AlertStore()
    delivery = AlertDelivery(status="delivered", attempts=1)
    event = make_alert_event(alert_id="alert-nl-1").model_copy(
        update={"callback_delivery": delivery}
    )
    alerts.merge(event)
    service = NlQueryService(
        config=NlConfig(enabled=True, llm=LlmConfig(provider="mock")),
        query_engine=engine,
        alert_store=alerts,
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
    assert "delivered" in response.answer
    assert any(c.type == "alert" for c in response.citations)
    assert response.alert_summaries[0].delivery.status == "delivered"


def test_alert_status_answer_cites_each_active_alert() -> None:
    store = AlertStore()
    store.merge(make_alert_event(alert_id="active-1"))
    store.merge(make_alert_event(alert_id="active-2", instance_id="magic-prod-02"))
    outcome = asyncio.run(
        _service(store).interpret_and_query(
            "Any alerts open for Magic?",
            context=NlQueryContext(default_application="Magic"),
            now=NOW,
        )
    )
    assert outcome.kind == "answer"
    response = outcome.answer  # type: ignore[union-attr]
    assert response.intent == "alert_status"
    cited = {c.alert_id for c in response.citations if c.type == "alert"}
    assert cited == {"active-1", "active-2"}
    assert any(c.type == "metrics_query" for c in response.citations)


def test_non_alert_answer_has_no_alert_citations() -> None:
    store = AlertStore()
    store.merge(make_alert_event(alert_id="active-1"))
    outcome = asyncio.run(
        _service(store).interpret_and_query(
            "Is Magic slow in the last 30 minutes?",
            context=NlQueryContext(default_application="Magic"),
            now=NOW,
        )
    )
    response = outcome.answer  # type: ignore[union-attr]
    assert response.intent == "latency_summary"
    assert not [c for c in response.citations if c.type == "alert"]
