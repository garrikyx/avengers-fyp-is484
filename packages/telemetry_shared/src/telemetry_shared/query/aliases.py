"""Metric and dimension alias resolution (`FR-QRY-034`).

The query API uses spec 004/007 wire names; the agent and Metric Store use
Python snake_case dimension keys on the wire snapshot series.
"""

from __future__ import annotations

# Convenience aliases accepted in `metrics[]`.
METRIC_ALIASES: dict[str, str] = {
    "orders": "orders_submitted",
    "rejections": "orders_rejected",
    "executions": "executions",
}

# Derived KPIs — not counters; resolved via `Indicators`.
DERIVED_METRICS: frozenset[str] = frozenset(
    {
        "rejectRate",
        "reject_rate",
        "fillRate",
        "fill_rate",
        "cancelRate",
        "cancel_rate",
        "parseErrorRate",
        "parse_error_rate",
        "throughput",
    }
)

# API / spec dimension name -> stored series dimension key.
API_DIMENSION_TO_STORED: dict[str, str] = {
    "sessionId": "session_id",
    "session": "session_id",
    "rejectReason": "reject_reason",
    "instanceId": "instance_id",
    "symbol": "symbol",
    "side": "side",
    "ordType": "ord_type",
    "ord_type": "ord_type",
    "msgType": "msg_type",
    "application": "application",
}

STORED_TO_API_DIMENSION: dict[str, str] = {
    "session_id": "sessionId",
    "reject_reason": "rejectReason",
    "instance_id": "instanceId",
    "symbol": "symbol",
    "side": "side",
    "ord_type": "ordType",
    "msg_type": "msgType",
}

KNOWN_COUNTERS: frozenset[str] = frozenset(
    {
        "orders_submitted",
        "orders_acked",
        "orders_rejected",
        "orders_canceled",
        "executions",
        "fills_full",
        "fills_partial",
        "order_qty",
        "parse_errors",
        "log_lines_read",
        "logouts",
        "seq_gaps",
        "clock_skew_events",
        "callback_failures",
        "publish_failures",
    }
)


def resolve_metric_name(name: str) -> str | None:
    """Map an API metric name to a canonical counter, or None if derived."""
    if name in DERIVED_METRICS:
        return None
    return METRIC_ALIASES.get(name, name)


def resolve_dimension_name(name: str) -> str:
    """Map an API dimension to the stored series key."""
    return API_DIMENSION_TO_STORED.get(name, name)


def to_api_dimension(stored: str) -> str:
    """Map a stored dimension key back to the API wire name."""
    return STORED_TO_API_DIMENSION.get(stored, stored)


def is_known_metric(name: str) -> bool:
    canonical = resolve_metric_name(name)
    if canonical is None:
        return name in DERIVED_METRICS or name.replace("_", "") in {
            m.replace("_", "") for m in DERIVED_METRICS
        }
    return canonical in KNOWN_COUNTERS or name in METRIC_ALIASES
