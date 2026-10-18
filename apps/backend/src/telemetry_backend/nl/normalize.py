"""Question normalization (FR-NLQ-005)."""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")


def normalize_question(question: str, *, max_chars: int) -> str:
    text = _WHITESPACE.sub(" ", question.strip())
    if len(text) > max_chars:
        return text[:max_chars]
    return text
