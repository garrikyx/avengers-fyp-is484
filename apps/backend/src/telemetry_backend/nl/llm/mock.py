"""Deterministic LLM mock for tests (FR-TST-009)."""

from __future__ import annotations

from telemetry_shared.models.metrics_query import QueryTimeRange

from telemetry_backend.nl.llm.protocol import (
    LlmSlotFiller,
    LlmSlotFillError,
    LlmSlotResult,
)


class MockLlmSlotFiller(LlmSlotFiller):
    def __init__(self, responses: dict[str, LlmSlotResult] | None = None) -> None:
        self._responses = responses or {}

    async def fill_slots(
        self,
        question: str,
        *,
        catalogue_summary: str,
        schema_json: str,
    ) -> LlmSlotResult:
        del catalogue_summary, schema_json
        normalized = question.strip().lower()
        for key, result in self._responses.items():
            if key.lower() in normalized:
                return result
        raise LlmSlotFillError("no mock LLM mapping for question")


def default_mock_responses() -> dict[str, LlmSlotResult]:
    return {
        "unusual phrasing about latency": LlmSlotResult(
            intent="latency_summary",
            time_range=QueryTimeRange(last="15m"),
            filters={"application": "Magic"},
        ),
    }
