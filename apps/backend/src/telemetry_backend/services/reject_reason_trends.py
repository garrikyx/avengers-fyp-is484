"""Increasing reject reasons (UBS-27): current window vs. the preceding one.

Built on `QueryEngine.query()` (grouped by `rejectReason`, counter
`orders_rejected`) rather than reading the Metric Store directly, so
retention limits, instance filters and replica fan-out behave exactly as for
`POST /telemetry/query/metrics`.

A reason is **increasing** when its count in the latest window exceeds the
preceding equal-length window's by more than `threshold`, and **emerging**
when it was absent before. Both need `min_occurrences` in the latest window.
"""

from __future__ import annotations

from datetime import datetime

from telemetry_shared.models.metrics_query import (
    MetricsQueryRequest,
    MetricsQueryResponse,
    QueryTimeRange,
)
from telemetry_shared.models.trends import (
    ReasonTrend,
    RejectReasonTrendsRequest,
    RejectReasonTrendsResponse,
    TrendDirection,
)

from telemetry_backend.services.query_engine import QueryEngine, QueryValidationError

_METRIC = "rejections"  # alias of orders_rejected (telemetry_shared.query.aliases)
_REASON = "rejectReason"
_STEADY_BAND = 0.1  # within +/-10% is "steady", not worth a line either way


def classify(
    current: int, previous: int, *, threshold: float, min_occurrences: int
) -> tuple[TrendDirection, float | None]:
    """Direction and relative change for one reason's two counts."""
    if previous == 0:
        change = None
        direction: TrendDirection = (
            "emerging" if current >= min_occurrences else "steady"
        )
        return direction, change
    change = (current - previous) / previous
    if change > threshold and current >= min_occurrences:
        return "increasing", change
    if change < -_STEADY_BAND:
        return "decreasing", change
    return "steady", change


class RejectReasonTrendService:
    def __init__(self, engine: QueryEngine) -> None:
        self._engine = engine

    async def analyse(
        self,
        request: RejectReasonTrendsRequest,
        *,
        now: datetime,
        skip_fanout: bool = False,
        fanout_client: object | None = None,
    ) -> RejectReasonTrendsResponse:
        """Raises `QueryValidationError` for a bad window or filter."""
        length = self._engine._parse_relative(request.window)
        if length.total_seconds() <= 0:
            raise QueryValidationError(
                code="invalid_field",
                message="window must be positive.",
                field="window",
                issue=f"{request.window!r} is not a positive duration",
            )
        current_from, previous_from = now - length, now - 2 * length

        current = await self._counts(
            request, current_from, now, skip_fanout, fanout_client, now
        )
        previous = await self._counts(
            request, previous_from, current_from, skip_fanout, fanout_client, now
        )

        complete = self._covers(previous_from, now)
        reasons = self._trends(current, previous, request)
        flagged = (
            sorted(
                (t for t in reasons if t.trend in ("emerging", "increasing")),
                key=lambda t: (
                    t.change_ratio is not None,  # emerging (unbounded) first
                    -(t.change_ratio or 0.0),
                    -t.current_count,
                ),
            )
            if complete
            else []
        )
        if not complete:
            reasons = [t.model_copy(update={"trend": "steady"}) for t in reasons]
        caveats = (
            []
            if complete
            else [
                "The Metric Store does not yet cover the whole preceding "
                f"{request.window} window, so no trend is reported."
            ]
        )
        return RejectReasonTrendsResponse(
            evaluated_at_utc=now,
            window=request.window,
            threshold=request.threshold,
            min_occurrences=request.min_occurrences,
            current_from_utc=current_from,
            current_to_utc=now,
            previous_from_utc=previous_from,
            previous_to_utc=current_from,
            previous_window_complete=complete,
            increasing=flagged,
            reasons=reasons,
            caveats=caveats,
        )

    def _covers(self, start: datetime, now: datetime) -> bool:
        oldest, _ = self._engine.store.retention_bounds(now=now)
        return oldest is not None and oldest <= start

    async def _counts(
        self,
        request: RejectReasonTrendsRequest,
        start: datetime,
        end: datetime,
        skip_fanout: bool,
        fanout_client: object | None,
        now: datetime,
    ) -> dict[str, int]:
        query = MetricsQueryRequest(
            time_range=QueryTimeRange(from_utc=start, to_utc=end),
            filters=request.filters,
            group_by=[_REASON],
            metrics=[_METRIC],
        )
        try:
            response = await self._engine.query(
                query, now=now, skip_fanout=skip_fanout, fanout_client=fanout_client
            )
        except QueryValidationError as exc:
            # The preceding window can lie wholly outside retention while the
            # latest one does not; that is "no history", not a bad request.
            if exc.code == "invalid_time_range" and start < end <= now:
                return {}
            raise
        return _by_reason(response)

    @staticmethod
    def _trends(
        current: dict[str, int],
        previous: dict[str, int],
        request: RejectReasonTrendsRequest,
    ) -> list[ReasonTrend]:
        trends: list[ReasonTrend] = []
        for reason in sorted(current.keys() | previous.keys()):
            now_count, before = current.get(reason, 0), previous.get(reason, 0)
            direction, change = classify(
                now_count,
                before,
                threshold=request.threshold,
                min_occurrences=request.min_occurrences,
            )
            trends.append(
                ReasonTrend(
                    reject_reason=reason,
                    current_count=now_count,
                    previous_count=before,
                    change_ratio=change,
                    trend=direction,
                )
            )
        return sorted(trends, key=lambda t: -t.current_count)


def _by_reason(response: MetricsQueryResponse) -> dict[str, int]:
    counts: dict[str, int] = {}
    for group in response.groups:
        reason = group.dimensions.get(_REASON)
        value = group.counters.get(_METRIC)
        if reason is None or not value:
            continue
        counts[reason] = counts.get(reason, 0) + int(value)
    return counts
