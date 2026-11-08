"""UBS-143: `reject_reason_trend` NL intent over UBS-27 (FR-QRY-040, FR-NLQ-003).

"Which reject reasons are increasing?" routes through the rule matcher (no LLM) and is
answered from `RejectReasonTrendService`, with every number taken from its payload.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.nl.catalogue import INTENT_DEFINITIONS, SUPPORTED_INTENTS
from telemetry_backend.nl.llm.mock import MockLlmSlotFiller
from telemetry_backend.nl.rule_matcher import HIGH_CONFIDENCE, match_rules
from telemetry_backend.nl.service import NlQueryOutcome, NlQueryService
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.nl_query import NlQueryContext, NlQueryResponse

from tests.unit.backend.nl.anti_fabrication import assert_answer_numbers_in_data
from tests.unit.backend.services.query_fixtures import make_snapshot

# Aligned to the 10s canonical bucket, so a 5m window has a complete history.
NOW = datetime.now(UTC).replace(microsecond=0)
NOW -= timedelta(seconds=NOW.second % 10)
WINDOW = timedelta(minutes=5)
QUESTION = "Which reject reasons are increasing in the last 5 minutes?"

_CONTEXT = NlQueryContext()
_CONFIG = NlConfig(enabled=True, llm=LlmConfig(provider="mock"))


class _ExplodingLlm(MockLlmSlotFiller):
    """FR-NLQ-006: a high-confidence rule match must never reach the model."""

    async def fill_slots(self, *args: object, **kwargs: object) -> object:  # type: ignore[override]
        raise AssertionError("LLM must be skipped for a rule match")


def _service(
    previous: dict[str, int],
    current: dict[str, int],
    *,
    with_history: bool = True,
) -> NlQueryService:
    store = MetricStore(StreamProcessorConfig())
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
    return NlQueryService(
        config=_CONFIG,
        query_engine=engine,
        alert_store=AlertStore(),
        llm=_ExplodingLlm({}),
        max_range_seconds=21_600,
    )


def _ask(
    service: NlQueryService,
    question: str = QUESTION,
    *,
    audience: str = "technical",
) -> NlQueryResponse:
    outcome: NlQueryOutcome = asyncio.run(
        service.interpret_and_query(
            question,
            context=NlQueryContext(audience=audience),  # type: ignore[arg-type]
            now=NOW,
        )
    )
    assert outcome.kind == "answer"
    return outcome.answer  # type: ignore[return-value]


# --- catalogue (FR-NLQ-003, FR-NLQ-004) -------------------------------------------


def test_catalogue_defines_reject_reason_trend_intent() -> None:
    assert "reject_reason_trend" in SUPPORTED_INTENTS
    definition = INTENT_DEFINITIONS["reject_reason_trend"]
    assert definition.required_slots == ()
    assert "timeRange" in definition.optional_slots
    assert definition.group_by == ("rejectReason",)
    assert not definition.series


# --- rule matcher (FR-NLQ-006) ----------------------------------------------------


@pytest.mark.parametrize(
    "question",
    [
        "Which reject reasons are increasing?",
        "Which reject reasons are going up?",
        "which reject reasons are increasing over the last hour",
        "What's driving rejects up?",
        "Are any reject reasons rising right now?",
        "Show emerging reject reasons",
    ],
)
def test_rule_matcher_routes_question_to_intent(question: str) -> None:
    match = match_rules(
        question,
        context=_CONTEXT,
        config=_CONFIG,
        now=NOW,
        max_range_seconds=21_600,
    )
    assert match is not None
    assert match.intent == "reject_reason_trend"
    assert match.confidence >= HIGH_CONFIDENCE


@pytest.mark.parametrize(
    ("question", "intent"),
    [
        ("Why are orders rejecting?", "rejection_summary"),
        ("Show rejects over the last hour", "trend"),
        ("Are rejects worse than yesterday?", "compare_period"),
    ],
)
def test_neighbouring_intents_are_not_stolen(question: str, intent: str) -> None:
    match = match_rules(
        question,
        context=_CONTEXT,
        config=_CONFIG,
        now=NOW,
        max_range_seconds=21_600,
    )
    assert match is not None
    assert match.intent == intent


# --- service: answer from the trend payload (FR-NLQ-009) --------------------------


def test_answer_lists_increasing_reasons_from_payload() -> None:
    service = _service(
        previous={"OrderExceedsLimit": 10, "UnknownSymbol": 20},
        current={"OrderExceedsLimit": 35, "UnknownSymbol": 20, "StaleQuote": 8},
    )
    response = _ask(service)

    assert response.source == "rule"
    assert response.intent == "reject_reason_trend"
    trends = response.reject_reason_trends
    assert trends is not None
    assert {t.reject_reason for t in trends.increasing} == {
        "OrderExceedsLimit",
        "StaleQuote",
    }
    assert "OrderExceedsLimit" in response.answer
    assert "StaleQuote" in response.answer
    assert "UnknownSymbol" not in response.answer  # steady: not worth a line
    assert "10" in response.answer and "35" in response.answer
    assert "+250%" in response.answer
    assert_answer_numbers_in_data(response.answer, response.data, trends)


def test_chart_rows_carry_the_increasing_reasons() -> None:
    service = _service(
        previous={"OrderExceedsLimit": 10}, current={"OrderExceedsLimit": 35}
    )
    response = _ask(service)
    assert [(r.name, r.value) for r in response.chart_rows] == [
        ("OrderExceedsLimit", 35)
    ]


def test_executive_answer_is_plain_language_and_passes_checker() -> None:
    service = _service(
        previous={"OrderExceedsLimit": 10}, current={"OrderExceedsLimit": 35}
    )
    response = _ask(service, audience="executive")
    assert "OrderExceedsLimit" in response.answer
    assert "magic-prod-01" not in response.answer
    assert "alert-" not in response.answer
    assert response.chart_rows
    assert response.reject_reason_trends is not None
    assert_answer_numbers_in_data(
        response.answer, response.data, response.reject_reason_trends
    )


def test_nothing_increasing_says_so_with_payload_numbers() -> None:
    service = _service(
        previous={"OrderExceedsLimit": 20}, current={"OrderExceedsLimit": 20}
    )
    response = _ask(service)
    assert response.reject_reason_trends is not None
    assert response.reject_reason_trends.increasing == []
    assert "No reject reason is increasing" in response.answer
    assert_answer_numbers_in_data(
        response.answer, response.data, response.reject_reason_trends
    )


def test_incomplete_history_is_stated_not_reported_as_no_trend() -> None:
    service = _service(
        previous={}, current={"OrderExceedsLimit": 35}, with_history=False
    )
    response = _ask(service)
    trends = response.reject_reason_trends
    assert trends is not None and not trends.previous_window_complete
    assert "enough history" in response.answer
    assert "No reject reason is increasing" not in response.answer
    assert any("does not yet cover" in c for c in response.caveats)


def test_interpreted_query_is_replayable_and_scoped() -> None:
    service = _service(
        previous={"OrderExceedsLimit": 10}, current={"OrderExceedsLimit": 35}
    )
    response = _ask(service)
    interpreted = response.interpreted_query
    assert interpreted.intent == "reject_reason_trend"
    assert interpreted.time_range.last == "5m"
    assert interpreted.group_by == ["rejectReason"]
    assert interpreted.filters["application"] == "Magic"
    assert response.reject_reason_trends is not None
    assert response.reject_reason_trends.window == "5m"


def test_reason_names_are_escaped() -> None:
    service = _service(previous={"<b>x</b>": 10}, current={"<b>x</b>": 35})
    response = _ask(service)
    assert "<b>" not in response.answer
    assert "&lt;b&gt;x&lt;/b&gt;" in response.answer
