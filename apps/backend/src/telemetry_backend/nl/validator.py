"""Validate interpreted queries against metrics API rules (FR-NLQ-002, FR-NLQ-008)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import ValidationError
from telemetry_shared.models.metrics_query import MetricsQueryRequest, QueryTimeRange
from telemetry_shared.models.nl_query import InterpretedQuery
from telemetry_shared.query.aliases import API_DIMENSION_TO_STORED, is_known_metric

from telemetry_backend.nl.catalogue import INTENT_DEFINITIONS, SUPPORTED_INTENTS
from telemetry_backend.nl.compiler import to_metrics_query
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.query_engine import QueryEngine, QueryValidationError


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    field: str
    issue: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    interpreted: InterpretedQuery
    metrics_request: MetricsQueryRequest
    caveats: tuple[str, ...]


def validate_interpreted_query(
    interpreted: InterpretedQuery,
    *,
    engine: QueryEngine,
    store: MetricStore,
    now: datetime,
) -> ValidationResult:
    issues = _schema_issues(interpreted)
    if issues:
        raise InterpretedValidationError(issues)

    clamped_range, clamp_caveats = _clamp_time_range(
        interpreted.time_range, store=store, now=now
    )
    if clamped_range is not interpreted.time_range:
        interpreted = interpreted.model_copy(update={"time_range": clamped_range})

    metrics_request = to_metrics_query(interpreted)
    try:
        engine.prepare_metrics_query(metrics_request, now=now)
    except QueryValidationError as exc:
        raise InterpretedValidationError(
            [ValidationIssue(field=exc.field, issue=exc.issue)]
        ) from exc
    return ValidationResult(
        interpreted=interpreted,
        metrics_request=metrics_request,
        caveats=tuple(clamp_caveats),
    )


class InterpretedValidationError(Exception):
    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__("interpreted query validation failed")


def _schema_issues(interpreted: InterpretedQuery) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if interpreted.intent not in SUPPORTED_INTENTS:
        issues.append(
            ValidationIssue("intent", f"unknown intent {interpreted.intent!r}")
        )
        return issues

    definition = INTENT_DEFINITIONS[interpreted.intent]
    if "symbol" in definition.required_slots and "symbol" not in interpreted.filters:
        issues.append(
            ValidationIssue(
                "filters.symbol", "symbol is required for this intent."
            )
        )

    for metric in interpreted.metrics:
        if not is_known_metric(metric):
            issues.append(ValidationIssue("metrics", f"unknown metric {metric!r}"))

    for dim in interpreted.group_by:
        if dim not in API_DIMENSION_TO_STORED:
            issues.append(ValidationIssue("groupBy", f"unknown dimension {dim!r}"))

    for key in interpreted.filters:
        if key in {"application", "instanceId", "instance_id"}:
            continue
        if key not in API_DIMENSION_TO_STORED:
            issues.append(ValidationIssue("filters", f"unknown dimension {key!r}"))

    try:
        QueryTimeRange.model_validate(interpreted.time_range.model_dump())
    except ValidationError as exc:
        for error in exc.errors():
            loc = ".".join(str(part) for part in error["loc"])
            issues.append(ValidationIssue(f"timeRange.{loc}", error["msg"]))

    return issues


def _clamp_time_range(
    time_range: QueryTimeRange, *, store: MetricStore, now: datetime
) -> tuple[QueryTimeRange, list[str]]:
    caveats: list[str] = []
    if time_range.last is not None:
        return time_range, caveats
    assert time_range.from_utc is not None and time_range.to_utc is not None
    oldest, newest = store.retention_bounds(now=now)
    if oldest is None or newest is None:
        return time_range, caveats

    from_utc = time_range.from_utc
    to_utc = time_range.to_utc
    changed = False
    if from_utc < oldest:
        from_utc = oldest
        changed = True
        caveats.append(
            "Clamped timeRange.fromUtc to retention window start "
            f"({oldest.isoformat()})."
        )
    if to_utc > newest:
        to_utc = newest
        changed = True
        caveats.append(
            f"Clamped timeRange.toUtc to retention window end ({newest.isoformat()})."
        )
    if not changed:
        return time_range, caveats
    return (
        QueryTimeRange(from_utc=from_utc, to_utc=to_utc),
        caveats,
    )
