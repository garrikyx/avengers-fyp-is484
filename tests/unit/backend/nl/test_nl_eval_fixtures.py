"""NL evaluation harness (UBS-101, FR-NLQ-025, FR-TST-007/008)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from telemetry_backend.config import LlmConfig, NlConfig, StreamProcessorConfig
from telemetry_backend.nl.catalogue import INTENT_DEFINITIONS
from telemetry_backend.nl.compiler import merge_interpreted_query
from telemetry_backend.nl.rule_matcher import (
    HIGH_CONFIDENCE,
    match_rules,
    rule_match_to_interpreted,
)
from telemetry_backend.nl.service import NlQueryService
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.nl_query import NlQueryContext

from tests.unit.backend.nl.anti_fabrication import assert_answer_numbers_in_data
from tests.unit.backend.services.query_fixtures import BASE_TIME, NOW, make_snapshot

_FIXTURES_PATH = (
    Path(__file__).resolve().parents[3] / "fixtures" / "nl" / "eval_fixtures.json"
)
_INTENT_THRESHOLD = 0.90
_SLOT_THRESHOLD = 0.80
_NOW = NOW
_MAX_RANGE = 21_600


def _load_fixtures() -> list[dict[str, Any]]:
    return json.loads(_FIXTURES_PATH.read_text())


def _interpret_rule(question: str) -> tuple[str | None, dict[str, Any] | None]:
    context = NlQueryContext()
    config = NlConfig(enabled=True, llm=LlmConfig(provider="mock"))
    match = match_rules(
        question,
        context=context,
        config=config,
        now=_NOW,
        max_range_seconds=_MAX_RANGE,
    )
    if match is None or match.confidence < HIGH_CONFIDENCE:
        return None, None
    payload, _caveats = rule_match_to_interpreted(match)
    interpreted = merge_interpreted_query(
        time_range=payload["time_range"],
        filters=payload["filters"],  # type: ignore[arg-type]
        group_by=payload["group_by"],  # type: ignore[arg-type]
        metrics=payload["metrics"],  # type: ignore[arg-type]
        series=payload["series"],  # type: ignore[arg-type]
        step=payload["step"],  # type: ignore[arg-type]
        percentiles=payload["percentiles"],  # type: ignore[arg-type]
        intent=payload["intent"],  # type: ignore[arg-type]
        context=context,
        config=config,
    )
    return interpreted.intent, interpreted.model_dump(mode="json", by_alias=True)


def _nl_service() -> NlQueryService:
    store = MetricStore(StreamProcessorConfig())
    store.merge(
        make_snapshot(counters={"orders_submitted": 100, "orders_rejected": 10}),
        canonical_start=BASE_TIME,
        now=_NOW,
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
        llm=__import__(
            "telemetry_backend.nl.llm.mock", fromlist=["MockLlmSlotFiller"]
        ).MockLlmSlotFiller({}),
        max_range_seconds=_MAX_RANGE,
    )


def test_nl_eval_fixture_corpus_meets_thresholds() -> None:
    fixtures = _load_fixtures()
    assert len(fixtures) >= 40

    intent_hits = 0
    slot_hits = 0
    rule_cases = 0

    for case in fixtures:
        if case.get("source") != "rule":
            continue
        rule_cases += 1
        intent, interpreted = _interpret_rule(case["question"])
        expected_intent = case["expectedIntent"]
        if intent == expected_intent:
            intent_hits += 1
        if interpreted is not None and intent == expected_intent:
            defn = INTENT_DEFINITIONS[expected_intent]  # type: ignore[index]
            if (
                list(interpreted.get("groupBy") or []) == list(defn.group_by)
                and list(interpreted.get("metrics") or []) == list(defn.metrics)
                and interpreted.get("series") == defn.series
                and interpreted.get("step") == defn.step
            ):
                slot_hits += 1

    intent_rate = intent_hits / rule_cases
    slot_rate = slot_hits / rule_cases
    print(
        f"NL eval: intent={intent_hits}/{rule_cases} ({intent_rate:.1%}), "
        f"slots={slot_hits}/{rule_cases} ({slot_rate:.1%})"
    )
    assert intent_rate >= _INTENT_THRESHOLD, f"intent accuracy {intent_rate:.1%}"
    assert slot_rate >= _SLOT_THRESHOLD, f"slot accuracy {slot_rate:.1%}"


@pytest.mark.parametrize(
    "case_id",
    [c["id"] for c in json.loads(_FIXTURES_PATH.read_text()) if c.get("expectAnswer")],
)
def test_nl_eval_anti_fabrication(case_id: str) -> None:
    fixtures = {c["id"]: c for c in _load_fixtures()}
    case = fixtures[case_id]
    service = _nl_service()
    outcome = asyncio.run(
        service.interpret_and_query(
            case["question"],
            context=NlQueryContext(),
            now=_NOW,
        )
    )
    assert outcome.kind == "answer"
    response = outcome.answer  # type: ignore[union-attr]
    assert_answer_numbers_in_data(response.answer, response.data)
