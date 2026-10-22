"""Natural language query models (spec 007 §6, spec 008)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.alerts_query import AlertDelivery
from telemetry_shared.models.metrics_query import MetricsQueryResponse, QueryTimeRange

Audience = Literal["technical", "executive"]

IntentId = Literal[
    "rejection_summary",
    "order_flow_summary",
    "latency_summary",
    "alert_status",
    "session_status",
    "symbol_drilldown",
    "agent_health",
    "parse_health",
    "compare_period",
    "trend",
]

InterpretationSource = Literal["rule", "llm"]


class NlQueryContext(CamelModel):
    default_application: str = "Magic"
    user_timezone: str = "Asia/Singapore"
    audience: Audience = "technical"


class InterpretedQuery(CamelModel):
    intent: IntentId
    time_range: QueryTimeRange
    filters: dict[str, str | list[str]] = Field(default_factory=dict)
    group_by: list[str] = Field(default_factory=list, max_length=3)
    metrics: list[str] = Field(min_length=1)
    percentiles: dict[str, list[int]] | None = None
    top_k: int | None = Field(default=None, ge=1)
    series: bool = False
    step: Literal["10s", "1m", "5m"] = "1m"


class NlQueryRequest(CamelModel):
    question: str = Field(min_length=1)
    context: NlQueryContext = Field(default_factory=NlQueryContext)


class NlCitation(CamelModel):
    type: Literal["metrics_query", "alert"]
    query_id: str | None = None
    alert_id: str | None = None


class NlChartRow(CamelModel):
    name: str
    value: str | float | int


class NlAlertSummary(CamelModel):
    alert_id: str
    rule_name: str
    severity: str
    status: str
    instance_id: str
    delivery: AlertDelivery


class NlQueryResponse(CamelModel):
    kind: Literal["answer"] = "answer"
    answer: str
    intent: IntentId
    confidence: float = Field(ge=0.0, le=1.0)
    source: InterpretationSource
    interpreted_query: InterpretedQuery
    data: MetricsQueryResponse
    citations: list[NlCitation] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    chart_rows: list[NlChartRow] = Field(default_factory=list)
    alert_summaries: list[NlAlertSummary] = Field(default_factory=list)


class IntentCatalogueEntry(CamelModel):
    intent: IntentId
    description: str
    example_questions: list[str]
    required_slots: list[str]
    optional_slots: list[str]


class NlIntentsResponse(CamelModel):
    intents: list[IntentCatalogueEntry]


class NlClarificationResponse(CamelModel):
    kind: Literal["clarification"] = "clarification"
    message: str
    supported_intents: list[IntentId]
    details: list[str] = Field(default_factory=list)
