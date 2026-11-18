"""FR-NLQ-030: suggested questions offered with conversational replies."""

from __future__ import annotations

from telemetry_backend.nl.render.replies import suggested_questions


def test_FR_NLQ_030_suggestions_cover_six_intents_in_order() -> None:
    assert suggested_questions() == [
        "How is Magic doing today?",
        "Why are orders rejecting?",
        "Is Magic slow right now?",
        "Any alerts open for Magic?",
        "Are the FIX sessions up?",
        "Is telemetry actually working?",
    ]
