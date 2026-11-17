"""UBS-129 integration: Host Monitor (stubbed sampler) -> RuleEvaluator running
the shipped config/rules.yaml -> AlertRouter, and -> SnapshotEmitter wire gauges.

Covers FR-HLT-013/015, FR-MET-034, and the ticket's done-when: a stubbed 0.96
disk fires `HostDiskFull` as critical; a failed read counts `host_sample_errors`
and the agent keeps running (no false alert, no zero gauge).
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import CallbackResult
from telemetry_agent.config import load_agent_config
from telemetry_agent.health.host_monitor import HostConfig, HostMonitor
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.pipeline.evaluator import RuleEvaluator
from telemetry_agent.pipeline.ingest import MetricsIngestor
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import PublishResult
from telemetry_agent.publishing.snapshot_bridge import SnapshotEmitter
from telemetry_agent.rules.engine import RuleEngine
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.ingestion import TelemetryBatch
from telemetry_shared.models.snapshot import Snapshot

_REPO_ROOT = Path(__file__).resolve().parents[3]
_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_APP = "Magic"


class _Sampler:
    def __init__(self) -> None:
        self.disk: float | Exception = 0.40
        self.mounts: dict[str, float | Exception] = {}  # per-path override
        self.memory: float | Exception = 0.50

    def disk_used_ratio(self, path: str) -> float:
        value = self.mounts.get(path, self.disk)
        if isinstance(value, Exception):
            raise value
        return value

    def memory_used_ratio(self) -> float:
        if isinstance(self.memory, Exception):
            raise self.memory
        return self.memory

    def own_usage(self) -> tuple[float, float]:
        return 84.0, 1.8

    def process_running(self, name: str) -> bool:
        return True


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
    def __init__(self, disk_paths: tuple[str, ...] = ("/data",)) -> None:
        cfg = load_agent_config(_REPO_ROOT / "config" / "agent.yaml")
        self.now = _T0
        self.sampler = _Sampler()
        self.monitor = HostMonitor(HostConfig(disk_paths=disk_paths), self.sampler)
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
        engine = RuleEngine(
            cfg.rules,
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
        return _host_alerts(self.evaluator.evaluate_once())


def _host_alerts(alerts: list[AlertEvent]) -> list[tuple[str, str, str]]:
    return [
        (a.rule_name, a.severity, a.status)
        for a in alerts
        if a.rule_name.startswith("Host")
    ]


def test_fr_met_034_stubbed_disk_at_0_96_fires_host_disk_full_critical() -> None:
    agent = _Agent()
    agent.sampler.disk = 0.96

    assert agent.tick() == []  # pending: the 1m `for` hold has not elapsed
    assert agent.tick(30) == []
    assert agent.tick(31) == [("HostDiskFull", "critical", "firing")]


def test_fr_met_034_disk_recovery_resolves_the_alert() -> None:
    agent = _Agent()
    agent.sampler.disk = 0.96
    agent.tick()
    agent.tick(61)

    agent.sampler.disk = 0.40
    agent.tick(1)  # FIRING -> RESOLVING
    assert agent.tick(301) == [("HostDiskFull", "critical", "resolved")]


def test_fr_met_034_memory_high_holds_two_minutes() -> None:
    agent = _Agent()
    agent.sampler.memory = 0.97
    agent.tick()
    assert agent.tick(61) == []  # past HostDiskFull's 1m, short of 2m
    assert agent.tick(60) == [("HostMemoryHigh", "critical", "firing")]


def test_fr_hlt_015_a_failed_read_counts_an_error_and_never_alerts() -> None:
    agent = _Agent()
    agent.sampler.disk = PermissionError("denied")
    agent.sampler.memory = NotImplementedError("platform")

    for _ in range(5):
        assert agent.tick(30) == []  # the agent keeps running

    assert agent.monitor.counters.snapshot()["host_sample_errors"] == 10
    assert agent.monitor.gauges() == {}


def test_fr_met_034_wire_snapshot_carries_host_gauges_and_omits_unread_ones() -> None:
    agent = _Agent()
    agent.sampler.disk = 0.77
    agent.sampler.memory = OSError("unreadable")
    agent.monitor.sample_once()

    agent.emitter.emit(_T0 + timedelta(seconds=25))

    gauges = agent.published_snapshots()[-1].gauges
    assert gauges["host_disk_used_ratio"] == 0.77
    assert "host_memory_used_ratio" not in gauges  # omitted, never 0


def test_fr_hlt_015_host_sample_errors_is_a_queryable_counter() -> None:
    """Failed reads reach the aggregator (so a rule or the backend can see
    them), not just a shutdown log line."""
    agent = _Agent()
    agent.sampler.disk = PermissionError("denied")

    for _ in range(3):
        agent.tick(10)

    rows = agent.ingestor.aggregator.snapshot("5m", ())
    errors = sum(row.counters.get("host_sample_errors", 0) for row in rows.values())
    assert errors == 3  # one unreadable mount per tick; memory read fine

    # ADR 0010 / FR-PUB-008: the emitter publishes every dirty closed bucket so
    # delayed publication cannot silently lose earlier host-sample errors.
    agent.emitter.emit(agent.now + timedelta(seconds=10))
    wire = [
        entry.counters["host_sample_errors"]
        for snap in agent.published_snapshots()
        for entry in snap.series
        if "host_sample_errors" in entry.counters
    ]
    assert sum(wire) == 3


def test_fr_met_034_wire_snapshot_carries_each_mount_and_the_worst_one() -> None:
    agent = _Agent(disk_paths=("/data", "/logs"))
    agent.sampler.mounts = {"/data": 0.30, "/logs": 0.91}
    agent.monitor.sample_once()

    agent.emitter.emit(_T0 + timedelta(seconds=25))

    gauges = agent.published_snapshots()[-1].gauges
    assert gauges["host_disk_used_ratio"] == 0.91
    assert gauges["host_disk_used_ratio:/data"] == 0.30
    assert gauges["host_disk_used_ratio:/logs"] == 0.91


def test_fr_met_034_unreadable_host_gauge_does_not_resolve_a_firing_alert() -> None:
    agent = _Agent()
    agent.sampler.disk = 0.96
    agent.tick()
    assert agent.tick(61) == [("HostDiskFull", "critical", "firing")]

    agent.sampler.disk = PermissionError("denied")
    for _ in range(12):  # 12 x 60s, far beyond resolveAfter (300s)
        assert agent.tick(60) == []

    agent.sampler.disk = 0.40
    assert agent.tick(1) == []  # FIRING -> RESOLVING
    assert agent.tick(301) == [("HostDiskFull", "critical", "resolved")]
