"""Health monitor end to end: simulator logs -> agent -> backend -> health API.

One test drives every stage the health signal passes through, with real
components and only the backend clock injected:

    simulator-format lines (UBS-31)
    -> MultiLogMonitor: multi-file tail, offsets.json (UBS-22/23)
    -> PipelineBridge + committer, FixParser / AppLogParser (UBS-48/49, 40-44)
    -> HealthReporter: read lag, parse errors, queue depth (UBS-30, 58-60)
    -> BackendPublisher, heartbeat inside TelemetryBatch (UBS-103)
    -> POST /telemetry/batch: dedupe + rate limit (UBS-85)
    -> Agent Registry -> GET /telemetry/health/agents (UBS-69)
    -> internal /metrics and /readyz (UBS-96)

The backend runs in-process via `httpx.ASGITransport`, the same way
`tests/integration/agent/test_UBS_103_publisher_backend.py` does.
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from simulator.mock_logger import rotate_if_needed
from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.publishing import (
    connect_reporter_to_publisher,
    drop_hook,
    heartbeat_provider,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.parser.applog.parser import AppLogParser
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.monitor_adapter import (
    MonitorPipelineAdapter,
    monitors_by_resolved_path,
)
from telemetry_agent.pipeline.supervisor import PipelineBridge
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.outcome import PublishAction
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import HttpsPublishSink
from telemetry_backend.config import BackendHealthConfig, IngestGuardConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app, create_internal_app

AGENT_ID = "magic-agent-e2e"
INSTANCE_ID = "magic-prod-01"
ENDPOINT = "https://backend.example/telemetry/batch"
T0 = datetime(2026, 9, 29, 4, 0, 0, tzinfo=UTC)

# The exact line shapes `apps/simulator/src/simulator/mock_logger.py` writes.
_APP_LINE = (
    "2026-09-29 12:00:00.{ms:03d} [INFO] [CoreEngine] Heartbeat active. "
    "Connected session count: 3"
)
_FIX_LINE = (
    "2026-09-29 12:00:00.{ms:03d} : 8=FIX.4.2|9=140|35=8|49=MAGIC|56=CLIENT"
    "|11=ORD{seq}|55=AAPL|54=1|38=100|44=150.50|10=112|"
)
# A FIX line with an unparseable SendingTime: counted as a parse error (UBS-59).
_BAD_FIX_LINE = (
    "2026-09-29 12:00:00.999 : 8=FIX.4.2|9=140|35=8|49=MAGIC|56=CLIENT"
    "|52=notatime|11=ORD0|55=AMD|54=1|38=100|44=150.50|10=112|"
)
# The simulator's own "Heartbeat active" format, so AppLogParser claims it.
_APP_LOG_PATTERN = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+ \[[A-Z]+\]"


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class RecordingTransport(httpx.AsyncBaseTransport):
    """Forwards to the in-process backend and keeps each request body, so
    the test can replay a batch exactly as the agent sent it."""

    def __init__(self, app: FastAPI) -> None:
        self._inner = httpx.ASGITransport(app=app)
        self.bodies: list[bytes] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.bodies.append(await request.aread())
        return await self._inner.handle_async_request(request)


@dataclass
class Stack:
    log_dir: Path
    app_log: Path
    fix_log: Path
    monitor: MultiLogMonitor
    bridge: PipelineBridge
    adapter: MonitorPipelineAdapter
    reporter: HealthReporter
    publisher: BackendPublisher
    transport: RecordingTransport
    deps: AppDeps
    clock: FakeClock
    public: TestClient
    internal: TestClient

    def pump(self) -> int:
        """Tail -> parse -> commit everything currently in the files."""
        return sum(1 for _ in self.adapter.run_until(max_lines=10_000, idle_rounds=3))

    def publish(self) -> PublishAction | None:
        return asyncio.run(self.publisher.publish_once())

    def agent(self) -> dict[str, object]:
        response = self.public.get(f"/telemetry/health/agents/{AGENT_ID}")
        assert response.status_code == 200, response.text
        body: dict[str, object] = response.json()
        return body

    def metrics(self) -> str:
        return str(self.internal.get("/metrics").text)


def write_lines(path: Path, lines: list[str]) -> None:
    # The simulator uses a plain open("a"), which writes CRLF on Windows;
    # "\n" keeps byte offsets identical on every platform.
    with path.open("a", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(line + "\n")


def fix_lines(start: int, count: int) -> list[str]:
    return [_FIX_LINE.format(ms=i % 1000, seq=start + i) for i in range(count)]


@pytest.fixture
def stack(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Stack]:
    monkeypatch.setenv("MAGIC_TELEMETRY_ID_HASH_KEY", "e2e-test-key")
    app_log = tmp_path / "Application.log"
    fix_log = tmp_path / "Fix.log"
    app_log.touch()
    fix_log.touch()

    # --- backend (UBS-69/85/96) ---------------------------------------------------
    clock = FakeClock()
    deps = AppDeps(
        config=BackendHealthConfig(
            missing_heartbeat_threshold_seconds=60,
            ingest=IngestGuardConfig(max_batches_per_minute_per_agent=3),
        ),
        clock=clock,
    )
    app = create_app(deps=deps)
    public = TestClient(app)
    internal = TestClient(create_internal_app(deps))

    # --- agent: tail -> pipeline -> health ------------------------------------------
    monitor = MultiLogMonitor(
        [app_log, fix_log],
        registry_path=tmp_path / "offsets.json",
        commit_on_read=False,
    )
    reporter = HealthReporter(
        monitor.monitors,
        heartbeat=HeartbeatConfig(agent_id=AGENT_ID, instance_ids=(INSTANCE_ID,)),
    )
    registry = Registry(
        parsers={
            "fix": FixParser(hash_key=b"e2e-test-key"),
            "applog": AppLogParser(app_log_patterns=[_APP_LOG_PATTERN]),
        }
    )
    bridge = PipelineBridge(config=PipelineConfig(parse_workers=1), registry=registry)
    # The committer only calls `sink.record_parse_result`, which
    # HealthReporter implements (the parameter is typed as the demo metrics
    # sink), so every committed line feeds parseErrorCountLast5Min (UBS-59).
    bridge.attach_committer(monitors_by_resolved_path(monitor.monitors), sink=reporter)
    bridge.start()
    adapter = MonitorPipelineAdapter(
        monitor, bridge, parser_chain=["fix", "applog"], instance_id=INSTANCE_ID
    )

    # --- agent: publish ---------------------------------------------------------------
    transport = RecordingTransport(app)
    publisher = BackendPublisher(
        HttpsPublishSink(ENDPOINT, "e2e-token", transport=transport),
        parse_publish_config({"endpoint": ENDPOINT}),
        agent_id=AGENT_ID,
        application="Magic",
        heartbeat_provider=heartbeat_provider(reporter),
        on_drop=drop_hook(reporter),
    )
    connect_reporter_to_publisher(reporter, publisher)  # UBS-60

    yield Stack(
        log_dir=tmp_path,
        app_log=app_log,
        fix_log=fix_log,
        monitor=monitor,
        bridge=bridge,
        adapter=adapter,
        reporter=reporter,
        publisher=publisher,
        transport=transport,
        deps=deps,
        clock=clock,
        public=public,
        internal=internal,
    )
    bridge.stop()
    monitor.close()


def committed_offsets(stack: Stack) -> dict[str, int]:
    for monitor in stack.monitor.monitors.values():
        monitor.flush_commits()
    entries = json.loads((stack.log_dir / "offsets.json").read_text())
    return {Path(entry["source"]).name: entry["offset"] for entry in entries}


def test_simulator_logs_reach_the_backend_health_api(stack: Stack) -> None:
    # --- simulator writes both files; one FIX line is bad ---------------------------
    write_lines(stack.app_log, [_APP_LINE.format(ms=i) for i in range(20)])
    write_lines(stack.fix_log, fix_lines(1001, 130) + [_BAD_FIX_LINE])

    # --- agent tails, parses and commits every line -------------------------------
    assert stack.pump() == 151
    # UBS-23 / FR-PIP-006: offsets only move once the committer has the line,
    # and after a full pass they sit at the end of each file.
    assert committed_offsets(stack) == {
        "Application.log": stack.app_log.stat().st_size,
        "Fix.log": stack.fix_log.stat().st_size,
    }

    # --- the agent's own view before it publishes -------------------------------
    heartbeat = stack.reporter.build_heartbeat()
    assert heartbeat.parse_error_count_last5_min == 1  # 1/151 < 1%: still healthy
    assert heartbeat.status == "healthy", heartbeat.status_reasons

    # --- publisher carries the heartbeat inside a TelemetryBatch --------------------
    assert stack.publish() is PublishAction.COMMIT

    agent = stack.agent()
    assert agent["status"] == "healthy"
    assert agent["reportedStatus"] == "healthy"
    assert agent["instanceIds"] == [INSTANCE_ID]
    assert agent["parseErrorCountLast5Min"] == 1
    assert agent["publishQueueDepth"] == 0
    assert agent["logReadLagMs"] is not None  # UBS-30 made it across
    files = {Path(str(f["path"])).name: f for f in agent["files"]}  # type: ignore[attr-defined]
    assert set(files) == {"Application.log", "Fix.log"}
    assert all(f["readLagMs"] is not None for f in files.values())

    listing = stack.public.get("/telemetry/health/agents").json()
    assert listing["counts"] == {
        "healthy": 1,
        "degraded": 0,
        "unhealthy": 0,
        "missing": 0,
    }

    metrics = stack.metrics()
    assert "telemetry_backend_ingest_batches_total 1.0" in metrics
    assert "telemetry_backend_heartbeats_received_total 1.0" in metrics
    assert "telemetry_backend_agents_known 1.0" in metrics
    assert f'telemetry_backend_agent_stale{{agent_id="{AGENT_ID}"}} 0.0' in metrics

    # --- UBS-85: the agent retries the same batch -> acknowledged, not re-ingested --
    replay = stack.public.post(
        "/telemetry/batch",
        content=stack.transport.bodies[-1],
        headers={"Content-Type": "application/json"},
    )
    assert replay.status_code == 202
    assert replay.json()["duplicate"] is True
    metrics = stack.metrics()
    assert "telemetry_backend_ingest_dedupe_hits_total 1.0" in metrics
    assert "telemetry_backend_ingest_batches_total 1.0" in metrics

    # --- UBS-85: past 3 batches/minute the backend answers 429 and the agent
    # --- backs off instead of dropping data ------------------------------------------
    assert stack.publish() is PublishAction.COMMIT
    assert stack.publish() is PublishAction.COMMIT
    assert stack.publish() is not PublishAction.COMMIT
    assert stack.publisher.counters.snapshot()["publish_rate_limited"] == 1
    assert "telemetry_backend_ingest_rate_limited_total 1.0" in stack.metrics()

    # --- UBS-96: heartbeats alone do not make the store ready -------------------------
    readyz = stack.internal.get("/readyz")
    assert readyz.status_code == 503
    assert readyz.json()["hasData"] is False

    # --- agent goes quiet: past missingHeartbeatThreshold it reads as missing ---------
    stack.clock.advance(61)
    assert stack.agent()["status"] == "missing"
    metrics = stack.metrics()
    assert "telemetry_backend_agents_stale 1.0" in metrics
    assert f'telemetry_backend_agent_stale{{agent_id="{AGENT_ID}"}} 1.0' in metrics


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="renames a file the monitor holds open; Windows refuses (same as the "
    "UBS-30 rotation tests), CI on Linux runs it",
)
def test_no_lines_are_lost_across_a_simulator_rotation(stack: Stack) -> None:
    before = fix_lines(1, 40)
    write_lines(stack.fix_log, before)
    assert stack.pump() == 40

    # UBS-31's rotation, then the simulator keeps writing to a fresh Fix.log.
    assert rotate_if_needed(stack.fix_log, max_bytes=1, keep_rotated_files=2)
    after = fix_lines(41, 25)
    write_lines(stack.fix_log, after)

    assert stack.pump() == 25  # UBS-24: new file picked up from offset 0
    assert committed_offsets(stack)["Fix.log"] == stack.fix_log.stat().st_size

    assert stack.publish() is PublishAction.COMMIT
    agent = stack.agent()
    assert agent["status"] == "healthy"
    assert agent["parseErrorCountLast5Min"] == 0
