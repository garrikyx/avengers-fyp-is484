"""Query alias tables shared by the backend Query Engine and NL adapter."""

from telemetry_shared.query.aliases import (
    API_DIMENSION_TO_STORED,
    DERIVED_METRICS,
    METRIC_ALIASES,
    STORED_TO_API_DIMENSION,
    resolve_dimension_name,
    resolve_metric_name,
    to_api_dimension,
)

__all__ = [
    "API_DIMENSION_TO_STORED",
    "DERIVED_METRICS",
    "METRIC_ALIASES",
    "STORED_TO_API_DIMENSION",
    "resolve_dimension_name",
    "resolve_metric_name",
    "to_api_dimension",
]
