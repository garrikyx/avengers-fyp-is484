"""Compile interpreted NL slots into metrics query requests."""

from __future__ import annotations

from typing import Literal

from telemetry_shared.models.metrics_query import MetricsQueryRequest
from telemetry_shared.models.nl_query import InterpretedQuery, NlQueryContext
from telemetry_shared.query.aliases import API_DIMENSION_TO_STORED, is_known_metric

from telemetry_backend.config import NlConfig
from telemetry_backend.nl.catalogue import (
    INTENT_DEFINITIONS,
    build_default_filters,
    default_time_range,
)

_VALID_STEPS: frozenset[str] = frozenset({"10s", "1m", "5m"})


def merge_interpreted_query(
    *,
    intent: str,
    time_range: object | None,
    filters: dict[str, str | list[str]] | None,
    group_by: list[str] | None,
    metrics: list[str] | None,
    series: bool | None,
    step: str | None,
    percentiles: dict[str, list[int]] | None,
    context: NlQueryContext,
    config: NlConfig,
) -> InterpretedQuery:
    definition = INTENT_DEFINITIONS[intent]  # type: ignore[index]
    merged_filters = dict(build_default_filters(context))
    if filters:
        merged_filters.update(filters)
    merged_metrics = _merge_metrics(metrics, definition.metrics)
    merged_group_by = _merge_group_by(group_by, definition.group_by)
    merged_series = (
        definition.series
        if not definition.series
        else (series if series is not None else definition.series)
    )
    merged_step = _merge_step(step, definition.step)
    return InterpretedQuery(
        intent=intent,  # type: ignore[arg-type]
        time_range=time_range or default_time_range(config.default_time_range),  # type: ignore[arg-type]
        filters=merged_filters,
        group_by=merged_group_by,
        metrics=merged_metrics,
        series=merged_series,
        step=merged_step,  # type: ignore[arg-type]
        percentiles=percentiles if percentiles is not None else definition.percentiles,
    )


def _merge_metrics(metrics: list[str] | None, defaults: tuple[str, ...]) -> list[str]:
    if not metrics:
        return list(defaults)
    valid = [name for name in metrics if is_known_metric(name)]
    return valid or list(defaults)


def _merge_group_by(group_by: list[str] | None, defaults: tuple[str, ...]) -> list[str]:
    if not group_by:
        return list(defaults)
    valid = [dim for dim in group_by if dim in API_DIMENSION_TO_STORED]
    return valid or list(defaults)


def _merge_step(step: str | None, default: str) -> Literal["10s", "1m", "5m"]:
    if step in _VALID_STEPS:
        return step  # type: ignore[return-value]
    return default  # type: ignore[return-value]


def to_metrics_query(interpreted: InterpretedQuery) -> MetricsQueryRequest:
    return MetricsQueryRequest(
        time_range=interpreted.time_range,
        filters=interpreted.filters,
        group_by=interpreted.group_by,
        metrics=interpreted.metrics,
        percentiles=interpreted.percentiles,
        top_k=interpreted.top_k,
        series=interpreted.series,
        step=interpreted.step,
    )
