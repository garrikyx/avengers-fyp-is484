"""LLM fallback behaviour (UBS-98)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.nl.llm.mock import MockLlmSlotFiller
from telemetry_backend.nl.llm.protocol import LlmSlotResult
from telemetry_backend.nl.service import NlQueryService
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.metrics_query import QueryTimeRange
from telemetry_shared.models.nl_query import NlQueryContext

NOW = datetime(2026, 6, 12, 4, 0, tzinfo=UTC)


class _TimeoutLlm(MockLlmSlotFiller):
    async def fill_slots(
        self, question: str, *, catalogue_summary: str, schema_json: str
    ):
        del question, catalogue_summary, schema_json
        await asyncio.sleep(5)
        raise AssertionError("should have timed out")


def _service(llm: MockLlmSlotFiller | _TimeoutLlm) -> NlQueryService:
    processor = StreamProcessor(StreamProcessorConfig(), store=MetricStore())
    engine = QueryEngine(
        processor.store,
        stream_processor=processor,
        agent_registry=AgentRegistry(),
    )
    config = NlConfig(
        enabled=True,
        llm=LlmConfig(provider="mock", timeout_seconds=0.05),
    )
    return NlQueryService(
        config=config,
        query_engine=engine,
        alert_store=AlertStore(),
        llm=llm,
        max_range_seconds=21_600,
    )


def test_llm_timeout_returns_clarification() -> None:
    service = _service(_TimeoutLlm())
    outcome = asyncio.run(
        service.interpret_and_query(
            "something that does not match rules at all xyz",
            context=NlQueryContext(),
            now=NOW,
        )
    )
    assert outcome.kind == "clarification"


def test_mock_llm_fills_slots_for_unknown_phrasing() -> None:
    llm = MockLlmSlotFiller(
        {
            "something that does not match rules at all xyz": LlmSlotResult(
                intent="latency_summary",
                time_range=QueryTimeRange(last="15m"),
            )
        }
    )
    service = _service(llm)
    outcome = asyncio.run(
        service.interpret_and_query(
            "something that does not match rules at all xyz",
            context=NlQueryContext(),
            now=NOW,
        )
    )
    assert outcome.kind == "answer"
    assert outcome.answer.intent == "latency_summary"  # type: ignore[union-attr]
    assert outcome.answer.source == "llm"  # type: ignore[union-attr]


def test_mock_llm_missing_mapping_raises_and_clarifies() -> None:
    service = _service(MockLlmSlotFiller({}))
    outcome = asyncio.run(
        service.interpret_and_query(
            "no rule and no llm mapping",
            context=NlQueryContext(),
            now=NOW,
        )
    )
    assert outcome.kind == "clarification"
