"""Shared service instances the routers reach through `request.app.state`.

One `AppDeps` is built in `main.py` (or a test) and attached to both the
public and the internal FastAPI app, so every router sees the same registry,
self-metrics, ingestion service and clock. Routers take
`deps: AppDeps = Depends(get_deps)`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fastapi import Request

from telemetry_backend.config import AlertingConfig, BackendHealthConfig
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.heartbeat_monitor import HeartbeatMonitor
from telemetry_backend.services.ingest_guard import IngestGuard
from telemetry_backend.services.ingestion import IngestionService
from telemetry_backend.services.self_metrics import SelfMetrics

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class AppDeps:
    config: BackendHealthConfig = field(default_factory=BackendHealthConfig)
    clock: Clock = _utc_now
    registry: AgentRegistry = field(init=False)
    alert_store: AlertStore = field(default_factory=AlertStore)
    heartbeat_monitor: HeartbeatMonitor = field(init=False)
    self_metrics: SelfMetrics = field(init=False)  # UBS-96
    ingest_guard: IngestGuard = field(init=False)  # UBS-85
    # Set by `main.create_app`, so the internal app's `/readyz` and
    # `/metrics` read the same ingestion service and store the public app
    # writes to.
    ingestion: IngestionService | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.registry = AgentRegistry(
            missing_threshold_seconds=self.config.missing_heartbeat_threshold_seconds,
            clock=self.clock,
        )
        self.ingest_guard = IngestGuard(self.config.ingest, clock=self.clock)
        self.self_metrics = SelfMetrics(
            self.registry, clock=self.clock, ingestion=lambda: self.ingestion
        )
        self.heartbeat_monitor = HeartbeatMonitor(
            registry=self.registry,
            alert_store=self.alert_store,
            config=AlertingConfig(
                missing_heartbeat_threshold_seconds=int(
                    self.config.missing_heartbeat_threshold_seconds
                ),
            ),
            now_fn=self.clock,
        )


def get_deps(request: Request) -> AppDeps:
    deps = getattr(request.app.state, "deps", None)
    if not isinstance(deps, AppDeps):
        raise RuntimeError("app.state.deps is not set; build the app via create_*_app")
    return deps
