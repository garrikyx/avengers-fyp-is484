"""Backend self-metrics (UBS-96; FR-HLT-010, spec 006 s7).

`SelfMetrics` owns a private Prometheus `CollectorRegistry` so nothing leaks
onto the process-global one and tests can build as many as they like.

Two kinds of number live here:

- Counters this module owns and the routes increment directly: batches
  accepted, heartbeats recorded, dedupe hits (UBS-85 increments that one).
- Numbers other components already keep - ingestion's rejection and
  queue-full totals and queue depth, the stream processor's readiness and
  too-old drops, the store's memory estimate and drop totals. They are
  *read* at scrape time from those components' public attributes, so the
  owners' code does not change and there is no second copy to drift.

Every series is present from the first scrape, at 0 until its producer is
bound: a missing series looks like a broken exporter, a 0 looks like idle.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily, Metric
from prometheus_client.registry import Collector

from telemetry_backend.services.agent_registry import AgentRegistry

if TYPE_CHECKING:
    from telemetry_backend.services.ingestion import IngestionService

Clock = Callable[[], datetime]
IngestionSource = Callable[[], "IngestionService | None"]

_NS = "telemetry_backend"

# Query latency SLO is p95 < 5s end to end (NFR-PERF-002) with a 3s server
# deadline (FR-QRY-014); buckets bracket that range.
_QUERY_LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class _BoundSourcesCollector(Collector):
    """Reads ingestion / stream processor / store state at scrape time."""

    def __init__(self, ingestion: IngestionSource, clock: Clock) -> None:
        self._ingestion = ingestion
        self._clock = clock

    def collect(self) -> Iterator[Metric]:
        ingestion = self._ingestion()
        processor = ingestion.stream_processor if ingestion is not None else None
        store = processor.store if processor is not None else None

        yield _counter(
            "ingest_validation_failures",
            "Payloads rejected by schema validation (FR-ING-003)",
            ingestion.rejected_payloads_total if ingestion else 0,
        )
        yield _counter(
            "ingest_queue_full",
            "Payloads refused with 503 because the ingest queue was full (FR-ING-009)",
            ingestion.queue_overflow_total if ingestion else 0,
        )
        yield _gauge(
            "ingest_queue_depth",
            "Items waiting in the in-process ingest queue (FR-ING-009)",
            ingestion.queue_depth if ingestion else 0,
        )

        dropped = CounterMetricFamily(
            f"{_NS}_dropped_payloads",
            "Accepted data discarded downstream of ingestion, by reason (FR-STM-005)",
            labels=["reason"],
        )
        dropped.add_metric(
            ["bucket_too_old"], processor.dropped_buckets_total if processor else 0
        )
        dropped.add_metric(
            ["after_retention"], store.dropped_after_retention_total if store else 0
        )
        dropped.add_metric(
            ["series_over_cap"], store.dropped_series_over_cap_total if store else 0
        )
        yield dropped

        yield _gauge(
            "store_memory_bytes",
            "Estimated metric store memory use (FR-QRY-003)",
            store.estimated_memory_bytes() if store else 0,
        )
        # Same check `/readyz` makes, so the gauge and the probe never disagree.
        warming = processor is None or not processor.is_ready(now=self._clock())
        yield _gauge(
            "warming_up", "1 while /readyz reports warming, else 0", int(warming)
        )


def _counter(name: str, doc: str, value: float) -> CounterMetricFamily:
    return CounterMetricFamily(f"{_NS}_{name}", doc, value=value)


def _gauge(name: str, doc: str, value: float) -> GaugeMetricFamily:
    return GaugeMetricFamily(f"{_NS}_{name}", doc, value=value)


class SelfMetrics:
    """Prometheus exposition for the backend's own internals (FR-HLT-010)."""

    def __init__(
        self,
        registry: AgentRegistry,
        clock: Clock | None = None,
        ingestion: IngestionSource | None = None,
    ) -> None:
        self._agent_registry = registry
        self._clock = clock or _utc_now
        self.registry = CollectorRegistry()
        # /metrics is a sync endpoint served from a threadpool; two overlapping
        # scrapes must not interleave clear()+labels() with generate_latest().
        self._scrape_lock = threading.Lock()

        # --- owned here, incremented by the routes -----------------------------
        self.ingest_batches = Counter(
            f"{_NS}_ingest_batches_total",
            "Telemetry batches accepted by POST /telemetry/batch",
            registry=self.registry,
        )
        self.heartbeats_received = Counter(
            f"{_NS}_heartbeats_received_total",
            "Heartbeat documents recorded in the agent registry",
            registry=self.registry,
        )
        self.dedupe_hits = Counter(
            f"{_NS}_ingest_dedupe_hits_total",
            "Batches dropped as duplicates by batchId (FR-ING-004, UBS-85)",
            registry=self.registry,
        )
        self.query_latency = Histogram(
            f"{_NS}_query_latency_seconds",
            "Server-side latency of public API requests, by route template",
            ["route"],
            buckets=_QUERY_LATENCY_BUCKETS,
            registry=self.registry,
        )

        # --- agents (computed from the registry at scrape time) ----------------
        self.agents_known = Gauge(
            f"{_NS}_agents_known",
            "Agents in the registry",
            registry=self.registry,
        )
        self.agents_stale = Gauge(
            f"{_NS}_agents_stale",
            "Agents past missingHeartbeatThreshold",
            registry=self.registry,
        )
        self.agent_heartbeat_age = Gauge(
            f"{_NS}_agent_heartbeat_age_seconds",
            "Seconds since the backend last received a heartbeat from the agent",
            ["agent_id"],
            registry=self.registry,
        )
        self.agent_stale = Gauge(
            f"{_NS}_agent_stale",
            "1 if the agent is past missingHeartbeatThreshold, else 0",
            ["agent_id"],
            registry=self.registry,
        )

        # --- read from other components at scrape time --------------------------
        self.registry.register(
            _BoundSourcesCollector(ingestion or (lambda: None), self._clock)
        )

    def refresh_agent_gauges(self, at: datetime | None = None) -> None:
        """Recompute per-agent gauges from the registry. Called per scrape so
        the exporter never needs a background thread; label cardinality is
        bounded by the registry size (spec 010 `store.maxInstances`)."""
        at = at or self._clock()
        records = self._agent_registry.all()
        stale = 0
        # Rebuild the per-agent label sets from scratch so decommissioned
        # agents (registry.remove()) do not linger in the exposition.
        self.agent_heartbeat_age.clear()
        self.agent_stale.clear()
        for record in records:
            is_stale = self._agent_registry.is_stale(record, at)
            stale += int(is_stale)
            age_s = self._agent_registry.heartbeat_age_ms(record, at) / 1000
            self.agent_heartbeat_age.labels(agent_id=record.agent_id).set(age_s)
            self.agent_stale.labels(agent_id=record.agent_id).set(int(is_stale))
        self.agents_known.set(len(records))
        self.agents_stale.set(stale)

    def exposition(self) -> tuple[bytes, str]:
        """(body, content-type) for `GET /metrics`."""
        with self._scrape_lock:
            self.refresh_agent_gauges()
            return generate_latest(self.registry), CONTENT_TYPE_LATEST
