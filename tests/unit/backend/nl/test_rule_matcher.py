"""Rule-first intent matcher tests (UBS-97)."""

from __future__ import annotations

from datetime import UTC, datetime

from telemetry_backend.config import NlConfig
from telemetry_backend.nl.rule_matcher import HIGH_CONFIDENCE, match_rules
from telemetry_shared.models.nl_query import NlQueryContext

NOW = datetime(2026, 6, 12, 4, 0, tzinfo=UTC)
CONTEXT = NlQueryContext()
CONFIG = NlConfig(enabled=True)


def test_rejection_summary_matches_common_phrasing() -> None:
    match = match_rules(
        "Why are Magic orders rejecting in the last 30 minutes?",
        context=CONTEXT,
        config=CONFIG,
        now=NOW,
        max_range_seconds=21_600,
    )
    assert match is not None
    assert match.intent == "rejection_summary"
    assert match.confidence >= HIGH_CONFIDENCE


def test_each_intent_has_a_matching_phrase() -> None:
    samples = {
        "rejection_summary": "show reject rate",
        "order_flow_summary": "how is magic doing today",
        "latency_summary": "is magic slow right now",
        "alert_status": "any alerts open",
        "session_status": "are the fix sessions up",
        "symbol_drilldown": "what's rejecting on ABC",
        "agent_health": "is telemetry actually working",
        "parse_health": "failing to parse anything",
        "compare_period": "rejects worse than yesterday",
        "trend": "show rejects over the last hour",
    }
    for intent, question in samples.items():
        match = match_rules(
            question,
            context=CONTEXT,
            config=CONFIG,
            now=NOW,
            max_range_seconds=21_600,
        )
        assert match is not None, intent
        assert match.intent == intent, question
