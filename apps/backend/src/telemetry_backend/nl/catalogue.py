"""Day-1 intent catalogue and slot defaults (FR-NLQ-003, FR-NLQ-004)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from telemetry_shared.models.metrics_query import QueryTimeRange
from telemetry_shared.models.nl_query import IntentId, NlQueryContext

Step = Literal["10s", "1m", "5m"]


@dataclass(frozen=True, slots=True)
class IntentDefinition:
    intent: IntentId
    description: str
    example_questions: tuple[str, ...]
    required_slots: tuple[str, ...]
    optional_slots: tuple[str, ...]
    metrics: tuple[str, ...]
    group_by: tuple[str, ...]
    series: bool = False
    step: Step = "1m"
    percentiles: dict[str, list[int]] | None = None


INTENT_DEFINITIONS: dict[IntentId, IntentDefinition] = {
    "rejection_summary": IntentDefinition(
        intent="rejection_summary",
        description="Reject counts and rate grouped by reject reason and instance.",
        example_questions=(
            "Why are orders rejecting?",
            "Show reject rate in the last 30 minutes",
        ),
        required_slots=(),
        optional_slots=("timeRange", "application", "instanceId", "groupBy"),
        metrics=("orders_submitted", "orders_rejected", "rejectRate"),
        group_by=("rejectReason", "instanceId"),
    ),
    "order_flow_summary": IntentDefinition(
        intent="order_flow_summary",
        description="Orders, acks, executions, rejects, and fill rate over the range.",
        example_questions=(
            "How is Magic doing today?",
            "Order flow summary for the last hour",
        ),
        required_slots=(),
        optional_slots=("timeRange", "application", "instanceId"),
        metrics=(
            "orders_submitted",
            "orders_acked",
            "executions",
            "orders_rejected",
            "fillRate",
        ),
        group_by=("instanceId",),
    ),
    "latency_summary": IntentDefinition(
        intent="latency_summary",
        description="Ack latency percentiles and throughput over the range.",
        example_questions=(
            "Is Magic slow right now?",
            "Show ack latency in the last 15 minutes",
        ),
        required_slots=(),
        optional_slots=("timeRange", "application", "instanceId"),
        metrics=("throughput",),
        group_by=("instanceId",),
        percentiles={"ack_latency_ms": [50, 95, 99]},
    ),
    "alert_status": IntentDefinition(
        intent="alert_status",
        description="Active alerts with severity and duration.",
        example_questions=(
            "Any alerts open for Magic?",
            "Show active alerts",
        ),
        required_slots=(),
        optional_slots=("application", "instanceId"),
        metrics=("orders_submitted",),
        group_by=(),
    ),
    "session_status": IntentDefinition(
        intent="session_status",
        description="FIX session logons, logouts, sequence gaps, and heartbeat issues.",
        example_questions=(
            "Are the FIX sessions up?",
            "Session status for magic-prod-01",
        ),
        required_slots=(),
        optional_slots=("timeRange", "instanceId", "session"),
        metrics=("logouts", "seq_gaps", "clock_skew_events"),
        group_by=("sessionId", "instanceId"),
    ),
    "symbol_drilldown": IntentDefinition(
        intent="symbol_drilldown",
        description="Metrics for a symbol grouped by reject reason.",
        example_questions=(
            "What's rejecting on ABC?",
            "Show rejects for symbol XYZ",
        ),
        required_slots=("symbol",),
        optional_slots=("timeRange", "application", "instanceId"),
        metrics=("orders_rejected", "rejectRate"),
        group_by=("rejectReason",),
    ),
    "agent_health": IntentDefinition(
        intent="agent_health",
        description="Telemetry agent heartbeat age, lag, and drop indicators.",
        example_questions=(
            "Is telemetry actually working?",
            "Agent health for magic-prod-01",
        ),
        required_slots=(),
        optional_slots=("instanceId",),
        metrics=("log_lines_read", "parse_errors", "publish_failures"),
        group_by=("instanceId",),
    ),
    "parse_health": IntentDefinition(
        intent="parse_health",
        description="Parse errors grouped by reason.",
        example_questions=(
            "Are we failing to parse anything?",
            "Parse error breakdown",
        ),
        required_slots=(),
        optional_slots=("timeRange", "instanceId"),
        metrics=("parse_errors",),
        group_by=("rejectReason",),
    ),
    "compare_period": IntentDefinition(
        intent="compare_period",
        description="Compare reject metrics between two time ranges.",
        example_questions=(
            "Are rejects worse than yesterday?",
            "Compare reject rate to yesterday",
        ),
        required_slots=(),
        optional_slots=("timeRange", "application", "instanceId"),
        metrics=("orders_submitted", "orders_rejected", "rejectRate"),
        group_by=("instanceId",),
    ),
    "trend": IntentDefinition(
        intent="trend",
        description="Time series of rejects over the range.",
        example_questions=(
            "Show rejects over the last hour",
            "Reject trend today",
        ),
        required_slots=(),
        optional_slots=("timeRange", "application", "instanceId", "step"),
        metrics=("orders_rejected",),
        group_by=(),
        series=True,
        step="1m",
    ),
}

SUPPORTED_INTENTS: tuple[IntentId, ...] = tuple(INTENT_DEFINITIONS.keys())


def default_time_range(default_last: str) -> QueryTimeRange:
    return QueryTimeRange(last=default_last)


def build_default_filters(context: NlQueryContext) -> dict[str, str]:
    return {"application": context.default_application}
