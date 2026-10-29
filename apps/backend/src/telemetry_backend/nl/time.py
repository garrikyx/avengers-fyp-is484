"""Time expression parsing for NL queries (FR-NLQ-011–014)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from telemetry_shared.models.metrics_query import QueryTimeRange

_RELATIVE_RE = re.compile(r"^(\d+)(s|m|h)$")
_LAST_N_RE = re.compile(
    r"\blast\s+(\d+)\s*(minute|minutes|min|mins|hour|hours|hr|hrs|h|m)\b",
    re.IGNORECASE,
)
_SINCE_RE = re.compile(r"\bsince\s+(\d{1,2}):(\d{2})\b", re.IGNORECASE)
_BETWEEN_RE = re.compile(
    r"\bbetween\s+(.+?)\s+and\s+(.+?)(?:\?|$|\.)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class TimeParseResult:
    time_range: QueryTimeRange
    explicit: bool
    caveats: tuple[str, ...] = ()


def _relative_from_amount(amount: int, unit: str) -> str:
    unit = unit.lower()
    if unit in {"minute", "minutes", "min", "mins", "m"}:
        return f"{amount}m"
    if unit in {"hour", "hours", "hr", "hrs", "h"}:
        return f"{amount}h"
    return f"{amount}m"


def _local_midnight(now: datetime, tz: ZoneInfo) -> datetime:
    local = now.astimezone(tz)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(UTC)


def _this_morning_start(now: datetime, tz: ZoneInfo) -> datetime:
    local = now.astimezone(tz)
    start = local.replace(hour=6, minute=0, second=0, microsecond=0)
    if local.hour < 6:
        start -= timedelta(days=1)
    return start.astimezone(UTC)


def parse_time_expression(
    text: str,
    *,
    now: datetime,
    timezone_name: str,
    default_last: str,
    max_range_seconds: int,
) -> TimeParseResult:
    lowered = text.lower()
    tz = ZoneInfo(timezone_name)

    match = _LAST_N_RE.search(text)
    if match:
        last = _relative_from_amount(int(match.group(1)), match.group(2))
        return TimeParseResult(QueryTimeRange(last=last), explicit=True)

    if "today" in lowered:
        from_utc = _local_midnight(now, tz)
        caveats: list[str] = []
        range_seconds = (now - from_utc).total_seconds()
        if range_seconds > max_range_seconds:
            from_utc = now - timedelta(seconds=max_range_seconds)
            caveats.append(
                f"Showing the last {max_range_seconds // 3600} hours; "
                "earlier data is not retained."
            )
        return TimeParseResult(
            QueryTimeRange(from_utc=from_utc, to_utc=now),
            explicit=True,
            caveats=tuple(caveats),
        )

    if "yesterday" in lowered:
        today_start = _local_midnight(now, tz)
        from_utc = today_start - timedelta(days=1)
        to_utc = today_start
        return TimeParseResult(
            QueryTimeRange(from_utc=from_utc, to_utc=to_utc),
            explicit=True,
        )

    if "this morning" in lowered:
        from_utc = _this_morning_start(now, tz)
        return TimeParseResult(
            QueryTimeRange(from_utc=from_utc, to_utc=now),
            explicit=True,
        )

    since = _SINCE_RE.search(text)
    if since:
        hour, minute = int(since.group(1)), int(since.group(2))
        local = now.astimezone(tz)
        start_local = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if start_local > local:
            start_local -= timedelta(days=1)
        return TimeParseResult(
            QueryTimeRange(from_utc=start_local.astimezone(UTC), to_utc=now),
            explicit=True,
        )

    between = _BETWEEN_RE.search(text)
    if between:
        left, right = between.group(1).strip(), between.group(2).strip()
        parsed_left = _parse_short_datetime(left, now=now, tz=tz)
        parsed_right = _parse_short_datetime(right, now=now, tz=tz)
        if parsed_left is not None and parsed_right is not None:
            from_utc, to_utc = parsed_left, parsed_right
            if from_utc > to_utc:
                from_utc, to_utc = to_utc, from_utc
            return TimeParseResult(
                QueryTimeRange(from_utc=from_utc, to_utc=to_utc),
                explicit=True,
            )

    return TimeParseResult(
        QueryTimeRange(last=default_last),
        explicit=False,
        caveats=(f"Using default time range of last {default_last}.",),
    )


def _parse_short_datetime(
    token: str, *, now: datetime, tz: ZoneInfo
) -> datetime | None:
    token = token.strip().lower()
    if token == "now":
        return now
    if token == "today":
        return _local_midnight(now, tz)
    if token == "yesterday":
        return _local_midnight(now, tz) - timedelta(days=1)
    clock = _SINCE_RE.match(f"since {token}")
    if clock:
        hour, minute = int(clock.group(1)), int(clock.group(2))
        local = now.astimezone(tz)
        start = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return start.astimezone(UTC)
    last = _LAST_N_RE.search(f"last {token}")
    if last:
        delta = _relative_from_amount(int(last.group(1)), last.group(2))
        return now - _parse_relative_duration(delta)
    return None


def baseline_time_range_before(from_utc: datetime, to_utc: datetime) -> QueryTimeRange:
    """Previous window of equal length immediately before the primary range."""
    duration = to_utc - from_utc
    if duration.total_seconds() <= 0:
        duration = timedelta(minutes=30)
    return QueryTimeRange(from_utc=from_utc - duration, to_utc=from_utc)


def _parse_relative_duration(value: str) -> timedelta:
    match = _RELATIVE_RE.match(value.strip())
    if not match:
        return timedelta(minutes=30)
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == "s":
        return timedelta(seconds=amount)
    if unit == "m":
        return timedelta(minutes=amount)
    return timedelta(hours=amount)
