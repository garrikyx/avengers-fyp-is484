"""Compile interpreted NL slots into metrics query requests."""

from __future__ import annotations

from telemetry_shared.models.metrics_query import MetricsQueryRequest
from telemetry_shared.models.nl_query import InterpretedQuery, NlQueryContext

from telemetry_backend.config import NlConfig
from telemetry_backend.nl.catalogue import (
    INTENT_DEFINITIONS,
    build_default_filters,
    default_time_range,
)


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
    return InterpretedQuery(
        intent=intent,  # type: ignore[arg-type]
        time_range=time_range or default_time_range(config.default_time_range),  # type: ignore[arg-type]
        filters=merged_filters,
        group_by=group_by if group_by is not None else list(definition.group_by),
        metrics=metrics if metrics is not None else list(definition.metrics),
        series=definition.series if series is None else series,
        step=(step or definition.step),  # type: ignore[arg-type]
        percentiles=percentiles if percentiles is not None else definition.percentiles,
    )


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
