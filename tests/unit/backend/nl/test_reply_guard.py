"""Conversational reply guard and small-talk matcher (FR-NLQ-030)."""

from __future__ import annotations

import pytest
from telemetry_backend.nl.reply_guard import MAX_REPLY_CHARS, guard_reply
from telemetry_backend.nl.smalltalk import match_small_talk


@pytest.mark.parametrize(
    "reply",
    [
        None,
        "   ",
        "Magic had 12 rejects today.",
        "See https://evil.example for details.",
        "Click [here](x)",
        "x" * (MAX_REPLY_CHARS + 1),
        "I can help you with the weather forecast for Singapore.",
    ],
)
def test_FR_NLQ_030_guard_rejects_unsafe_replies(reply: str | None) -> None:
    assert guard_reply(reply) is None


def test_FR_NLQ_030_guard_cleans_whitespace() -> None:
    assert (
        guard_reply("  Sorry,\n\tI only cover Magic telemetry.  ")
        == "Sorry, I only cover Magic telemetry."
    )


def test_FR_NLQ_030_guard_accepts_the_configured_application() -> None:
    assert guard_reply("I only cover Orion.", application="Orion") is not None
    assert guard_reply("I only cover Orion.") is None


@pytest.mark.parametrize(
    ("question", "kind"),
    [
        ("hi", "greeting"),
        ("Good morning!", "greeting"),
        ("thanks a lot", "thanks"),
        ("What can you do?", "help"),
        ("help", "help"),
    ],
)
def test_FR_NLQ_030_small_talk_matches(question: str, kind: str) -> None:
    assert match_small_talk(question) == kind


@pytest.mark.parametrize(
    "question",
    ["hi, why are orders rejecting?", "help me find rejects", "is magic slow"],
)
def test_FR_NLQ_030_telemetry_questions_are_not_small_talk(question: str) -> None:
    assert match_small_talk(question) is None
