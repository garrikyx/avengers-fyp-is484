"""UBS-114 / FR-TST-010 slice: the real agent process, end to end.

`build_agent` + `run_agent` (what `telemetry-agent` runs) against the real
backend app in-process and a stub Magic callback endpoint:

    Fix.log reject burst -> agent (pipeline thread + event loop)
      -> backend alert store (GET /telemetry/alerts)
      -> Magic callback, HMAC-signed
      -> heartbeat -> GET /telemetry/health/agents shows the agent

and a clean stop: offsets flushed to the end of the file.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from telemetry_agent.callbacks.signing import sign
from telemetry_agent.config import load_agent_config
from telemetry_agent.main import build_agent, run_agent
from telemetry_backend.main import create_app

AGENT_ID = "magic-agent-e2e-114"
SECRET = "e2e-callback-secret"
BURST = 51  # RejectSpike fires above 50 rejects in 1m

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
callbacks:
  endpoint: https://magic.example/magic/callbacks/telemetry-alerts
"""

# RejectSpike as in config/rules.yaml, with no `for` hold so the test is quick.
_RULES = """
rules:
  - name: RejectSpike
    kind: threshold
    source: counter
    metric: orders_rejected
    operator: ">"
    tiers: [{severity: warning, threshold: 50}]
    window: 1m
    for: 0s
"""


def _burst(sending_time: str) -> list[str]:
    lines = []
    for tag in range(BURST):
        seq = 2 * tag + 1
        lines.append(
            f"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34={seq}|52={sending_time}"
            f"|11=C{tag}|55=AAPL|54=1|40=2|38=100|10=000|"
        )
        lines.append(
            f"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34={seq + 1}|52={sending_time}"
            f"|11=C{tag}|37=O{tag}|17=E{tag}|55=AAPL|54=1|150=8|39=8|103=3|10=000|"
        )
    return lines


def test_the_agent_process_alerts_magic_and_the_backend(tmp_path: Path) -> None:
    log_dir = (tmp_path / "logs").as_posix()
    state_dir = (tmp_path / "state").as_posix()
    (tmp_path / "rules.yaml").write_text(_RULES, encoding="utf-8")
    config_path = tmp_path / "agent.yaml"
    config_path.write_text(
        _CONFIG.format(agent_id=AGENT_ID, log_dir=log_dir, state_dir=state_dir),
        encoding="utf-8",
    )
    cfg = load_agent_config(config_path)

    callbacks: list[httpx.Request] = []

    def magic(request: httpx.Request) -> httpx.Response:
        callbacks.append(request)
        return httpx.Response(200, json={})

    app = create_app()
    agent = build_agent(
        cfg,
        publish_transport=httpx.ASGITransport(app=app),
        callback_transport=httpx.MockTransport(magic),
        started_at=datetime.now(UTC) - timedelta(hours=1),  # past startup grace
        env={
            "MAGIC_TELEMETRY_ID_HASH_KEY": "e2e-hash-key",
            "MAGIC_TELEMETRY_PUBLISH_TOKEN": "e2e-token",
            "MAGIC_TELEMETRY_CALLBACK_SECRET": SECRET,
        },
    )
    fix_log = tmp_path / "logs" / "Fix.log"

    async def scenario() -> tuple[list[dict[str, object]], dict[str, object]]:
        # ASGITransport skips the backend lifespan, so run its ingestion
        # worker here, in the same loop as the agent.
        worker = asyncio.create_task(app.state.ingestion.run())
        stop = asyncio.Event()
        running = asyncio.create_task(run_agent(agent, stop))
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://backend"
        )
        try:
            await asyncio.sleep(0.3)  # agent is tailing before the burst lands
            stamp = datetime.now(UTC).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]
            with fix_log.open("a", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(_burst(stamp)) + "\n")

            alerts: list[dict[str, object]] = []
            for _ in range(150):  # up to ~15s
                await asyncio.sleep(0.1)
                body = (await client.get("/telemetry/alerts")).json()
                alerts = body["alerts"]
                if alerts and callbacks:
                    break
            agent_health = (
                await client.get(f"/telemetry/health/agents/{AGENT_ID}")
            ).json()
        finally:
            stop.set()
            await asyncio.wait_for(running, 15)  # graceful shutdown completes
            worker.cancel()
            await client.aclose()
        return alerts, agent_health

    alerts, agent_health = asyncio.run(scenario())

    # --- the backend got the alert from this agent ------------------------------
    assert [a["ruleName"] for a in alerts] == ["RejectSpike"]
    assert alerts[0]["source"] == "agent"
    assert alerts[0]["agentId"] == AGENT_ID

    # --- Magic got one signed callback for it ----------------------------------------
    assert len(callbacks) == 1
    request = callbacks[0]
    body = request.read()
    timestamp = request.headers["X-Telemetry-Timestamp"]
    assert request.headers["X-Telemetry-Signature"] == sign(
        SECRET.encode(), timestamp, body
    )
    assert json.loads(body)["ruleName"] == "RejectSpike"

    # --- the heartbeat in the same batches registered the agent ---------------------
    assert agent_health["status"] == "healthy"

    # --- clean stop: every line ingested, offsets flushed to the end of the file ---
    assert agent.ingestor.stats()["lines_ingested"] == 2 * BURST
    assert agent.ingestor.stats()["ingest_errors"] == 0
    offsets = json.loads((tmp_path / "state" / "offsets.json").read_text())
    by_name = {Path(e["source"]).name: e["offset"] for e in offsets}
    assert by_name["Fix.log"] == fix_log.stat().st_size
