"""Shared contract: the Metrics Aggregator's snapshot output (MA-04).

Built by `telemetry_agent.metrics.snapshot.snapshot()` from the already-tested
`MetricsAggregator`/`LatencyCorrelator` (MA-01/02/03). Consumed by the Rule
Engine (alert evaluation — see the alert-readiness table in
docs/plan/ma-epic-implementation-summary.md) and the Backend Publisher, whose
eventual relay target is `POST /telemetry/query/metrics` (spec 007 §3) —
field names here mirror that response shape so relaying needs no renaming.
Pydantic per FR-ING-022: shared cross-component schemas live in
packages/telemetry_shared, not duplicated per app.

Wire format is camelCase (spec 004/007's own convention); Python attributes
stay snake_case via `alias_generator`.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, frozen=True, extra="forbid"
    )


class Indicator(_CamelModel):
    """One computed ratio (rejectRate/fillRate/cancelRate/parseErrorRate).

    `value` is None when `denominator` is 0 (spec 004 §4.5: never fabricate a
    rate from no data). `low_confidence` is True whenever `denominator` is
    below the configured minimum sample size — including the denominator==0
    case — so a Rule Engine can tell "no data" and "a little data" apart from
    "enough data to trust", without conflating a real 100% rate from one
    sample with an idle window (this is what stops HighRejectRate firing on
    one rejected order).
    """

    value: float | None
    denominator: int
    low_confidence: bool


class Indicators(_CamelModel):
    """spec 004 §4.5's derived KPIs. `parse_error_rate` is formula-ready but
    will read as `value=None, low_confidence=True` until a future ticket
    wires a `parse_errors`/`log_lines_read` producer into the aggregator —
    nothing fabricates data for it. `throughput` (orders/sec) is not a ratio
    of two counters, so it carries no denominator/low_confidence.
    """

    reject_rate: Indicator
    fill_rate: Indicator
    cancel_rate: Indicator
    parse_error_rate: Indicator
    throughput: float


class LatencySummary(_CamelModel):
    """Percentiles are approximate (FR-QRY-012, interpolated from fixed
    histogram bucket boundaries) — `approximate` is always True today, kept
    as an explicit field rather than a comment so a consumer doesn't have to
    assume it.
    """

    p50: float | None
    p95: float | None
    p99: float | None
    avg: float | None
    count: int
    approximate: bool = True


class Gauges(_CamelModel):
    """Instance-wide state, not grouped by dimension — matching spec 004 §3
    where gauges sit beside `series[]`, not nested inside each series.
    """

    pending_orders: int
    oldest_pending_age_seconds: float | None
    seconds_since_last_event: float | None


class WindowBounds(_CamelModel):
    from_utc: datetime
    to_utc: datetime


class MetricsGroup(_CamelModel):
    """One row of a snapshot. `dimensions` is empty for the ungrouped
    (`groupBy=[]`) case — that row *is* the window-wide total, so there is no
    separate duplicate totals block.
    """

    dimensions: dict[str, str]
    counters: dict[str, Decimal]
    indicators: Indicators
    latency: dict[str, LatencySummary]

    @field_serializer("counters")
    def _serialize_counters(
        self, counters: dict[str, Decimal]
    ) -> dict[str, int | float]:
        # Counters are always whole (every write is a positive increment or
        # a whole-quantity fill) — emit plain JSON numbers matching spec
        # 007's example, not Pydantic's default Decimal-as-string encoding.
        return {
            key: int(value) if value == value.to_integral_value() else float(value)
            for key, value in counters.items()
        }


class MetricsSnapshot(_CamelModel):
    window: str
    window_bounds: WindowBounds
    generated_at_utc: datetime
    group_by: tuple[str, ...]
    gauges: Gauges
    groups: list[MetricsGroup]
