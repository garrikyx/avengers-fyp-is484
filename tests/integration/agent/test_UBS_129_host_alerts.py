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
        self.memory: float | Exception = 0.50

    def disk_used_ratio(self, path: str) -> float:
        if isinstance(self.disk, Exception):
            raise self.disk
        return self.disk

    def memory_used_ratio(self) -> float:
        if isinstance(self.memory, Exception):
            raise self.memory
        return self.memory

    def own_usage(self) -> tuple[float, float]:
        return 84.0, 1.8


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
    def __init__(self) -> None:
        cfg = load_agent_config(_REPO_ROOT / "config" / "agent.yaml")
        self.now = _T0
        self.sampler = _Sampler()
        self.monitor = HostMonitor(HostConfig(disk_paths=("/data",)), self.sampler)
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
