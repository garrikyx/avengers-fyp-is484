"""Metrics Query Engine (spec 006 §5, UBS-68/91)."""

from __future__ import annotations

import asyncio
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_shared.metrics import (
    Histogram,
    build_latency_summary,
    compute_indicators,
)
from telemetry_shared.models.metrics import Indicators, LatencySummary, MetricsGroup
from telemetry_shared.models.metrics_query import (
    DataCompleteness,
    EffectiveTimeRange,
    MetricsQueryRequest,
    MetricsQueryResponse,
    QueryGroup,
    QueryInterpretation,
    SeriesPoint,
)
from telemetry_shared.query.aliases import (
    is_known_metric,
    resolve_dimension_name,
    resolve_metric_name,
    to_api_dimension,
)

from telemetry_backend.config import QueryConfig, StreamProcessorConfig
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.metric_store import MetricStore
from telemetry_backend.services.stream_processor import StreamProcessor

_RELATIVE_RE = re.compile(r"^(\d+)(s|m|h)$")

_DERIVED_TO_INDICATOR: dict[str, str] = {
    "rejectRate": "reject_rate",
    "reject_rate": "reject_rate",
    "fillRate": "fill_rate",
    "fill_rate": "fill_rate",
    "cancelRate": "cancel_rate",
    "cancel_rate": "cancel_rate",
    "parseErrorRate": "parse_error_rate",
    "parse_error_rate": "parse_error_rate",
    "throughput": "throughput",
}

DimKey = tuple[tuple[str, str], ...]


@dataclass(slots=True, frozen=True)
class QueryValidationError(Exception):
    code: str
    message: str
    field: str
    issue: str


@dataclass(slots=True, frozen=True)
class QueryTimeoutError(Exception):
    partial: MetricsQueryResponse | None = None


@dataclass
class _AccumulatedGroup:
    dimensions: dict[str, str] = field(default_factory=dict)
    counters: dict[str, Decimal] = field(default_factory=dict)
    histograms: dict[str, Histogram] = field(default_factory=dict)
    series_points: list[tuple[datetime, dict[str, int | float | None]]] = field(
        default_factory=list
    )


