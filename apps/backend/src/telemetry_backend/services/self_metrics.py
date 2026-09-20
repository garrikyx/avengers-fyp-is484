"""Backend self-metrics and warm-up state (UBS-96; FR-HLT-010, FR-QRY-005).

`SelfMetrics` owns a private Prometheus `CollectorRegistry` so nothing leaks
onto the process-global one and tests can build as many as they like. The
producers of most of these numbers (ingestion, dedupe, store, query) belong
to other tickets; each has a small typed method here so those components
record a number without knowing Prometheus exists. Until they call in, the
metric is present with value 0 - exposition must be stable from the first
scrape (a missing series looks like a broken exporter, a 0 looks like idle).

`WarmupTracker` is the process-level `/readyz` state: `warming` until
`warmupWindow` has elapsed since the first accepted *telemetry* ingest.
Heartbeats do not count - an agent saying hello is not data in the store,
and FR-QRY-005 exists precisely so an empty store is never read as "no
activity". See docs/plan/ubs69-96-notes.md.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from telemetry_backend.services.agent_registry import AgentRegistry

Clock = Callable[[], datetime]
ReadyState = Literal["warming", "ready"]

# Query latency SLO is p95 < 5s end to end (NFR-PERF-002) with a 3s server
# deadline (FR-QRY-014); buckets bracket that range.
_QUERY_LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0)


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True, frozen=True)
class WarmupStatus:
    state: ReadyState
    warmup_window_seconds: float
    since_first_ingest_seconds: float | None  # None until anything has arrived


class WarmupTracker:
    def __init__(self, window_seconds: float, clock: Clock | None = None) -> None:
        if window_seconds < 0:
            raise ValueError("window_seconds must be >= 0")
        self.window_seconds = window_seconds
        self._clock = clock or _utc_now
        self._first_ingest_at: datetime | None = None

    def mark_ingest(self, at: datetime | None = None) -> None:
        """Called by the ingestion path when a telemetry batch is accepted."""
        if self._first_ingest_at is None:
            self._first_ingest_at = at or self._clock()

    def status(self, at: datetime | None = None) -> WarmupStatus:
        at = at or self._clock()
        if self._first_ingest_at is None:
            return WarmupStatus("warming", self.window_seconds, None)
        elapsed = max(0.0, (at - self._first_ingest_at).total_seconds())
        state: ReadyState = "ready" if elapsed >= self.window_seconds else "warming"
        return WarmupStatus(state, self.window_seconds, elapsed)


class SelfMetrics:
    """Prometheus exposition for the backend's own internals (FR-HLT-010)."""

    def __init__(self, registry: AgentRegistry, clock: Clock | None = None) -> None:
        self._agent_registry = registry
        self._clock = clock or _utc_now
        self.registry = CollectorRegistry()
        # /metrics is a sync endpoint served from a threadpool; two overlapping
        # scrapes must not interleave clear()+labels() with generate_latest().
        self._scrape_lock = threading.Lock()
        ns = "telemetry_backend"

        # --- ingestion (UBS-66 / 85 / 87 call these) ---------------------------
        self.ingest_batches = Counter(
            f"{ns}_ingest_batches_total",
            "Telemetry batches accepted by the ingestion service",
            registry=self.registry,
        )
        self.ingest_validation_failures = Counter(
            f"{ns}_ingest_validation_failures_total",
            "Batches or items rejected by schema/allowlist validation (FR-ING-003/007)",
            registry=self.registry,
        )
        self.dedupe_hits = Counter(
            f"{ns}_ingest_dedupe_hits_total",
            "Batches dropped as duplicates by batchId (FR-ING-004)",
            registry=self.registry,
        )
        self.dropped_payloads = Counter(
            f"{ns}_dropped_payloads_total",
            "Payloads dropped after acceptance (too old, queue overflow) (FR-STM-005)",
            registry=self.registry,
        )
        self.heartbeats_received = Counter(
            f"{ns}_heartbeats_received_total",
            "Heartbeat documents recorded in the agent registry",
            registry=self.registry,
        )
        self.ingest_queue_depth = Gauge(
            f"{ns}_ingest_queue_depth",
            "Items waiting in the in-process ingest queue (FR-ING-009)",
            registry=self.registry,
        )

        # --- store (UBS-90 calls these) ----------------------------------------
        self.store_buckets = Gauge(
            f"{ns}_store_buckets",
            "Canonical buckets resident in the metric store",
            registry=self.registry,
        )
        self.store_memory_bytes = Gauge(
            f"{ns}_store_memory_bytes",
            "Estimated metric store memory use (FR-QRY-003)",
            registry=self.registry,
        )

        # --- query ----------------------------------------------------------------
        self.query_latency = Histogram(
            f"{ns}_query_latency_seconds",
            "Server-side latency of public API requests, by route template",
            ["route"],
            buckets=_QUERY_LATENCY_BUCKETS,
            registry=self.registry,
        )

        # --- agents (computed from the registry at scrape time) -------------------
        self.agents_known = Gauge(
            f"{ns}_agents_known",
            "Agents in the registry",
            registry=self.registry,
        )
        self.agents_stale = Gauge(
            f"{ns}_agents_stale",
            "Agents past missingHeartbeatThreshold",
            registry=self.registry,
        )
        self.agent_heartbeat_age = Gauge(
            f"{ns}_agent_heartbeat_age_seconds",
            "Seconds since the backend last received a heartbeat from the agent",
            ["agent_id"],
            registry=self.registry,
        )
        self.agent_stale = Gauge(
            f"{ns}_agent_stale",
            "1 if the agent is past missingHeartbeatThreshold, else 0",
            ["agent_id"],
            registry=self.registry,
        )
        self.warmup_state = Gauge(
            f"{ns}_warming_up",
            "1 while /readyz reports warming, else 0",
            registry=self.registry,
        )

    # --- refresh + expose ----------------------------------------------------------

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

    def exposition(self, warmup: WarmupTracker | None = None) -> tuple[bytes, str]:
        """(body, content-type) for `GET /metrics`."""
        with self._scrape_lock:
            self.refresh_agent_gauges()
            if warmup is not None:
                self.warmup_state.set(int(warmup.status().state == "warming"))
            return generate_latest(self.registry), CONTENT_TYPE_LATEST
