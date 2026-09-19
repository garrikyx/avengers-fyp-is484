"""FR-PRS-025/026 timestamp tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from telemetry_agent.parser.fix.timestamps import parse_fix_timestamp


def test_FR_PRS_025_parses_fix_timestamp_utc() -> None:
    wall = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    result = parse_fix_timestamp("20260101-10:00:00.123", wall=wall)
    assert result.bad_timestamp is False
    assert result.time_source == "fix"
    assert result.event_time == datetime(2026, 1, 1, 10, 0, 0, 123000, tzinfo=UTC)


def test_FR_PRS_025_bad_timestamp_falls_back_to_log() -> None:
    wall = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    result = parse_fix_timestamp("not-a-ts", wall=wall)
    assert result.bad_timestamp is True
    assert result.time_source == "log"
    assert result.event_time == wall


def test_FR_PRS_026_clock_skew_uses_agent_clock() -> None:
    wall = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    result = parse_fix_timestamp(
        "20260101-09:00:00",
        wall=wall,
        max_skew=timedelta(minutes=5),
    )
    assert result.clock_skew is True
    assert result.time_source == "agent"
    assert result.event_time == wall
