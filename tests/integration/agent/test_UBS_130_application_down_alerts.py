"""UBS-130 integration: Host Monitor (stubbed process list) -> RuleEvaluator
running the shipped config/rules.yaml -> AlertRouter, and -> SnapshotEmitter.

Covers FR-HLT-014, FR-MET-034 and the ticket's done-when:
  * a missing process fires `ApplicationDown` (critical) and its return resolves it;
  * an empty `process.name` reports no gauge and fires nothing.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import CallbackResult
from telemetry_agent.config import host_rule_filter, load_agent_config
from telemetry_agent.health.host_monitor import HostConfig, HostMonitor
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.pipeline.evaluator import RuleEvaluator
from telemetry_agent.pipeline.ingest import MetricsIngestor
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import PublishResult
from telemetry_agent.publishing.snapshot_bridge import SnapshotEmitter
from telemetry_agent.rules.config_loader import load_rules
from telemetry_agent.rules.engine import RuleEngine
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.ingestion import TelemetryBatch
from telemetry_shared.models.snapshot import Snapshot

_REPO_ROOT = Path(__file__).resolve().parents[3]
_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_APP = "Magic"
_MAGIC = "magic.exe"


class _Sampler:
    def __init__(self) -> None:
        self.names: list[str] | Exception = ["sshd", _MAGIC]

    def disk_used_ratio(self, path: str) -> float:
        return 0.40

    def memory_used_ratio(self) -> float:
        return 0.50

    def own_usage(self) -> tuple[float, float]:
        return 84.0, 1.8

    def process_running(self, name: str) -> bool:
        if isinstance(self.names, Exception):
            raise self.names
        return name in set(self.names)


class _NullCallbackSink:
    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> CallbackResult:
        return CallbackResult(status_code=200, latency_ms=1.0)


class _CapturingSink:
    def __init__(self) -> None:
        self.batches: list[TelemetryBatch] = []

    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> PublishResult:
        self.batches.append(TelemetryBatch.model_validate_json(body))
        return PublishResult(status_code=202, latency_ms=1.0)


class _Agent:
    def __init__(self, process_name: str = _MAGIC) -> None:
        cfg = load_agent_config(_REPO_ROOT / "config" / "agent.yaml")
        self.now = _T0
        self.sampler = _Sampler()
        host = HostConfig(disk_paths=("/data",), process_name=process_name)
        self.monitor = HostMonitor(host, self.sampler)
        self.ingestor = MetricsIngestor.build_default(
            clock=lambda: self.now.timestamp(), monotonic=lambda: 0.0
        )
        self.sink = _CapturingSink()
        self.publisher = BackendPublisher(
            self.sink,
            parse_publish_config({"endpoint": "https://backend.example/batch"}),
            agent_id=cfg.agent_id,
            application=_APP,
        )
        dispatcher = CallbackDispatcher(
            _NullCallbackSink(),
            parse_callbacks_config({"endpoint": "https://magic.example/cb"}),
            b"secret",
        )
        # The shipped rules, filtered as build_agent does for this host block.
        rules = load_rules(
            _REPO_ROOT / "config" / "rules.yaml", keep=host_rule_filter(host)
        )
        engine = RuleEngine(
            rules,
            instance_id=cfg.instance_id,
            application=_APP,
            agent_id=cfg.agent_id,
            started_at=_T0 - timedelta(hours=1),
        )
        self.emitter = SnapshotEmitter(
            self.ingestor.aggregator,
            self.publisher,
            bucket_seconds=cfg.publish.metrics_bucket_seconds,
            agent_id=cfg.agent_id,
            application=_APP,
            instance_id=cfg.instance_id,
            host_gauges=self.monitor.gauges,
        )
        self.evaluator = RuleEvaluator(
            engine,
            self.ingestor.aggregator,
            AlertRouter(
                self.publisher,
                agent_id=cfg.agent_id,
                application=_APP,
                dispatcher=dispatcher,
            ),
            instance_id=cfg.instance_id,
            correlator=self.ingestor.correlator,
            session_tracker=self.ingestor.session_tracker,
            publisher=self.publisher,
            dispatcher=dispatcher,
            clock=lambda: self.now,
            monotonic=lambda: 0.0,
            lock=self.ingestor.lock,
            host_gauges=self.monitor.gauges,
            host_counters=self.monitor.counters,
        )

    def published_snapshots(self) -> list[Snapshot]:
        while self.publisher.queue_depth():
            asyncio.run(self.publisher.publish_once(now=self.now))
        return [snap for batch in self.sink.batches for snap in batch.snapshots]

    def tick(self, advance: float = 1.0) -> list[tuple[str, str, str]]:
        self.now += timedelta(seconds=advance)
        self.monitor.sample_once()
        return _down_alerts(self.evaluator.evaluate_once())


def _down_alerts(alerts: list[AlertEvent]) -> list[tuple[str, str, str]]:
    return [
        (a.rule_name, a.severity, a.status)
        for a in alerts
        if a.rule_name == "ApplicationDown"
    ]


def test_fr_hlt_014_missing_process_fires_application_down_critical() -> None:
    agent = _Agent()
    agent.sampler.names = ["sshd"]

    assert agent.tick() == []  # pending: the 30s hold has not elapsed
    assert agent.tick(29) == []
    assert agent.tick(1) == [("ApplicationDown", "critical", "firing")]


def test_fr_hlt_014_process_return_resolves_the_alert() -> None:
    agent = _Agent()
    agent.sampler.names = ["sshd"]
    agent.tick()
    assert agent.tick(31) == [("ApplicationDown", "critical", "firing")]

    agent.sampler.names = ["sshd", _MAGIC]
    assert agent.tick(1) == []  # FIRING -> RESOLVING
    assert agent.tick(301) == [("ApplicationDown", "critical", "resolved")]


def test_fr_hlt_014_a_running_process_never_alerts() -> None:
    agent = _Agent()
    for _ in range(10):
        assert agent.tick(30) == []


def test_fr_hlt_014_a_lookalike_process_does_not_keep_magic_up() -> None:
    agent = _Agent()
    agent.sampler.names = [f"{_MAGIC}.bak", f"not{_MAGIC}"]
    agent.tick()
    assert agent.tick(31) == [("ApplicationDown", "critical", "firing")]


def test_fr_hlt_014_empty_process_name_reports_no_gauge_and_never_alerts() -> None:
    agent = _Agent(process_name="")
    agent.sampler.names = []  # nothing running: still silent

    for _ in range(5):
        assert agent.tick(30) == []

    assert "magic_process_up" not in agent.monitor.gauges()
    agent.emitter.emit(agent.now)
    gauges = agent.published_snapshots()[-1].gauges
    assert "magic_process_up" not in gauges


def test_fr_met_034_unreadable_process_list_is_not_an_alert() -> None:
    agent = _Agent()
    agent.sampler.names = PermissionError("denied")

    for _ in range(5):
        assert agent.tick(30) == []

    assert "magic_process_up" not in agent.monitor.gauges()
    assert agent.monitor.counters.snapshot()["host_sample_errors"] == 5


def test_fr_met_034_unreadable_process_list_does_not_resolve_a_firing_alert() -> None:
    """The list becoming unreadable is "no data", not "Magic is back": the
    alert stays firing past `resolveAfter`, and resolves once Magic is seen."""
    agent = _Agent()
    agent.sampler.names = ["sshd"]
    agent.tick()
    assert agent.tick(31) == [("ApplicationDown", "critical", "firing")]

    agent.sampler.names = PermissionError("denied")
    for _ in range(12):  # 12 x 60s, far beyond resolveAfter (300s)
        assert agent.tick(60) == []

    agent.sampler.names = ["sshd", _MAGIC]
    assert agent.tick(1) == []  # FIRING -> RESOLVING
    assert agent.tick(301) == [("ApplicationDown", "critical", "resolved")]


def test_fr_met_034_wire_snapshot_carries_magic_process_up() -> None:
    agent = _Agent()
    agent.sampler.names = ["sshd"]
    agent.monitor.sample_once()

    agent.emitter.emit(_T0 + timedelta(seconds=25))

    assert agent.published_snapshots()[-1].gauges["magic_process_up"] == 0.0
