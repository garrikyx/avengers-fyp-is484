"""Shared numeric and completeness formatters for NL templates (FR-NLQ-010, 016)."""

from __future__ import annotations

from datetime import datetime

from telemetry_shared.models.alerts_query import AlertRecord
from telemetry_shared.models.metrics import LatencySummary
from telemetry_shared.models.metrics_query import (
    DataCompleteness,
    EffectiveTimeRange,
    MetricsQueryResponse,
    QueryGroup,
)
from telemetry_shared.models.nl_query import Audience, NlChartRow

from telemetry_backend.nl.render.escape import escape_adaptive_card_text


def format_rate(value: float | None, *, label: str = "reject rate") -> str:
    if value is None:
        return f"not enough activity to compute {label}"
    return f"{value:.1%}"


def format_int(value: int | float | None, *, default: int = 0) -> str:
    if value is None:
        return str(default)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(int(value)) if isinstance(value, (int, float)) else str(default)


def completeness_sentence(completeness: DataCompleteness) -> str | None:
    if completeness.confidence == "complete":
        return None
    expected = completeness.agents_expected
    reporting = completeness.agents_reporting
    if expected <= 0:
        return (
            f"Data confidence is {completeness.confidence}; "
            "these numbers may be incomplete."
        )
    missing = expected - reporting
    if missing > 0:
        return (
            f"{missing} of {expected} agents is not reporting, "
            "so these numbers are incomplete."
        )
    if completeness.stale_agents:
        return (
            f"{len(completeness.stale_agents)} of {expected} agents is stale; "
            "these numbers may be incomplete."
        )
    return (
        f"Data confidence is {completeness.confidence}; "
        "these numbers may be incomplete."
    )


def effective_range_sentence(effective: EffectiveTimeRange) -> str:
    start = effective.from_utc.strftime("%Y-%m-%d %H:%M UTC")
    end = effective.to_utc.strftime("%Y-%m-%d %H:%M UTC")
    return f"Data covers {start} through {end}."


def top_groups_by_counter(
    groups: list[QueryGroup],
    counter: str,
    *,
    limit: int = 3,
    label_key: str = "rejectReason",
) -> list[tuple[str, int]]:
    ranked: list[tuple[str, int]] = []
    for group in groups:
        raw = group.counters.get(counter)
        if raw is None:
            continue
        count = int(raw)
        label = (
            group.dimensions.get(label_key)
            or group.dimensions.get("instanceId")
            or "other"
        )
        ranked.append((str(label), count))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:limit]


def breakdown_phrase(
    ranked: list[tuple[str, int]],
    *,
    audience: Audience,
) -> str:
    if not ranked:
        return ""
    parts: list[str] = []
    for label, count in ranked:
        safe_label = escape_adaptive_card_text(label)
        if audience == "executive":
            parts.append(f"{safe_label} ({count})")
        else:
            parts.append(f"{safe_label} with {count} occurrences")
    return "The largest categories were " + ", followed by ".join(parts) + "."


def latency_phrase(latency: dict[str, LatencySummary]) -> str:
    summary = latency.get("ack_latency_ms")
    if (
        summary is None
        or summary.count == 0
        or summary.p50 is None
        or summary.p95 is None
    ):
        return "Ack latency is not available (insufficient samples)."
    return (
        f"Ack latency p50 {summary.p50:.0f} ms, "
        f"p95 {summary.p95:.0f} ms over {summary.count} samples."
    )


def alert_duration_minutes(alert: AlertRecord, *, now: datetime) -> int:
    delta = now - alert.first_observed_utc
    return max(int(delta.total_seconds() // 60), 0)


def delivery_phrase(alert: AlertRecord) -> str:
    delivery = alert.delivery
    status = escape_adaptive_card_text(delivery.status)
    attempts = delivery.attempts
    if status == "unknown":
        return "Callback to Magic: not yet reported."
    if status == "delivered":
        return f"Callback to Magic: delivered ({attempts} attempt(s))."
    if status == "failed":
        return f"Callback to Magic: failed after {attempts} attempt(s)."
    return f"Callback to Magic: {status} ({attempts} attempt(s))."


def alert_prose(
    alerts: list[AlertRecord],
    *,
    audience: Audience,
    now: datetime,
) -> str:
    if not alerts:
        return ""
    alert = alerts[0]
    minutes = alert_duration_minutes(alert, now=now)
    delivery = delivery_phrase(alert)
    if audience == "executive":
        return (
            f"The {escape_adaptive_card_text(alert.rule_name)} alert has been "
            f"active for {minutes} minutes. {delivery}"
        )
    return (
        f"The {escape_adaptive_card_text(alert.rule_name)} alert "
        f"({escape_adaptive_card_text(alert.alert_id)}) is active on "
        f"{escape_adaptive_card_text(alert.instance_id)} for {minutes} minutes. "
        f"{delivery}"
    )


def chart_rows_from_groups(
    groups: list[QueryGroup],
    counter: str,
    *,
    limit: int = 5,
    label_key: str = "rejectReason",
) -> list[NlChartRow]:
    rows: list[NlChartRow] = []
    for label, count in top_groups_by_counter(
        groups, counter, limit=limit, label_key=label_key
    ):
        rows.append(NlChartRow(name=label, value=count))
    return rows


def compare_delta_phrase(
    primary: MetricsQueryResponse,
    baseline: MetricsQueryResponse,
    *,
    metric: str = "rejectRate",
) -> str:
    current = primary.totals.get(metric)
    previous = baseline.totals.get(metric)
    if current is None or previous is None:
        return "Period comparison is not available due to insufficient activity."
    delta = current - previous
    direction = "higher" if delta > 0 else "lower" if delta < 0 else "unchanged"
    if direction == "unchanged":
        return f"Reject rate is unchanged at {format_rate(current)}."
    return (
        f"Reject rate is {format_rate(current)}, {abs(delta):.1%} {direction} "
        f"than the previous period ({format_rate(previous)})."
    )
