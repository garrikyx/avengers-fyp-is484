"""UBS-69: GET /telemetry/health/agents[/{agentId}] (spec 007 s5.1, s5.2),
served from the same app as the Ingestion Service (UBS-66).
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from telemetry_backend.config import BackendHealthConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app
from telemetry_shared.models.ingestion import Heartbeat, HeartbeatFile, ResourceUsage

T0 = datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


@pytest.fixture
def env() -> tuple[TestClient, AppDeps, FakeClock]:
    clock = FakeClock()
    deps = AppDeps(
        config=BackendHealthConfig(missing_heartbeat_threshold_seconds=60), clock=clock
    )
    return TestClient(create_app(deps=deps)), deps, clock


def heartbeat(agent_id: str = "magic-agent-sg-01", **kw: object) -> Heartbeat:
    base: dict[str, object] = {
        "schema_version": 1,
        "agent_id": agent_id,
        "instance_ids": ["magic-prod-01"],
        "sent_at_utc": T0,
        "agent_version": "0.1.0+abc1234",
        "uptime_seconds": 86400,
        "status": "healthy",
        "files": [
            HeartbeatFile(
                path="/var/log/magic/fix.log",
                instance_id="magic-prod-01",
                offset=918273645,
                read_lag_ms=120.0,
                rotations_detected=3,
                state="reading",
            )
        ],
        "parse_error_count_last5_min": 2,
        "callback_failures_last5_min": 0,
        "publish_queue_depth": 4,
        "publish_buffer_bytes": 1048576,
        "dropped_events_last5_min": 0,
        "active_alert_count": 1,
        "resource_usage": ResourceUsage(rss_mb=84, cpu_percent=1.8, active_tasks=42),
    }
    base.update(kw)
    return Heartbeat(**base)  # type: ignore[arg-type]


def post(client: TestClient, hb: Heartbeat) -> None:
    resp = client.post(
        "/telemetry/heartbeat",
        content=hb.model_dump_json(by_alias=True),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 202, resp.text


# --- list ---------------------------------------------------------------------------


def test_empty_registry(env: tuple[TestClient, AppDeps, FakeClock]) -> None:
    client, _, _ = env
    assert client.get("/telemetry/health/agents").json() == {
        "agents": [],
        "counts": {"healthy": 0, "degraded": 0, "unhealthy": 0, "missing": 0},
    }


def test_list_matches_spec_007_5_1(env: tuple[TestClient, AppDeps, FakeClock]) -> None:
    client, _, clock = env
    post(client, heartbeat())
    clock.advance(3.1)
    body = client.get("/telemetry/health/agents").json()
    assert body["counts"] == {"healthy": 1, "degraded": 0, "unhealthy": 0, "missing": 0}
    agent = body["agents"][0]
    assert set(agent) == {
        "agentId",
        "status",
        "instanceIds",
        "lastHeartbeatUtc",
        "heartbeatAgeMs",
        "agentVersion",
    }
    assert agent["agentId"] == "magic-agent-sg-01"
    assert agent["heartbeatAgeMs"] == 3100


def test_counts_cover_all_four_states(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    client, _, clock = env
    for agent_id, st in (("h", "healthy"), ("d", "degraded"), ("u", "unhealthy")):
        post(client, heartbeat(agent_id, status=st))
    post(client, heartbeat("m"))
    clock.advance(61)  # only "m" is left to go stale
    for agent_id, st in (("h", "healthy"), ("d", "degraded"), ("u", "unhealthy")):
        post(client, heartbeat(agent_id, status=st, sent_at_utc=clock()))
    body = client.get("/telemetry/health/agents").json()
    assert body["counts"] == {"healthy": 1, "degraded": 1, "unhealthy": 1, "missing": 1}
    assert {a["agentId"]: a["status"] for a in body["agents"]}["m"] == "missing"


# --- detail --------------------------------------------------------------------------


def test_detail_matches_spec_007_5_2(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    client, _, clock = env
    post(client, heartbeat(status="degraded"))
    clock.advance(1)
    body = client.get("/telemetry/health/agents/magic-agent-sg-01").json()
    for key in (
        "agentId",
        "status",
        "lastHeartbeatUtc",
        "agentVersion",
        "uptimeSeconds",
        "logReadLagMs",
        "parseErrorCountLast5Min",
        "callbackFailuresLast5Min",
        "publishQueueDepth",
        "droppedEventsLast5Min",
        "files",
        "resourceUsage",
    ):
        assert key in body, key
    assert body["status"] == "degraded"
    assert body["reportedStatus"] == "degraded"
    assert body["logReadLagMs"] == 120.0  # worst case across files[]
    assert body["parseErrorCountLast5Min"] == 2
    assert body["publishQueueDepth"] == 4
    assert body["heartbeatAgeMs"] == 1000
    assert body["files"][0]["path"] == "/var/log/magic/fix.log"
    assert body["files"][0]["state"] == "reading"
    assert body["resourceUsage"]["rssMb"] == 84.0


def test_log_read_lag_is_null_when_no_file_has_read_yet(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    """FR-HLT-004: an unread file has no lag; 0 would read as 'caught up'."""
    client, _, _ = env
    post(client, heartbeat(files=[]))
    body = client.get("/telemetry/health/agents/magic-agent-sg-01").json()
    assert body["logReadLagMs"] is None


def test_detail_unknown_agent_is_404(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    client, _, _ = env
    resp = client.get("/telemetry/health/agents/nope")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "not_found"


def test_missing_heartbeat_detected_backend_side(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    """The agent stops sending; the backend, not the agent, flips it."""
    client, _, clock = env
    post(client, heartbeat())
    clock.advance(60)
    assert (
        client.get("/telemetry/health/agents/magic-agent-sg-01").json()["status"]
        == "healthy"
    )
    clock.advance(1)
    body = client.get("/telemetry/health/agents/magic-agent-sg-01").json()
    assert body["status"] == "missing"
    assert body["reportedStatus"] == "healthy"
    assert body["heartbeatAgeMs"] == 61_000


def test_only_file_paths_are_path_like(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    """FR-HLT-011: files[].path is the only path-like data in the response."""
    client, _, _ = env
    post(client, heartbeat())
    body = client.get("/telemetry/health/agents/magic-agent-sg-01").json()
    assert [
        (k, v)
        for k, v in body.items()
        if isinstance(v, str) and ("/" in v or "\\" in v)
    ] == []


# --- registration happens on the real ingestion path ---------------------------------


def test_registration_is_driven_by_the_ingestion_route(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    """FR-ING-010: the registry fills as telemetry arrives, with no separate
    endpoint of its own (our placeholder route is gone - UBS-66 owns this)."""
    client, deps, _ = env
    assert len(deps.registry) == 0
    post(client, heartbeat())
    assert len(deps.registry) == 1
    assert deps.registry.get("magic-agent-sg-01") is not None


def test_probes_still_served_and_ingestion_untouched(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    client, _, _ = env
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 503  # warming, no data yet
    assert client.get("/metrics").status_code == 404  # internal only (UBS-96)
