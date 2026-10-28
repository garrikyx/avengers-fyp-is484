"""LLM fallback behaviour (UBS-98)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.nl.llm.mock import MockLlmSlotFiller
from telemetry_backend.nl.llm.protocol import (
    NO_INTENT,
    LlmSlotResult,
    LlmUnavailableError,
)
from telemetry_backend.nl.render.replies import WEAK_RULE_MATCH_CAVEAT
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


class _UnavailableLlm(MockLlmSlotFiller):
    async def fill_slots(
        self, question: str, *, catalogue_summary: str, schema_json: str
    ):
        del question, catalogue_summary, schema_json
        raise LlmUnavailableError("connection refused")


class _ForbiddenLlm(MockLlmSlotFiller):
    async def fill_slots(
        self, question: str, *, catalogue_summary: str, schema_json: str
    ):
        raise AssertionError("small talk must not reach the LLM")


def _service(llm: MockLlmSlotFiller) -> NlQueryService:
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
    assert outcome.answer.reason == "llm_unavailable"  # type: ignore[union-attr]
    assert outcome.answer.suggested_questions  # type: ignore[union-attr]


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


def test_llm_placeholder_metrics_still_answers() -> None:
    llm = MockLlmSlotFiller(
        {
            "anything firing on magic": LlmSlotResult(
                intent="alert_status",
                filters={"application": "Magic"},
                metrics=["metric"],
                group_by=["dimension"],
                series=True,
            )
        }
    )
    service = _service(llm)
    outcome = asyncio.run(
        service.interpret_and_query(
            "Is anything firing on Magic that I should worry about right now?",
            context=NlQueryContext(),
            now=NOW,
        )
    )
    assert outcome.kind == "answer"
    assert outcome.answer.source == "llm"  # type: ignore[union-attr]
    assert outcome.answer.intent == "alert_status"  # type: ignore[union-attr]


def test_llm_applies_time_from_question_when_slots_omit_range() -> None:
    llm = MockLlmSlotFiller(
        {
            "abnormal response times in the last 15 minutes": LlmSlotResult(
                intent="latency_summary",
                time_range=None,
            )
        }
    )
    service = _service(llm)
    outcome = asyncio.run(
        service.interpret_and_query(
            "Has Magic been seeing abnormal response times in the last 15 minutes?",
            context=NlQueryContext(),
            now=NOW,
        )
    )
    assert outcome.kind == "answer"
    assert outcome.answer.source == "llm"  # type: ignore[union-attr]
    assert outcome.answer.interpreted_query.time_range.last == "15m"  # type: ignore[union-attr]


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
    assert "supported telemetry intent" in outcome.answer.message  # type: ignore[union-attr]


def _ask(service: NlQueryService, question: str):  # type: ignore[no-untyped-def]
    return asyncio.run(
        service.interpret_and_query(question, context=NlQueryContext(), now=NOW)
    )


def test_FR_NLQ_021_timeout_falls_back_to_weak_rule_match() -> None:
    outcome = _ask(_service(_TimeoutLlm()), "is it slow")
    assert outcome.kind == "answer"
    assert outcome.answer.source == "rule"  # type: ignore[union-attr]
    assert outcome.answer.intent == "latency_summary"  # type: ignore[union-attr]
    assert WEAK_RULE_MATCH_CAVEAT in outcome.answer.caveats  # type: ignore[union-attr]


def test_FR_NLQ_021_unreachable_llm_without_rule_match_is_friendly() -> None:
    outcome = _ask(_service(_UnavailableLlm()), "tell me something about xyz")
    assert outcome.kind == "clarification"
    assert outcome.answer.reason == "llm_unavailable"  # type: ignore[union-attr]
    assert outcome.answer.suggested_questions  # type: ignore[union-attr]


def test_FR_NLQ_030_guarded_llm_reply_is_returned() -> None:
    llm = MockLlmSlotFiller(
        {
            "weather": LlmSlotResult(
                intent=NO_INTENT,
                reply="I can't help with the weather, but I can tell you how Magic "
                "is doing.",
            )
        }
    )
    outcome = _ask(_service(llm), "what's the weather like")
    assert outcome.kind == "clarification"
    assert outcome.answer.reason == "out_of_scope"  # type: ignore[union-attr]
    assert "weather" in outcome.answer.message  # type: ignore[union-attr]


def test_FR_NLQ_030_llm_reply_with_numbers_uses_template() -> None:
    llm = MockLlmSlotFiller(
        {"weather": LlmSlotResult(intent=NO_INTENT, reply="Magic had 42 rejects.")}
    )
    outcome = _ask(_service(llm), "what's the weather like")
    assert outcome.answer.reason == "out_of_scope"  # type: ignore[union-attr]
    assert "42" not in outcome.answer.message  # type: ignore[union-attr]
    assert "only answer questions" in outcome.answer.message  # type: ignore[union-attr]


def test_FR_NLQ_030_small_talk_skips_the_llm() -> None:
    service = _service(_ForbiddenLlm())
    greeting = _ask(service, "Hi!")
    assert greeting.answer.reason == "greeting"  # type: ignore[union-attr]
    help_reply = _ask(service, "what can you do?")
    assert help_reply.answer.reason == "help"  # type: ignore[union-attr]
    assert help_reply.answer.suggested_questions  # type: ignore[union-attr]
