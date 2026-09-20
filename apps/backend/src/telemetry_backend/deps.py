"""Shared service instances the routers reach through `request.app.state`.

One `AppDeps` is built in `main.py` (or a test) and attached to both the
public and the internal FastAPI app, so every router sees the same registry,
self-metrics, warm-up state and clock. Routers take
`deps: AppDeps = Depends(get_deps)`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fastapi import Request

from telemetry_backend.config import BackendHealthConfig
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.self_metrics import SelfMetrics, WarmupTracker

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class AppDeps:
    config: BackendHealthConfig = field(default_factory=BackendHealthConfig)
    clock: Clock = _utc_now
    registry: AgentRegistry = field(init=False)
    self_metrics: SelfMetrics = field(init=False)  # UBS-96
    warmup: WarmupTracker = field(init=False)  # UBS-96, FR-QRY-005

    def __post_init__(self) -> None:
        self.registry = AgentRegistry(
            missing_threshold_seconds=self.config.missing_heartbeat_threshold_seconds,
            clock=self.clock,
        )
        self.self_metrics = SelfMetrics(self.registry, clock=self.clock)
        self.warmup = WarmupTracker(self.config.warmup_window_seconds, clock=self.clock)


def get_deps(request: Request) -> AppDeps:
    deps = getattr(request.app.state, "deps", None)
    if not isinstance(deps, AppDeps):
        raise RuntimeError("app.state.deps is not set; build the app via create_*_app")
    return deps