class QueryEngine:
    """Read-only metrics queries over the in-memory MetricStore."""

    def __init__(
        self,
        store: MetricStore,
        *,
        stream_processor: StreamProcessor,
        agent_registry: AgentRegistry | None = None,
        query_config: QueryConfig | None = None,
        stream_config: StreamProcessorConfig | None = None,
    ) -> None:
        self._store = store
        self._processor = stream_processor
        self._registry = agent_registry or AgentRegistry()
        self._query_config = query_config or QueryConfig()
        self._stream_config = stream_config or stream_processor._config

    async def query(
        self,
        request: MetricsQueryRequest,
        *,
        now: datetime | None = None,
        skip_fanout: bool = False,
        fanout_client: object | None = None,
    ) -> MetricsQueryResponse:
        now = now or datetime.now(UTC)
        if (
            not skip_fanout
            and self._query_config.query_mode == "fanout"
            and self._query_config.replica_registry
            and fanout_client is not None
        ):
            from telemetry_backend.services.replica_fanout import ReplicaFanout

            fanout = ReplicaFanout(
                local=self,
                config=self._query_config,
                client=fanout_client,
            )
            return await fanout.query(request, now=now)

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._execute_sync, request, now=now),
                timeout=self._query_config.query_timeout_seconds,
            )
        except TimeoutError as exc:
            raise QueryTimeoutError(partial=None) from exc

    def _execute_sync(
        self, request: MetricsQueryRequest, *, now: datetime
    ) -> MetricsQueryResponse:
        from_utc, to_utc = self._resolve_time_range(request, now=now)
        self._validate_clamps(request, from_utc=from_utc, to_utc=to_utc)
        self._validate_retention(from_utc=from_utc, to_utc=to_utc, now=now)
        self._validate_metrics_and_dimensions(request)

        stored_group_by = tuple(
            resolve_dimension_name(dim) for dim in request.group_by
        )
        resolved_metrics = self._resolve_requested_metrics(request.metrics)
        instance_ids = self._resolve_instances(request.filters, now=now)

        accumulated: dict[DimKey, _AccumulatedGroup] = {}
        merged_histograms: dict[str, Histogram] = {}
        reporting_agents: set[str] = set()
        restarted_buckets = 0

        for instance_id in instance_ids:
            reporting_agents.update(
                self._store.contributing_agent_ids(
                    instance_id, from_utc=from_utc, to_utc=to_utc
                )
            )
            restarted_buckets += self._store.restarted_bucket_count(
                instance_id, from_utc=from_utc, to_utc=to_utc
            )
            if request.series:
                steps = self._store.read_series(
                    instance_id,
                    from_utc=from_utc,
                    to_utc=to_utc,
                    step=request.step,
                    group_by=stored_group_by,
                )
                self._accumulate_series(
                    accumulated,
                    steps,
                    request=request,
                    group_by=stored_group_by,
                )
            for group in self._store.read(
                instance_id,
                from_utc=from_utc,
                to_utc=to_utc,
                group_by=stored_group_by,
            ):
                key: DimKey = tuple(sorted(group.dimensions.items()))
                self._accumulate_group(accumulated, key, group, merged_histograms)

        filtered = self._apply_dimension_filters(accumulated, request.filters)
        window_seconds = max((to_utc - from_utc).total_seconds(), 0.0)
        query_groups = [
            self._to_query_group(
                acc,
                request=request,
                window_seconds=window_seconds,
                include_series=request.series,
            )
            for acc in filtered.values()
        ]

        truncated = False
        if request.top_k is not None and len(query_groups) > request.top_k:
            query_groups, truncated = self._apply_top_k(
                query_groups, request.top_k, request.metrics
            )
        if len(query_groups) > self._query_config.max_groups:
            raise QueryValidationError(
                code="invalid_field",
                message="Query exceeds maxGroups.",
                field="groupBy",
                issue=(
                    f"group count {len(query_groups)} exceeds maxGroups "
                    f"{self._query_config.max_groups}"
                ),
            )

        totals = self._build_totals(filtered, request, window_seconds=window_seconds)
        latency = self._build_latency_summary(merged_histograms, request)
        data_completeness = self._build_data_completeness(
            reporting_agents=reporting_agents,
            restarted_buckets=restarted_buckets,
            now=now,
        )

        return MetricsQueryResponse(
            query_id=f"q-{uuid.uuid4().hex[:8]}",
            evaluated_at_utc=now,
            effective_time_range=EffectiveTimeRange(from_utc=from_utc, to_utc=to_utc),
            interpretation=QueryInterpretation(
                metrics=list(resolved_metrics),
                group_by=list(request.group_by),
                filters=dict(request.filters),
            ),
            totals=totals,
            latency=latency,
            groups=query_groups,
            truncated=truncated,
            data_completeness=data_completeness,
        )

    def _resolve_time_range(
        self, request: MetricsQueryRequest, *, now: datetime
    ) -> tuple[datetime, datetime]:
        tr = request.time_range
        if tr.last is not None:
            delta = self._parse_relative(tr.last)
            return now - delta, now
        assert tr.from_utc is not None and tr.to_utc is not None
        if tr.from_utc >= tr.to_utc:
            raise QueryValidationError(
                code="invalid_time_range",
                message="timeRange fromUtc must be before toUtc.",
                field="timeRange",
                issue="fromUtc is not before toUtc.",
            )
        return tr.from_utc, tr.to_utc

    @staticmethod
    def _parse_relative(value: str) -> timedelta:
        match = _RELATIVE_RE.match(value.strip())
        if not match:
            raise QueryValidationError(
                code="invalid_time_range",
                message="Invalid relative timeRange.last value.",
                field="timeRange.last",
                issue=f"cannot parse {value!r}",
            )
        amount = int(match.group(1))
        unit = match.group(2)
        if unit == "s":
            return timedelta(seconds=amount)
        if unit == "m":
            return timedelta(minutes=amount)
        return timedelta(hours=amount)

    def _validate_clamps(
        self,
        request: MetricsQueryRequest,
        *,
        from_utc: datetime,
        to_utc: datetime,
    ) -> None:
        range_seconds = (to_utc - from_utc).total_seconds()
        if range_seconds > self._query_config.max_range_seconds:
            raise QueryValidationError(
                code="invalid_time_range",
                message="timeRange exceeds the maximum queryable window.",
                field="timeRange",
                issue=(
                    f"range is {range_seconds:.0f}s; "
                    f"maxRangeSeconds is {self._query_config.max_range_seconds}"
                ),
            )
        if request.series:
            step_seconds = {"10s": 10, "1m": 60, "5m": 300}[request.step]
            points = int(range_seconds // step_seconds) + 1
            if points > self._query_config.max_series_points:
                raise QueryValidationError(
                    code="invalid_field",
                    message="Query exceeds maxSeriesPoints.",
                    field="step",
                    issue=(
                        f"series would contain {points} points; "
                        f"maxSeriesPoints is {self._query_config.max_series_points}"
                    ),
                )

    def _validate_retention(
        self, *, from_utc: datetime, to_utc: datetime, now: datetime
    ) -> None:
        oldest, newest = self._store.retention_bounds(now=now)
        if oldest is None or newest is None:
            return
        if to_utc < oldest or from_utc > newest:
            raise QueryValidationError(
                code="invalid_time_range",
                message="Requested time range is outside the retention window.",
                field="timeRange",
                issue=(
                    f"available range is {oldest.isoformat()} to "
                    f"{newest.isoformat()}"
                ),
            )

    def _validate_metrics_and_dimensions(self, request: MetricsQueryRequest) -> None:
        for metric in request.metrics:
            if not is_known_metric(metric):
                raise QueryValidationError(
                    code="unknown_metric",
                    message="Unknown metric requested.",
                    field="metrics",
                    issue=f"unknown metric {metric!r}",
                )

    def _resolve_requested_metrics(self, metrics: list[str]) -> list[str]:
        resolved: list[str] = []
        for name in metrics:
            canonical = resolve_metric_name(name)
            resolved.append(canonical if canonical is not None else name)
        return resolved

    def _resolve_instances(
        self, filters: dict[str, str | list[str]], *, now: datetime
    ) -> list[str]:
        all_instances = self._store.list_instance_ids(now=now)
        apps = self._store.instance_applications

        instance_filter = filters.get("instanceId") or filters.get("instance_id")
        if isinstance(instance_filter, list):
            instance_filter = instance_filter[0] if instance_filter else None

        app_filter = filters.get("application")
        if isinstance(app_filter, list):
            app_filter = app_filter[0] if app_filter else None

        if instance_filter:
            return [str(instance_filter)]

        if app_filter:
            return [
                instance_id
                for instance_id in all_instances
                if apps.get(instance_id) == app_filter
            ]

        return all_instances

    def _accumulate_group(
        self,
        accumulated: dict[DimKey, _AccumulatedGroup],
        key: DimKey,
        group: MetricsGroup,
        merged_histograms: dict[str, Histogram],
    ) -> None:
        acc = accumulated.setdefault(
            key, _AccumulatedGroup(dimensions=dict(group.dimensions))
        )
        for metric, value in group.counters.items():
            acc.counters[metric] = acc.counters.get(metric, Decimal(0)) + value
        for metric, summary in group.latency.items():
            hist = merged_histograms.setdefault(metric, Histogram())
            if summary.count > 0 and summary.avg is not None:
                hist.count += summary.count
                hist.sum_ms += Decimal(str(summary.avg * summary.count))

    def _accumulate_series(
        self,
        accumulated: dict[DimKey, _AccumulatedGroup],
        steps: list[tuple[datetime, list[MetricsGroup]]],
        *,
        request: MetricsQueryRequest,
        group_by: tuple[str, ...],
    ) -> None:
        for ts, groups in steps:
            if not group_by:
                key: DimKey = ()
                acc = accumulated.setdefault(key, _AccumulatedGroup())
                if groups:
                    values = self._metric_values_from_group(groups[0], request.metrics)
                else:
                    values = {name: None for name in request.metrics}
                acc.series_points.append((ts, values))
                continue

            present: set[DimKey] = set()
            for group in groups:
                key = tuple(sorted(group.dimensions.items()))
                present.add(key)
                acc = accumulated.setdefault(
                    key, _AccumulatedGroup(dimensions=dict(group.dimensions))
                )
                acc.series_points.append(
                    (ts, self._metric_values_from_group(group, request.metrics))
                )
            for key, acc in accumulated.items():
                if key and key not in present:
                    nulls = {name: None for name in request.metrics}
                    acc.series_points.append((ts, nulls))

    def _metric_values_from_group(
        self, group: MetricsGroup, metrics: list[str]
    ) -> dict[str, int | float | None]:
        values: dict[str, int | float | None] = {}
        for name in metrics:
            canonical = resolve_metric_name(name)
            if canonical and canonical in group.counters:
                value = group.counters[canonical]
                values[name] = (
                    int(value) if value == value.to_integral_value() else float(value)
                )
            elif name in _DERIVED_TO_INDICATOR:
                ind_key = _DERIVED_TO_INDICATOR[name]
                if ind_key == "throughput":
                    values[name] = group.indicators.throughput
                else:
                    values[name] = getattr(group.indicators, ind_key).value
        return values

    def _apply_dimension_filters(
        self,
        groups: dict[DimKey, _AccumulatedGroup],
        filters: dict[str, str | list[str]],
    ) -> dict[DimKey, _AccumulatedGroup]:
        dimension_filters: dict[str, str | list[str]] = {}
        for key, value in filters.items():
            if key in ("application", "instanceId", "instance_id"):
                continue
            dimension_filters[resolve_dimension_name(key)] = value

        if not dimension_filters:
            return groups

        return {
            key: group
            for key, group in groups.items()
            if self._matches_filters(group.dimensions, dimension_filters)
        }

    @staticmethod
    def _matches_filters(
        dimensions: dict[str, str],
        filters: dict[str, str | list[str]],
    ) -> bool:
        for dim, expected in filters.items():
            actual = dimensions.get(dim)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    def _to_query_group(
        self,
        acc: _AccumulatedGroup,
        *,
        request: MetricsQueryRequest,
        window_seconds: float,
        include_series: bool,
    ) -> QueryGroup:
        indicators = compute_indicators(
            acc.counters,
            min_sample_size=self._stream_config.min_sample_size,
            window_seconds=window_seconds,
        )
        api_dims = {to_api_dimension(k): v for k, v in acc.dimensions.items()}
        points: list[SeriesPoint] | None = None
        if include_series and acc.series_points:
            points = [
                SeriesPoint(ts_utc=ts, values=values)
                for ts, values in acc.series_points
            ]
        return QueryGroup(
            dimensions=api_dims,
            counters=self._select_counters(acc.counters, request.metrics),
            indicators=self._select_indicators(indicators, request.metrics),
            points=points,
        )

    def _select_counters(
        self, counters: dict[str, Decimal], metrics: list[str]
    ) -> dict[str, int | float]:
        selected: dict[str, int | float] = {}
        for name in metrics:
            canonical = resolve_metric_name(name)
            if canonical is None or canonical not in counters:
                continue
            value = counters[canonical]
            selected[name] = (
                int(value) if value == value.to_integral_value() else float(value)
            )
        return selected

    @staticmethod
    def _select_indicators(
        indicators: Indicators, metrics: list[str]
    ) -> dict[str, float | None]:
        selected: dict[str, float | None] = {}
        for name in metrics:
            ind_key = _DERIVED_TO_INDICATOR.get(name)
            if ind_key is None:
                continue
            if ind_key == "throughput":
                selected[name] = indicators.throughput
            else:
                selected[name] = getattr(indicators, ind_key).value
        return selected

    def _build_totals(
        self,
        groups: dict[DimKey, _AccumulatedGroup],
        request: MetricsQueryRequest,
        *,
        window_seconds: float,
    ) -> dict[str, int | float | None]:
        totals_counters: dict[str, Decimal] = {}
        for group in groups.values():
            for metric, value in group.counters.items():
                prev = totals_counters.get(metric, Decimal(0))
                totals_counters[metric] = prev + value
        indicators = compute_indicators(
            totals_counters,
            min_sample_size=self._stream_config.min_sample_size,
            window_seconds=window_seconds,
        )
        result: dict[str, int | float | None] = {}
        result.update(self._select_counters(totals_counters, request.metrics))
        result.update(self._select_indicators(indicators, request.metrics))
        return result

    def _build_latency_summary(
        self,
        histograms: dict[str, Histogram],
        request: MetricsQueryRequest,
    ) -> dict[str, LatencySummary]:
        if not request.percentiles:
            return {}
        result: dict[str, LatencySummary] = {}
        for metric, requested in request.percentiles.items():
            hist = histograms.get(metric)
            if hist is None:
                continue
            result[metric] = build_latency_summary(
                hist,
                percentiles=tuple(requested),
                min_sample_size=self._stream_config.min_sample_size,
            )
        return result

    def _apply_top_k(
        self,
        groups: list[QueryGroup],
        top_k: int,
        metrics: list[str],
    ) -> tuple[list[QueryGroup], bool]:
        sort_metric = resolve_metric_name(metrics[0]) or metrics[0]

        def sort_key(group: QueryGroup) -> float:
            if sort_metric in group.counters:
                return float(group.counters[sort_metric])
            return float(group.indicators.get(metrics[0]) or 0)

        ranked = sorted(groups, key=sort_key, reverse=True)
        top = ranked[:top_k]
        rest = ranked[top_k:]
        if not rest:
            return top, False

        other_counters: dict[str, float] = {}
        for group in rest:
            for metric, value in group.counters.items():
                other_counters[metric] = other_counters.get(metric, 0) + value
        other_dim = "rejectReason" if any(
            g.dimensions.get("rejectReason") for g in groups
        ) else "__other__"
        top.append(
            QueryGroup(
                dimensions={other_dim: "__other__"},
                counters=other_counters,
            )
        )
        return top, True

    def _build_data_completeness(
        self,
        *,
        reporting_agents: set[str],
        restarted_buckets: int,
        now: datetime,
        failed_peers: list[str] | None = None,
        partial: bool = False,
    ) -> DataCompleteness:
        expected_ids = self._registry.all_agent_ids()
        stale_records = self._registry.agents_exceeding_threshold(
            self._query_config.missing_heartbeat_threshold_seconds, now=now
        )
        stale_agents = [record.agent_id for record in stale_records]
        confidence: str = "complete"
        if stale_agents or restarted_buckets > 0 or partial or failed_peers:
            confidence = "partial"
        if not reporting_agents and expected_ids:
            confidence = "degraded"
        return DataCompleteness(
            agents_expected=len(expected_ids) or len(reporting_agents),
            agents_reporting=len(reporting_agents),
            stale_agents=stale_agents,
            restarted_buckets=restarted_buckets,
            dropped_batches_reported=self._processor.dropped_buckets_total,
            confidence=confidence,  # type: ignore[arg-type]
            failed_peers=failed_peers or [],
        )
