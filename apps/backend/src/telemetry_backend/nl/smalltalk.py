"""Deterministic small-talk replies that skip the LLM (FR-NLQ-030).

Only whole-message pleasantries match, so "hi, why are orders rejecting?" still goes
through the rule matcher.
"""

from __future__ import annotations

import re
from typing import Literal

SmallTalkKind = Literal["greeting", "thanks", "help"]

_TRAILING_PUNCTUATION = re.compile(r"[\s!.?,]+$")

_PATTERNS: tuple[tuple[SmallTalkKind, re.Pattern[str]], ...] = (
    (
        "greeting",
        re.compile(
            r"^(hi|hello|hey|hiya|yo|good (morning|afternoon|evening))"
            r"( there| bot| team)?$"
        ),
    ),
    (
        "thanks",
        re.compile(r"^(thanks|thank you|thx|ty|cheers)( a lot| so much| very much)?$"),
    ),
    (
        "help",
        re.compile(
            r"^(help|menu|commands|what can you do|what do you do|"
            r"how do i use (this|you)|who are you|what are you|"
            r"what can i ask( you)?)$"
        ),
    ),
)


def match_small_talk(question: str) -> SmallTalkKind | None:
    text = _TRAILING_PUNCTUATION.sub("", question.strip().lower())
    for kind, pattern in _PATTERNS:
        if pattern.match(text):
            return kind
    return None
