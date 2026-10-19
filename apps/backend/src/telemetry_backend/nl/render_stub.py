"""Minimal template answers until UBS-99 full renderer."""

from __future__ import annotations

from telemetry_shared.models.metrics_query import MetricsQueryResponse
from telemetry_shared.models.nl_query import IntentId


def render_stub_answer(
    intent: IntentId,
    *,
    data: MetricsQueryResponse,
    active_alerts: int = 0,
) -> str:
    totals = data.totals
    if intent == "rejection_summary":
        rejected = totals.get("orders_rejected")
        submitted = totals.get("orders_submitted")
        rate = totals.get("rejectRate")
        if rejected is None and submitted is None:
            return "No order activity in the selected time range."
        rate_text = f"{rate:.1%}" if isinstance(rate, float) else "not enough activity"
        return (
            f"Recorded {rejected or 0} rejected orders out of "
            f"{submitted or 0} submitted ({rate_text} reject rate)."
        )
    if intent == "order_flow_summary":
        return (
            f"Order flow: {totals.get('orders_submitted', 0)} submitted, "
            f"{totals.get('executions', 0)} executions, "
            f"{totals.get('orders_rejected', 0)} rejects."
        )
    if intent == "latency_summary":
        throughput = totals.get("throughput")
        label = throughput if throughput is not None else "unavailable"
        return f"Throughput is {label}."
    if intent == "alert_status":
        return f"{active_alerts} active alert(s) match the requested scope."
    if intent == "session_status":
        return (
            f"Session counters: {totals.get('logouts', 0)} logouts, "
            f"{totals.get('seq_gaps', 0)} sequence gaps."
        )
    if intent == "symbol_drilldown":
        return f"Symbol drilldown shows {totals.get('orders_rejected', 0)} rejects."
    if intent == "agent_health":
        return (
            f"Agent health: {totals.get('log_lines_read', 0)} lines read, "
            f"{totals.get('parse_errors', 0)} parse errors."
        )
    if intent == "parse_health":
        return f"Parse health: {totals.get('parse_errors', 0)} parse errors in range."
    if intent == "compare_period":
        rate = totals.get("rejectRate")
        rate_text = f"{rate:.1%}" if isinstance(rate, float) else "insufficient data"
        return (
            f"Primary period reject rate is {rate_text} "
            "(comparison baseline deferred)."
        )
    if intent == "trend":
        return f"Reject trend series returned {len(data.groups)} group(s)."
    return "Query completed."
