"""NL query orchestration (spec 008 §3)."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from telemetry_shared.models.alerts_query import AlertRecord
from telemetry_shared.models.metrics_query import (
    MetricsQueryRequest,
    MetricsQueryResponse,
)
from telemetry_shared.models.nl_query import (
    InterpretedQuery,
    NlCitation,
    NlClarificationResponse,
    NlQueryContext,
    NlQueryResponse,
)

from telemetry_backend.config import NlConfig
from telemetry_backend.nl.catalogue import SUPPORTED_INTENTS as CATALOGUE_INTENTS
from telemetry_backend.nl.compiler import merge_interpreted_query
from telemetry_backend.nl.intents import catalogue_summary_for_prompt
from telemetry_backend.nl.llm.protocol import LlmSlotFiller, LlmSlotFillError
from telemetry_backend.nl.normalize import normalize_question
from telemetry_backend.nl.render import RenderInput, render_answer
from telemetry_backend.nl.rule_matcher import (
    HIGH_CONFIDENCE,
    match_rules,
    rule_match_to_interpreted,
)
from telemetry_backend.nl.time import baseline_time_range_before
from telemetry_backend.nl.validator import (
    InterpretedValidationError,
    validate_interpreted_query,
)
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.query_engine import QueryEngine

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class NlQueryOutcome:
    kind: Literal["answer", "clarification"]
    answer: NlQueryResponse | NlClarificationResponse


class NlQueryService:
    def __init__(
        self,
        *,
        config: NlConfig,
        query_engine: QueryEngine,
        alert_store: AlertStore,
        llm: LlmSlotFiller,
        max_range_seconds: int,
    ) -> None:
        self._config = config
        self._engine = query_engine
        self._alert_store = alert_store
        self._llm = llm
        self._max_range_seconds = max_range_seconds

    async def interpret_and_query(
        self,
        question: str,
        *,
        context: NlQueryContext,
        now: datetime,
        user_id: str | None = None,
    ) -> NlQueryOutcome:
        normalized = normalize_question(
            question, max_chars=self._config.max_question_chars
        )
        rule_match = match_rules(
            normalized,
            context=context,
            config=self._config,
            now=now,
            max_range_seconds=self._max_range_seconds,
        )

        source: Literal["rule", "llm"] = "rule"
        confidence = 0.0
        time_caveats: tuple[str, ...] = ()
        interpreted: InterpretedQuery | None = None

        if rule_match is not None and rule_match.confidence >= HIGH_CONFIDENCE:
            payload, time_caveats = rule_match_to_interpreted(rule_match)
            interpreted = merge_interpreted_query(
                time_range=payload["time_range"],
                filters=payload["filters"],  # type: ignore[arg-type]
                group_by=payload["group_by"],  # type: ignore[arg-type]
                metrics=payload["metrics"],  # type: ignore[arg-type]
                series=payload["series"],  # type: ignore[arg-type]
                step=payload["step"],  # type: ignore[arg-type]
                percentiles=payload["percentiles"],  # type: ignore[arg-type]
                intent=payload["intent"],  # type: ignore[arg-type]
                context=context,
                config=self._config,
            )
            confidence = rule_match.confidence
            source = "rule"
        else:
            source = "llm"
            try:
                llm_result = await asyncio.wait_for(
                    self._llm.fill_slots(
                        normalized,
                        catalogue_summary=catalogue_summary_for_prompt(),
                        schema_json=_slot_schema_json(),
                    ),
                    timeout=self._config.llm.timeout_seconds,
                )
            except (LlmSlotFillError, TimeoutError):
                return NlQueryOutcome(
                    kind="clarification",
                    answer=_clarification(
                        "I could not interpret that question within the time limit. "
                        "Try one of the supported intents."
                    ),
                )
            interpreted = merge_interpreted_query(
                intent=llm_result.intent,
                time_range=llm_result.time_range,
                filters=llm_result.filters,
                group_by=llm_result.group_by,
                metrics=llm_result.metrics,
                series=llm_result.series,
                step=llm_result.step,
                percentiles=llm_result.percentiles,
                context=context,
                config=self._config,
            )
            confidence = 0.75

        assert interpreted is not None
        try:
            validated = validate_interpreted_query(
                interpreted,
                engine=self._engine,
                store=self._engine.store,
                now=now,
            )
        except InterpretedValidationError as exc:
            details = [f"{issue.field}: {issue.issue}" for issue in exc.issues]
            return NlQueryOutcome(
                kind="clarification",
                answer=_clarification(
                    "The interpreted query was invalid. Please clarify your question.",
                    details=details,
                ),
            )

        caveats = list(time_caveats) + list(validated.caveats)
        intent = validated.interpreted.intent
        metrics_request = validated.metrics_request

        baseline_data: MetricsQueryResponse | None = None
        if intent == "compare_period":
            data, baseline_data = await self._query_compare_period(
                metrics_request, now=now
            )
        else:
            data = await self._engine.query(metrics_request, now=now)

        alerts, citations = self._alerts_for_intent(
            intent,
            interpreted=validated.interpreted,
            data=data,
        )
        citations = [
            NlCitation(type="metrics_query", query_id=data.query_id),
            *citations,
        ]

        rendered = render_answer(
            RenderInput(
                intent=intent,
                data=data,
                baseline_data=baseline_data,
                audience=context.audience,
                alerts=tuple(alerts),
                application=str(
                    validated.interpreted.filters.get("application", context.default_application)
                ),
                extra_caveats=tuple(caveats),
                now=now,
            )
        )

        logger.info(
            "nl interpreted query user=%s intent=%s source=%s interpreted=%s",
            user_id or "anonymous",
            validated.interpreted.intent,
            source,
            validated.interpreted.model_dump(mode="json", by_alias=True),
        )
        response = NlQueryResponse(
            answer=rendered.answer,
            intent=validated.interpreted.intent,
            confidence=confidence,
            source=source,
            interpreted_query=validated.interpreted,
            data=data,
            citations=citations,
            caveats=caveats,
            chart_rows=rendered.chart_rows,
            alert_summaries=rendered.alert_summaries,
        )
        return NlQueryOutcome(kind="answer", answer=response)

    async def _query_compare_period(
        self, request: MetricsQueryRequest, *, now: datetime
    ) -> tuple[MetricsQueryResponse, MetricsQueryResponse | None]:
        primary = await self._engine.query(request, now=now)
        from_utc = primary.effective_time_range.from_utc
        to_utc = primary.effective_time_range.to_utc
        baseline_range = baseline_time_range_before(from_utc, to_utc)
        baseline_request = request.model_copy(update={"time_range": baseline_range})
        try:
            self._engine.prepare_metrics_query(baseline_request, now=now)
        except Exception:
            return primary, None
        baseline = await self._engine.query(baseline_request, now=now)
        return primary, baseline

    def _alerts_for_intent(
        self,
        intent: str,
        *,
        interpreted: InterpretedQuery,
        data: MetricsQueryResponse,
    ) -> tuple[list[AlertRecord], list[NlCitation]]:
        if intent not in {"alert_status", "rejection_summary", "order_flow_summary"}:
            return [], []

        application = str(interpreted.filters.get("application", "")) or None
        instance_id = _filter_instance(interpreted.filters)
        listed = self._alert_store.list_alerts(
            status="active",
            application=application,
            instance_id=instance_id,
        )
        alerts = listed.alerts
        if intent == "rejection_summary" and alerts:
            alerts = alerts[:1]
        if intent == "order_flow_summary" and not alerts:
            return [], []

        citations = [
            NlCitation(type="alert", alert_id=alert.alert_id) for alert in alerts[:3]
        ]
        if intent == "alert_status":
            return alerts, citations
        return alerts, citations


def _filter_instance(filters: dict[str, str | list[str]]) -> str | None:
    value = filters.get("instanceId")
    if isinstance(value, str):
        return value
    return None


def _clarification(
    message: str, *, details: list[str] | None = None
) -> NlClarificationResponse:
    return NlClarificationResponse(
        message=message,
        supported_intents=list(CATALOGUE_INTENTS),
        details=details or [],
    )


def _slot_schema_json() -> str:
    schema = {
        "intent": list(CATALOGUE_INTENTS),
        "timeRange": {"last": "30m", "fromUtc": "ISO-8601", "toUtc": "ISO-8601"},
        "filters": {
            "application": "string",
            "instanceId": "string",
            "symbol": "string",
        },
        "groupBy": ["dimension"],
        "metrics": ["metric"],
        "series": False,
        "step": "1m",
    }
    return json.dumps(schema)
