"""UBS-129: the real agent process runs the Host Monitor.

`build_agent` + `run_agent` against the real backend app in-process:

    stubbed sampler at 0.96 disk -> HostDiskFull critical in the backend
      (FR-HLT-013, FR-MET-034)
    real psutil sampler           -> heartbeat resourceUsage.rssMb > 0
      (FR-HLT-016)
    host.enabled: false           -> no monitor, no host alert
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from telemetry_agent.config import load_agent_config
from telemetry_agent.main import Agent, build_agent, run_agent
from telemetry_backend.main import create_app

AGENT_ID = "magic-agent-e2e-129"

_CONFIG = """
agent:
  id: {agent_id}
  instanceIds: [magic-e2e-01]
logs:
  paths: [{log_dir}/Application.log, {log_dir}/Fix.log]
  stateDir: {state_dir}
pipeline:
  evaluationInterval: 200ms
rules:
  path: rules.yaml
publish:
  endpoint: https://backend.example/telemetry/batch
  interval: 1s
host:
  enabled: {enabled}
  sampleInterval: 200ms
  diskPaths: ["{disk}"]
"""

# HostDiskFull as in config/rules.yaml, with no `for` hold so the test is quick.
_RULES = """
rules:
  - name: HostDiskFull
    kind: threshold
    source: gauge
    metric: host_disk_used_ratio
    operator: ">"
    tiers:
      - {severity: warning, threshold: 0.85}
      - {severity: critical, threshold: 0.95}
    for: 0s
    dependsOnLogActivity: false
"""


class _StubSampler:
    def disk_used_ratio(self, path: str) -> float:
        return 0.96

    def memory_used_ratio(self) -> float:
        return 0.5

    def own_usage(self) -> tuple[float, float]:
        return 84.0, 1.8


def _agent(
    tmp_path: Path, *, enabled: bool = True, stub: bool = False
) -> tuple[Any, Agent]:
    (tmp_path / "rules.yaml").write_text(_RULES, encoding="utf-8")
    config_path = tmp_path / "agent.yaml"
    config_path.write_text(
        _CONFIG.format(
            agent_id=AGENT_ID,
            log_dir=(tmp_path / "logs").as_posix(),
            state_dir=(tmp_path / "state").as_posix(),
            enabled=str(enabled).lower(),
            disk=tmp_path.as_posix(),
        ),
        encoding="utf-8",
    )
    app = create_app()
    agent = build_agent(
        load_agent_config(config_path),
        publish_transport=httpx.ASGITransport(app=app),
        started_at=datetime.now(UTC) - timedelta(hours=1),  # past startup grace
        env={
            "MAGIC_TELEMETRY_ID_HASH_KEY": "e2e-hash-key",
            "MAGIC_TELEMETRY_PUBLISH_TOKEN": "e2e-token",
            "MAGIC_TELEMETRY_CALLBACK_SECRET": "e2e-secret",
        },
        host_sampler=_StubSampler() if stub else None,
    )
    return app, agent


def _run(app: Any, agent: Agent, *, wait_for: str) -> tuple[list[Any], dict[str, Any]]:
    """Run the agent until `wait_for` ('alert' or 'rss') shows in the backend."""

    async def scenario() -> tuple[list[Any], dict[str, Any]]:
        worker = asyncio.create_task(app.state.ingestion.run())
        stop = asyncio.Event()
        running = asyncio.create_task(run_agent(agent, stop))
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://backend"
        )
        alerts: list[Any] = []
        health: dict[str, Any] = {}
        try:
            for _ in range(0 if wait_for == "none" else 100):  # up to ~10s
                await asyncio.sleep(0.1)
                alerts = (await client.get("/telemetry/alerts")).json()["alerts"]
                health = (
                    await client.get(f"/telemetry/health/agents/{AGENT_ID}")
                ).json()
                rss = (health.get("resourceUsage") or {}).get("rssMb")
                if (wait_for == "alert" and alerts) or (wait_for == "rss" and rss):
                    break
            if wait_for == "none":
                await asyncio.sleep(1.5)
                alerts = (await client.get("/telemetry/alerts")).json()["alerts"]
        finally:
            stop.set()
            await asyncio.wait_for(running, 15)
            worker.cancel()
            await client.aclose()
        return alerts, health

    return asyncio.run(scenario())


def test_fr_met_034_stubbed_disk_at_0_96_fires_host_disk_full_in_the_backend(
    tmp_path: Path,
) -> None:
    app, agent = _agent(tmp_path, stub=True)

    alerts, _ = _run(app, agent, wait_for="alert")

    assert [(a["ruleName"], a["severity"]) for a in alerts] == [
        ("HostDiskFull", "critical")
    ]
    assert alerts[0]["agentId"] == AGENT_ID
    assert agent.host_monitor is not None
    assert agent.host_monitor.counters.snapshot().get("host_sample_errors", 0) == 0


def test_fr_hlt_016_heartbeat_reports_the_real_agents_non_zero_rss(
    tmp_path: Path,
) -> None:
    app, agent = _agent(tmp_path)

    _, health = _run(app, agent, wait_for="rss")

    assert health["resourceUsage"]["rssMb"] > 0
    assert agent.host_monitor is not None
    assert agent.host_monitor.counters.snapshot().get("host_sample_errors", 0) == 0


def test_fr_hlt_013_host_disabled_runs_no_monitor_and_raises_no_host_alert(
    tmp_path: Path,
) -> None:
    app, agent = _agent(tmp_path, enabled=False, stub=True)
    assert agent.host_monitor is None

    alerts, _ = _run(app, agent, wait_for="none")

    assert alerts == []
