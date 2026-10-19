"""Deterministic rule-first intent matcher (FR-NLQ-006)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from telemetry_shared.models.nl_query import IntentId, NlQueryContext

from telemetry_backend.config import NlConfig
from telemetry_backend.nl.catalogue import INTENT_DEFINITIONS, build_default_filters
from telemetry_backend.nl.time import parse_time_expression

HIGH_CONFIDENCE = 0.85

_INSTANCE_RE = re.compile(
    r"\b(magic[-\w]+|instance[-\s]+[\w-]+)\b", re.IGNORECASE
)
_SYMBOL_RE = re.compile(
    r"\b(?:symbol|on|for)\s+([A-Z]{1,8})\b|\b([A-Z]{2,8})\b"
)
_SESSION_RE = re.compile(r"\bsession\s+([\w:>-]+)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class RuleMatchResult:
    intent: IntentId
    confidence: float
    time_range: object
    filters: dict[str, str | list[str]]
    group_by: list[str]
    metrics: list[str]
    series: bool
    step: str
    percentiles: dict[str, list[int]] | None
    time_caveats: tuple[str, ...]
    explicit_time: bool


@dataclass(frozen=True, slots=True)
class _IntentPattern:
    intent: IntentId
    strong: tuple[re.Pattern[str], ...]
    weak: tuple[re.Pattern[str], ...]
    priority: int = 0


_PATTERNS: tuple[_IntentPattern, ...] = (
    _IntentPattern(
        "symbol_drilldown",
        (
            re.compile(r"what(?:'s| is) rejecting on", re.I),
            re.compile(r"reject(?:s|ing)? (?:on|for) symbol", re.I),
        ),
        (re.compile(r"symbol drilldown", re.I),),
        priority=10,
    ),
    _IntentPattern(
        "rejection_summary",
        (
            re.compile(r"why are .* reject", re.I),
            re.compile(r"orders rejecting", re.I),
            re.compile(r"reject rate", re.I),
            re.compile(r"why .* reject", re.I),
        ),
        (re.compile(r"rejections?", re.I),),
        priority=5,
    ),
    _IntentPattern(
        "order_flow_summary",
        (
            re.compile(r"how is magic doing", re.I),
            re.compile(r"order flow", re.I),
        ),
        (re.compile(r"how .* doing today", re.I),),
    ),
    _IntentPattern(
        "latency_summary",
        (
            re.compile(r"is magic slow", re.I),
            re.compile(r"ack latency", re.I),
            re.compile(r"latency summary", re.I),
        ),
        (re.compile(r"\bslow\b", re.I),),
    ),
    _IntentPattern(
        "alert_status",
        (
            re.compile(r"any alerts", re.I),
            re.compile(r"active alerts", re.I),
            re.compile(r"alerts open", re.I),
        ),
        (re.compile(r"\balerts\b", re.I),),
    ),
    _IntentPattern(
        "session_status",
        (
            re.compile(r"fix sessions? up", re.I),
            re.compile(r"session status", re.I),
            re.compile(r"sessions? up", re.I),
        ),
        (re.compile(r"logon|logouts?", re.I),),
    ),
    _IntentPattern(
        "agent_health",
        (
            re.compile(r"telemetry actually working", re.I),
            re.compile(r"agent health", re.I),
        ),
        (re.compile(r"is telemetry", re.I),),
    ),
    _IntentPattern(
        "parse_health",
        (
            re.compile(r"failing to parse", re.I),
            re.compile(r"parse error", re.I),
            re.compile(r"parse health", re.I),
        ),
        (re.compile(r"parse", re.I),),
    ),
    _IntentPattern(
        "compare_period",
        (
            re.compile(r"worse than yesterday", re.I),
            re.compile(r"compare .* yesterday", re.I),
            re.compile(r"compare period", re.I),
        ),
        (re.compile(r"compared to", re.I),),
    ),
    _IntentPattern(
        "trend",
        (
            re.compile(r"show rejects over", re.I),
            re.compile(r"reject trend", re.I),
            re.compile(r"over the last hour", re.I),
        ),
        (re.compile(r"\btrend\b", re.I),),
    ),
)


def match_rules(
    question: str,
    *,
    context: NlQueryContext,
    config: NlConfig,
    now: object,
    max_range_seconds: int,
) -> RuleMatchResult | None:
    best_intent: IntentId | None = None
    best_score = 0.0
    best_priority = -1

    for pattern in _PATTERNS:
        score = _score_patterns(question, pattern.strong, pattern.weak)
        if score <= 0:
            continue
        if score > best_score or (
            score == best_score and pattern.priority > best_priority
        ):
            best_intent = pattern.intent
            best_score = score
            best_priority = pattern.priority

    if best_intent is None:
        return None

    definition = INTENT_DEFINITIONS[best_intent]
    time_result = parse_time_expression(
        question,
        now=now,  # type: ignore[arg-type]
        timezone_name=context.user_timezone,
        default_last=config.default_time_range,
        max_range_seconds=max_range_seconds,
    )
    filters: dict[str, str | list[str]] = dict(build_default_filters(context))
    filters.update(_extract_filters(question, context))

    if best_intent == "symbol_drilldown" and "symbol" not in filters:
        symbol = _extract_symbol(question)
        if symbol is None:
            return None
        filters["symbol"] = symbol

    confidence = min(1.0, best_score)
    if time_result.explicit:
        confidence = min(1.0, confidence + 0.05)
    elif confidence < 0.9:
        confidence = min(0.84, confidence)

    if confidence < HIGH_CONFIDENCE:
        return None

    return RuleMatchResult(
        intent=best_intent,
        confidence=confidence,
        time_range=time_result.time_range,
        filters=filters,
        group_by=list(definition.group_by),
        metrics=list(definition.metrics),
        series=definition.series,
        step=definition.step,
        percentiles=definition.percentiles,
        time_caveats=time_result.caveats,
        explicit_time=time_result.explicit,
    )


def _score_patterns(
    text: str, strong: tuple[re.Pattern[str], ...], weak: tuple[re.Pattern[str], ...]
) -> float:
    for pattern in strong:
        if pattern.search(text):
            return 0.92
    for pattern in weak:
        if pattern.search(text):
            return 0.78
    return 0.0


def _extract_filters(
    text: str, context: NlQueryContext
) -> dict[str, str | list[str]]:
    filters: dict[str, str | list[str]] = {}
    instance = _extract_instance(text)
    if instance is not None:
        filters["instanceId"] = instance
    session = _SESSION_RE.search(text)
    if session:
        filters["session"] = session.group(1)
    symbol = _extract_symbol(text)
    if symbol is not None:
        filters["symbol"] = symbol
    if "magic" in text.lower() and "application" not in filters:
        filters.setdefault("application", context.default_application)
    return filters


def _extract_instance(text: str) -> str | None:
    match = _INSTANCE_RE.search(text)
    if not match:
        return None
    value = match.group(1).replace("instance ", "").replace("instance-", "")
    if value.lower().startswith("magic"):
        return value.lower().replace(" ", "-")
    return value


def _extract_symbol(text: str) -> str | None:
    for match in _SYMBOL_RE.finditer(text):
        symbol = match.group(1) or match.group(2)
        if symbol and symbol.upper() not in {"MAGIC", "FIX", "SHOW", "LAST", "HOUR"}:
            return symbol.upper()
    return None


def rule_match_to_interpreted(
    match: RuleMatchResult,
) -> tuple[dict[str, object], tuple[str, ...]]:
    payload = {
        "intent": match.intent,
        "time_range": match.time_range,
        "filters": match.filters,
        "group_by": match.group_by,
        "metrics": match.metrics,
        "series": match.series,
        "step": match.step,
        "percentiles": match.percentiles,
    }
    return payload, match.time_caveats
