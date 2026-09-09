"""FR-PRS-022 tag 58 normalisation tests."""

from __future__ import annotations

from telemetry_agent.parser.fix.normalize import (
    compile_reject_patterns,
    match_reject_label,
    normalize_reject_text,
)


def test_FR_PRS_022_normalizes_digits_and_tokens() -> None:
    raw = '  Price 123 exceeds LIMIT for "ABC" symbol  '
    normalized = normalize_reject_text(raw)
    assert "#" in normalized
    assert "price" in normalized


def test_FR_PRS_022_pattern_match() -> None:
    patterns = compile_reject_patterns([("price_exceeds_limit", r"price.*limit")])
    label, unclassified = match_reject_label("Price 999 exceeds limit", patterns)
    assert label == "price_exceeds_limit"
    assert unclassified is False


def test_FR_PRS_022_unclassified_increments_flag() -> None:
    patterns = compile_reject_patterns([("known", r"known pattern")])
    label, unclassified = match_reject_label("totally unknown reason", patterns)
    assert label is None
    assert unclassified is True


def test_FR_PRS_022_cardinality_overflow() -> None:
    seen = {f"label_{i}" for i in range(50)}
    patterns = compile_reject_patterns([("label_new", r"overflow token")])
    label, _ = match_reject_label("overflow token here", patterns, max_labels=50, seen_labels=seen)
    assert label == "__other__"
