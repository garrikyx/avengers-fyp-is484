"""Time expression parsing for NL queries."""

from __future__ import annotations

from datetime import UTC, datetime

from telemetry_backend.nl.time import parse_time_expression

NOW = datetime(2026, 6, 12, 4, 0, tzinfo=UTC)


def test_last_30_minutes_is_explicit() -> None:
    result = parse_time_expression(
        "reject rate in the last 30 minutes",
        now=NOW,
        timezone_name="Asia/Singapore",
        default_last="30m",
        max_range_seconds=21_600,
    )
    assert result.explicit is True
    assert result.time_range.last == "30m"


def test_missing_time_uses_default_with_caveat() -> None:
    result = parse_time_expression(
        "why rejecting",
        now=NOW,
        timezone_name="Asia/Singapore",
        default_last="30m",
        max_range_seconds=21_600,
    )
    assert result.explicit is False
    assert result.time_range.last == "30m"
    assert result.caveats
