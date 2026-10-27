"""NL query orchestration (spec 008 §3)."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import ValidationError
from telemetry_shared.models.alerts_query import AlertRecord
from telemetry_shared.models.metrics_query import (
    MetricsQueryRequest,
    MetricsQueryResponse,
)
from telemetry_shared.models.nl_query import (
    ClarificationReason,
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
from telemetry_backend.nl.llm.protocol import (
    NO_INTENT,
    LlmSlotFiller,
    LlmSlotFillError,
    LlmUnavailableError,
    ManagedLlmSlotFiller,
)
from telemetry_backend.nl.normalize import normalize_question
from telemetry_backend.nl.render import RenderInput, render_answer
from telemetry_backend.nl.render.replies import (
    WEAK_RULE_MATCH_CAVEAT,
    greeting_message,
    help_message,
    llm_unavailable_message,
    out_of_scope_message,
    suggested_questions,
    thanks_message,
)
from telemetry_backend.nl.reply_guard import guard_reply
from telemetry_backend.nl.rule_matcher import (
    HIGH_CONFIDENCE,
    RuleMatchResult,
    match_rules,
    rule_match_to_interpreted,
)
from telemetry_backend.nl.smalltalk import SmallTalkKind, match_small_talk
from telemetry_backend.nl.time import baseline_time_range_before, parse_time_expression
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
        application = context.default_application
        small_talk = match_small_talk(normalized)
        if small_talk is not None:
            logger.info(
                "nl small talk user=%s kind=%s", user_id or "anonymous", small_talk
            )
            return _small_talk_outcome(small_talk, application)

        # A weak match is kept as the fallback when the LLM is unavailable
        # (FR-NLQ-021); only a high-confidence one skips the LLM (FR-NLQ-006).
        rule_match = match_rules(
            normalized,
            context=context,
            config=self._config,
            now=now,
            max_range_seconds=self._max_range_seconds,
            min_confidence=0.0,
        )

        source: Literal["rule", "llm"] = "rule"
        confidence = 0.0
        time_caveats: tuple[str, ...] = ()
        interpreted: InterpretedQuery | None = None

        if rule_match is not None and rule_match.confidence >= HIGH_CONFIDENCE:
            interpreted, time_caveats = self._rule_interpreted(rule_match, context)
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
            except (TimeoutError, LlmSlotFillError) as exc:
                unavailable = isinstance(exc, TimeoutError | LlmUnavailableError)
                logger.warning(
                    "nl llm fallback %s: %s",
                    "unavailable" if unavailable else "failed",
                    type(exc).__name__,
                )
                if rule_match is None:
                    return _no_interpretation_outcome(unavailable=unavailable)
                interpreted, time_caveats = self._rule_interpreted(rule_match, context)
                time_caveats = (*time_caveats, WEAK_RULE_MATCH_CAVEAT)
                confidence = rule_match.confidence
                source = "rule"
                llm_result = None

            if llm_result is not None:
                llm_intent = llm_result.intent
                if llm_intent == NO_INTENT:
                    return _conversational_outcome(llm_result.reply, application)
                llm_time_range = llm_result.time_range
                if llm_time_range is None:
                    time_from_question = parse_time_expression(
                        normalized,
                        now=now,
                        timezone_name=context.user_timezone,
                        default_last=self._config.default_time_range,
                        max_range_seconds=self._max_range_seconds,
                    )
                    if time_from_question.explicit:
                        llm_time_range = time_from_question.time_range
                        time_caveats = time_from_question.caveats
                try:
                    interpreted = merge_interpreted_query(
                        intent=llm_intent,
                        time_range=llm_time_range,
                        filters=llm_result.filters,
                        group_by=llm_result.group_by,
                        metrics=llm_result.metrics,
                        series=llm_result.series,
                        step=llm_result.step,
                        percentiles=llm_result.percentiles,
                        context=context,
                        config=self._config,
                    )
                except ValidationError as exc:
                    details = [
                        f"{err.get('loc', ('',))[0]}: {err.get('msg', 'invalid')}"
                        for err in exc.errors()
                    ]
                    return NlQueryOutcome(
                        kind="clarification",
                        answer=_clarification(
                            "The interpreted query was invalid. "
                            "Please clarify your question.",
                            details=details,
                        ),
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
                    validated.interpreted.filters.get(
                        "application", context.default_application
                    )
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

    def _rule_interpreted(
        self, rule_match: RuleMatchResult, context: NlQueryContext
    ) -> tuple[InterpretedQuery, tuple[str, ...]]:
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
        return interpreted, time_caveats

    async def warm_up(self) -> None:
        """Load the model before the first question (startup background task)."""
        if self._config.llm.warm_up and isinstance(self._llm, ManagedLlmSlotFiller):
            await self._llm.warm_up()

    async def aclose(self) -> None:
        if isinstance(self._llm, ManagedLlmSlotFiller):
            await self._llm.aclose()

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
    message: str,
    *,
    details: list[str] | None = None,
    reason: ClarificationReason = "clarify",
    suggestions: list[str] | None = None,
) -> NlClarificationResponse:
    return NlClarificationResponse(
        message=message,
        supported_intents=list(CATALOGUE_INTENTS),
        details=details or [],
        reason=reason,
        suggested_questions=(
            suggestions if suggestions is not None else suggested_questions()
        ),
    )


def _reply(message: str, reason: ClarificationReason) -> NlQueryOutcome:
    return NlQueryOutcome(
        kind="clarification", answer=_clarification(message, reason=reason)
    )


def _small_talk_outcome(kind: SmallTalkKind, application: str) -> NlQueryOutcome:
    if kind == "greeting":
        return _reply(greeting_message(application), "greeting")
    if kind == "thanks":
        return _reply(thanks_message(application), "greeting")
    return _reply(help_message(application), "help")


def _conversational_outcome(reply: str | None, application: str) -> NlQueryOutcome:
    """FR-NLQ-030: the model's own words only when the guard accepts them."""
    guarded = guard_reply(reply, application=application)
    return _reply(guarded or out_of_scope_message(application), "out_of_scope")


def _no_interpretation_outcome(*, unavailable: bool) -> NlQueryOutcome:
    if unavailable:
        return _reply(llm_unavailable_message(), "llm_unavailable")
    return _reply(
        "I could not map that question to a supported telemetry intent. "
        "Try one of these questions.",
        "clarify",
    )


def _slot_schema_json() -> str:
    schema = {
        "intent": list(CATALOGUE_INTENTS),
        "timeRange": {
            "exampleRelative": {"last": "15m"},
            "exampleAbsolute": {
                "fromUtc": "2026-06-12T00:00:00Z",
                "toUtc": "2026-06-12T01:00:00Z",
            },
        },
        "filters": {
            "example": {"application": "Magic", "instanceId": "magic-prod-01"},
        },
        "optionalSlotsNote": (
            "Omit groupBy, metrics, series, and step to use intent defaults "
            "from the catalogue; only set them when you must override."
        ),
        "latency_summaryExample": {
            "intent": "latency_summary",
            "timeRange": {"last": "15m"},
            "filters": {"application": "Magic"},
        },
    }
    return json.dumps(schema)
