from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern

_DIGIT_RUN = re.compile(r"\d+")
_QUOTED = re.compile(r'"[^"]*"')
_LONG_TOKEN = re.compile(r"[A-Za-z0-9]{12,}")
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class RejectPattern:
    label: str
    pattern: Pattern[str]


def compile_reject_patterns(
    patterns: list[tuple[str, str]],
) -> list[RejectPattern]:
    return [
        RejectPattern(label=label, pattern=re.compile(regex))
        for label, regex in patterns
    ]


def normalize_reject_text(raw: str) -> str:
    """Steps 1–2 of FR-PRS-022 (matching input only, not emitted)."""
    text = raw.strip().lower()
    text = _WHITESPACE.sub(" ", text)
    text = _QUOTED.sub("*", text)
    text = _LONG_TOKEN.sub("*", text)
    text = _DIGIT_RUN.sub("#", text)
    return text


def match_reject_label(
    raw_text: str | None,
    patterns: list[RejectPattern],
    *,
    max_labels: int = 50,
    seen_labels: set[str] | None = None,
) -> tuple[str | None, bool]:
    """Return (label, is_unclassified).

    On no match returns (None, True) — caller increments unclassified_reject_text.
    On cardinality overflow returns ('__other__', False).
    """
    if raw_text is None or raw_text.strip() == "":
        return None, False

    normalized = normalize_reject_text(raw_text)
    for rule in patterns:
        if rule.pattern.search(normalized):
            label = rule.label
            if seen_labels is not None:
                if label not in seen_labels:
                    if len(seen_labels) >= max_labels:
                        return "__other__", False
                    seen_labels.add(label)
            return label, False
    return None, True
