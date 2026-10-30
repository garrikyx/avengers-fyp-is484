"""Template-based NL answer rendering (FR-NLQ-009, FR-NLQ-015, FR-NLQ-027)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from telemetry_shared.models.alerts_query import AlertRecord
from telemetry_shared.models.metrics_query import MetricsQueryResponse
from telemetry_shared.models.nl_query import (
    Audience,
    IntentId,
    NlAlertSummary,
    NlChartRow,
)

from telemetry_backend.nl.render import formatters as fmt
from telemetry_backend.nl.render.escape import escape_adaptive_card_text


@dataclass(frozen=True, slots=True)
class RenderInput:
    intent: IntentId
    data: MetricsQueryResponse
    audience: Audience = "technical"
    alerts: tuple[AlertRecord, ...] = ()
    baseline_data: MetricsQueryResponse | None = None
    application: str = "Magic"
    extra_caveats: tuple[str, ...] = ()
    now: datetime | None = None


@dataclass(frozen=True, slots=True)
class RenderOutput:
    answer: str
    chart_rows: list[NlChartRow] = field(default_factory=list)
    alert_summaries: list[NlAlertSummary] = field(default_factory=list)


def _append_caveats(parts: list[str], inp: RenderInput) -> None:
    completeness = fmt.completeness_sentence(inp.data.data_completeness)
    if completeness:
        parts.append(completeness)
    for caveat in inp.extra_caveats:
        if caveat and caveat not in parts:
            parts.append(caveat)


def _indicator_rate(totals: dict[str, int | float | None], key: str) -> float | None:
    value = totals.get(key)
    return value if isinstance(value, float) else None


def _summaries(alerts: tuple[AlertRecord, ...]) -> list[NlAlertSummary]:
    return [
        NlAlertSummary(
            alert_id=a.alert_id,
            rule_name=a.rule_name,
            severity=a.severity,
            status=a.status,
            instance_id=a.instance_id,
            delivery=a.delivery,
        )
        for a in alerts
    ]


def render_answer(inp: RenderInput) -> RenderOutput:
    """Build deterministic prose from query results only."""
    now = inp.now or inp.data.evaluated_at_utc
    parts: list[str] = []
    chart_rows: list[NlChartRow] = []

    app = escape_adaptive_card_text(inp.application)
    totals = inp.data.totals
    groups = inp.data.groups

    if inp.intent == "rejection_summary":
        rejected = totals.get("orders_rejected")
        submitted = totals.get("orders_submitted")
        rate = totals.get("rejectRate")
        if rejected is None and submitted is None:
            parts.append("No order activity in the selected time range.")
        else:
            lead = (
                f"{app} recorded {fmt.format_int(rejected)} rejected orders "
                f"out of {fmt.format_int(submitted)} submitted "
                f"({fmt.format_rate(rate if isinstance(rate, float) else None)})."
            )
            parts.append(lead)
            ranked = fmt.top_groups_by_counter(groups, "orders_rejected")
            breakdown = fmt.breakdown_phrase(ranked, audience=inp.audience)
            if breakdown:
                parts.append(breakdown)
            chart_rows = fmt.chart_rows_from_groups(groups, "orders_rejected")
        alert_text = fmt.alert_prose(list(inp.alerts), audience=inp.audience, now=now)
        if alert_text:
            parts.append(alert_text)

    elif inp.intent == "order_flow_summary":
        fill = fmt.format_rate(_indicator_rate(totals, "fillRate"), label="fill rate")
        parts.append(
            f"{app} order flow: "
            f"{fmt.format_int(totals.get('orders_submitted'))} submitted, "
            f"{fmt.format_int(totals.get('orders_acked'))} acked, "
            f"{fmt.format_int(totals.get('executions'))} executions, "
            f"{fmt.format_int(totals.get('orders_rejected'))} rejects "
            f"(fill rate {fill})."
        )

    elif inp.intent == "latency_summary":
        throughput = totals.get("throughput")
        tp = (
            f"{throughput:.1f}"
            if isinstance(throughput, (int, float))
            else "unavailable"
        )
        latency = fmt.latency_phrase(inp.data.latency)
        parts.append(f"{app} throughput is {tp} orders/min. {latency}")

    elif inp.intent == "alert_status":
        count = len(inp.alerts)
        if count == 0:
            parts.append(f"No active alerts match the requested scope for {app}.")
        else:
            parts.append(f"{count} active alert(s) for {app}.")
            for alert in inp.alerts[:3]:
                if inp.audience == "executive":
                    parts.append(
                        f"- {escape_adaptive_card_text(alert.rule_name)} "
                        f"({escape_adaptive_card_text(alert.severity)}). "
                        f"{fmt.delivery_phrase(alert)}"
                    )
                else:
                    parts.append(
                        f"- {escape_adaptive_card_text(alert.rule_name)} on "
                        f"{escape_adaptive_card_text(alert.instance_id)} "
                        f"({escape_adaptive_card_text(alert.alert_id)}). "
                        f"{fmt.delivery_phrase(alert)}"
                    )

    elif inp.intent == "session_status":
        parts.append(
            f"Session activity: {fmt.format_int(totals.get('logouts'))} logouts, "
            f"{fmt.format_int(totals.get('seq_gaps'))} sequence gaps."
        )

    elif inp.intent == "symbol_drilldown":
        rate_text = fmt.format_rate(_indicator_rate(totals, "rejectRate"))
        rejects = fmt.format_int(totals.get("orders_rejected"))
        parts.append(f"Symbol scope shows {rejects} rejects ({rate_text}).")
        ranked = fmt.top_groups_by_counter(
            groups, "orders_rejected", label_key="rejectReason"
        )
        breakdown = fmt.breakdown_phrase(ranked, audience=inp.audience)
        if breakdown:
            parts.append(breakdown)

    elif inp.intent == "agent_health":
        parts.append(
            "Telemetry agent health: "
            f"{fmt.format_int(totals.get('log_lines_read'))} lines read, "
            f"{fmt.format_int(totals.get('parse_errors'))} parse errors, "
            f"{fmt.format_int(totals.get('publish_failures'))} publish failures."
        )

    elif inp.intent == "parse_health":
        errors = fmt.format_int(totals.get("parse_errors"))
        parts.append(f"Parse health: {errors} parse errors in range.")
        ranked = fmt.top_groups_by_counter(
            groups, "parse_errors", label_key="rejectReason"
        )
        breakdown = fmt.breakdown_phrase(ranked, audience=inp.audience)
        if breakdown:
            parts.append(breakdown)

    elif inp.intent == "compare_period":
        rate = totals.get("rejectRate")
        parts.append(
            f"Primary period reject rate is "
            f"{fmt.format_rate(rate if isinstance(rate, float) else None)}."
        )
        if inp.baseline_data is not None:
            parts.append(fmt.compare_delta_phrase(inp.data, inp.baseline_data))
        elif inp.audience == "executive":
            parts.append("Previous period comparison is not available.")

    elif inp.intent == "trend":
        points = sum(len(g.points or []) for g in groups)
        parts.append(
            f"Reject trend returned {len(groups)} series with {points} point(s) "
            f"over {fmt.effective_range_sentence(inp.data.effective_time_range)}"
        )
        chart_rows = fmt.chart_rows_from_groups(groups, "orders_rejected")

    else:
        parts.append("Query completed.")

    parts.append(fmt.effective_range_sentence(inp.data.effective_time_range))
    _append_caveats(parts, inp)

    answer = " ".join(p for p in parts if p).strip()
    if len(answer.split()) > 95 and inp.intent in {
        "rejection_summary",
        "order_flow_summary",
        "latency_summary",
    }:
        answer = " ".join(answer.split()[:95]) + "…"

    return RenderOutput(
        answer=answer,
        chart_rows=chart_rows,
        alert_summaries=_summaries(inp.alerts),
    )
