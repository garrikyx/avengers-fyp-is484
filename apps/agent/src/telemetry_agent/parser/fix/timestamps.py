from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

_FIX_TS = re.compile(
    r"^(\d{4})(\d{2})(\d{2})-(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?$"
)


@dataclass(frozen=True, slots=True)
class TimestampResult:
    event_time: datetime
    time_source: str
    bad_timestamp: bool = False
    clock_skew: bool = False


def parse_fix_timestamp(
    raw: str | None,
    *,
    wall: datetime,
    max_skew: timedelta = timedelta(minutes=5),
) -> TimestampResult:
    """Parse FIX SendingTime/TransactTime as UTC."""
    if raw is None or raw.strip() == "":
        return TimestampResult(event_time=wall, time_source="log")

    match = _FIX_TS.match(raw.strip())
    if match is None:
        return TimestampResult(event_time=wall, time_source="log", bad_timestamp=True)

    year, month, day, hour, minute, second, frac = match.groups()
    micro = 0
    if frac:
        micro = int(frac.ljust(6, "0")[:6])

    try:
        parsed = datetime(
            int(year),
            int(month),
            int(day),
            int(hour),
            int(minute),
            int(second),
            micro,
            tzinfo=UTC,
        )
    except ValueError:
        return TimestampResult(event_time=wall, time_source="log", bad_timestamp=True)

    if wall.tzinfo is None:
        wall = wall.replace(tzinfo=UTC)
    skew = abs(parsed - wall)
    if skew > max_skew:
        return TimestampResult(
            event_time=wall,
            time_source="agent",
            clock_skew=True,
        )
    return TimestampResult(event_time=parsed, time_source="fix")
