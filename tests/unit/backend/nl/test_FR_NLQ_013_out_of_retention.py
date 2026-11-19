"""FR-NLQ-011/013: a time range that is entirely outside retention.

"Yesterday" resolves to the previous local day, which the 6-hour in-memory
store (ADR 0005) no longer holds by mid-morning.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.nl.llm.mock import MockLlmSlotFiller
from telemetry_backend.nl.service import NlQueryOutcome, NlQueryService
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.nl_query import NlQueryContext

from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot


def _service() -> NlQueryService:
    store = MetricStore(StreamProcessorConfig())
    # Baseline window (the 30m before the last 30m): 5% rejects.
    store.merge(
        make_snapshot(
            counters={
                "orders_submitted": 100,
                "orders_acked": 95,
                "orders_rejected": 5,
            },
            bucket_start=BASE_TIME - timedelta(minutes=40),
        ),
        canonical_start=BASE_TIME - timedelta(minutes=40),
        now=NOW,
    )
    # Recent window: 10% rejects.
    store.merge(
        make_snapshot(
            counters={
                "orders_submitted": 100,
                "orders_acked": 90,
                "orders_rejected": 10,
            }
        ),
        canonical_start=BASE_TIME,
        now=NOW,
    )
    processor = StreamProcessor(StreamProcessorConfig(), store=store)
    engine = QueryEngine(
        store, stream_processor=processor, agent_registry=AgentRegistry()
    )
    return NlQueryService(
        config=NlConfig(enabled=True, llm=LlmConfig(provider="mock")),
        query_engine=engine,
        alert_store=AlertStore(),
        llm=MockLlmSlotFiller({}),
        max_range_seconds=21_600,
    )


def _ask(question: str) -> NlQueryOutcome:
    return asyncio.run(
        _service().interpret_and_query(
            question, context=NlQueryContext(default_application="Magic"), now=NOW
        )
    )


def test_FR_NLQ_013_worse_than_yesterday_compares_recent_windows() -> None:
    outcome = _ask("Are rejects worse than yesterday?")

    assert outcome.kind == "answer"
    response = outcome.answer  # type: ignore[union-attr]
    assert response.intent == "compare_period"
    assert response.interpreted_query.time_range.last == "30m"
    assert any("outside the retention window" in c for c in response.caveats)
    assert "higher than the previous period" in response.answer


def test_FR_NLQ_011_other_questions_about_yesterday_get_a_readable_reply() -> None:
    outcome = _ask("Why were orders rejecting yesterday?")

    assert outcome.kind == "clarification"
    details = outcome.answer.details  # type: ignore[union-attr]
    assert any("outside the retention window" in d for d in details)
    assert not any("fromUtc is not before toUtc" in d for d in details)
