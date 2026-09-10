"""Derived-ratio computation (spec 004 §4.5, FR-QRY-010, FR-STM-003).

Shared by the agent (ratios over one agent's own window) and the backend
Stream Processor / Query Engine (ratios over counters already summed across
every contributing agent). The rule is the same in both places and MUST stay
one implementation: a ratio is never averaged — including never averaging
per-agent ratios — it is always recomputed from a numerator and a
denominator that are themselves sums of raw counters.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from telemetry_shared.models.metrics import Indicator, Indicators


@dataclass(slots=True, frozen=True)
class RatioDef:
    name: str
    numerator: str
    denominator: tuple[str, ...]


# spec 004 §4.5's own formulas, verbatim.
STANDARD_RATIOS: tuple[RatioDef, ...] = (
    RatioDef("reject_rate", "orders_rejected", ("orders_acked", "orders_rejected")),
    RatioDef("fill_rate", "executions", ("orders_acked",)),
    RatioDef("cancel_rate", "orders_canceled", ("orders_submitted",)),
    RatioDef("parse_error_rate", "parse_errors", ("log_lines_read",)),
)


def compute_ratio(
    counters: dict[str, Decimal], ratio: RatioDef, min_sample_size: int
) -> Indicator:
    """`value` is None when `denominator` is 0 (never fabricate a rate from
    no data). `low_confidence` is True whenever `denominator` is below
    `min_sample_size` — including the zero-denominator case.
    """
    numerator = counters.get(ratio.numerator, Decimal(0))
    denominator = sum(
        (counters.get(dim, Decimal(0)) for dim in ratio.denominator), Decimal(0)
    )
    if denominator == 0:
        return Indicator(value=None, denominator=0, low_confidence=True)
    return Indicator(
        value=float(numerator / denominator),
        denominator=int(denominator),
        low_confidence=denominator < min_sample_size,
    )


def compute_indicators(
    counters: dict[str, Decimal], *, min_sample_size: int, window_seconds: float
) -> Indicators:
    """All four spec 004 §4.5 indicators from one counters map — the caller
    supplies counters already summed across whatever scope applies (one
    agent's window, or every agent contributing to a backend time range).
    """
    ratios = {
        ratio.name: compute_ratio(counters, ratio, min_sample_size)
        for ratio in STANDARD_RATIOS
    }
    throughput = (
        float(counters.get("orders_submitted", Decimal(0))) / window_seconds
        if window_seconds > 0
        else 0.0
    )
    return Indicators(
        reject_rate=ratios["reject_rate"],
        fill_rate=ratios["fill_rate"],
        cancel_rate=ratios["cancel_rate"],
        parse_error_rate=ratios["parse_error_rate"],
        throughput=throughput,
    )
