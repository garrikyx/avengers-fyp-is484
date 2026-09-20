"""UBS-69: GET /telemetry/health/agents[/{agentId}] (spec 007 s5.1, s5.2)."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from telemetry_backend.app import create_internal_app, create_public_app
from telemetry_backend.config import BackendHealthConfig
from telemetry_backend.deps import AppDeps
from telemetry_shared.models.health import AgentHeartbeat, FileReadHealth

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


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
        config=BackendHealthConfig(missing_heartbeat_threshold_seconds=60),
        clock=clock,
    )
    return TestClient(create_public_app(deps)), deps, clock


def heartbeat(agent_id: str = "magic-agent-sg-01", **kw: object) -> AgentHeartbeat:
    base: dict[str, object] = {
        "agent_id": agent_id,
        "instance_ids": ["magic-prod-01"],
        "sent_at_utc": T0,
        "agent_version": "0.1.0+abc1234",
        "uptime_seconds": 86400.0,
        "status": "healthy",
        "status_reasons": [],
        "files": [
            FileReadHealth(
                path="/var/log/magic/fix.log",
                offset=918273645,
                instance_id="magic-prod-01",
                read_lag_ms=120.0,
                state="reading",
            )
        ],
        "read_lag_ms": 120.0,
        "parse_error_count_last5_min": 2,
        "publish_queue_depth": 4,
    }
    base.update(kw)
    return AgentHeartbeat(**base)  # type: ignore[arg-type]


def post(client: TestClient, hb: AgentHeartbeat) -> dict[str, object]:
    resp = client.post(
        "/telemetry/heartbeat",
        content=hb.model_dump_json(by_alias=True),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 202, resp.text
    return dict(resp.json())


# --- list ---------------------------------------------------------------------------


def test_empty_registry(env: tuple[TestClient, AppDeps, FakeClock]) -> None:
    client, _, _ = env
    body = client.get("/telemetry/health/agents").json()
    assert body == {
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
    assert agent["status"] == "healthy"
    assert agent["instanceIds"] == ["magic-prod-01"]
    assert agent["heartbeatAgeMs"] == 3100
    assert agent["lastHeartbeatUtc"].startswith("2026-09-20T04:00:00")


def test_counts_cover_all_four_states(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    client, _, clock = env
    post(client, heartbeat("h", status="healthy"))
    post(client, heartbeat("d", status="degraded"))
    post(client, heartbeat("u", status="unhealthy"))
    post(client, heartbeat("m"))
    # let "m" go stale, keep the others fresh
    clock.advance(61)
    for agent_id, status in (("h", "healthy"), ("d", "degraded"), ("u", "unhealthy")):
        post(client, heartbeat(agent_id, status=status, sent_at_utc=clock()))
    body = client.get("/telemetry/health/agents").json()
    assert body["counts"] == {"healthy": 1, "degraded": 1, "unhealthy": 1, "missing": 1}
    assert {a["agentId"]: a["status"] for a in body["agents"]}["m"] == "missing"


# --- detail --------------------------------------------------------------------------


def test_detail_matches_spec_007_5_2(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    client, _, clock = env
    post(
        client,
        heartbeat(
            status="degraded",
            status_reasons=["Fix.log: read lag 6200ms exceeds 5000ms threshold"],
        ),
    )
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
    assert body["statusReasons"] == [
        "Fix.log: read lag 6200ms exceeds 5000ms threshold"
    ]
    assert body["logReadLagMs"] == 120.0
    assert body["parseErrorCountLast5Min"] == 2
    assert body["callbackFailuresLast5Min"] is None  # FR-HLT-004: null, never 0
    assert body["publishQueueDepth"] == 4
    assert body["heartbeatAgeMs"] == 1000
    assert body["firstSeenUtc"].startswith("2026-09-20T04:00:00")
    assert body["files"][0]["path"] == "/var/log/magic/fix.log"
    assert body["files"][0]["state"] == "reading"


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
    """The agent stops sending; the backend, not the agent, flips it to missing."""
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
    assert body["reportedStatus"] == "healthy"  # last word from the agent is kept
    assert body["heartbeatAgeMs"] == 61_000


def test_only_file_paths_are_path_like(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    """FR-HLT-011: files[].path is the only path-like data in the response."""
    client, _, _ = env
    post(client, heartbeat())
    body = client.get("/telemetry/health/agents/magic-agent-sg-01").json()
    paths = [
        (k, v)
        for k, v in body.items()
        if isinstance(v, str) and ("/" in v or "\\" in v)
    ]
    assert paths == []
    assert all("/" in f["path"] for f in body["files"])


# --- placeholder ingest --------------------------------------------------------------


def test_placeholder_route_rejects_schema_drift(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    client, _, _ = env
    resp = client.post("/telemetry/heartbeat", json={"agentId": "x", "bogus": 1})
    assert resp.status_code == 422
    missing = {e["loc"][-1] for e in resp.json()["detail"] if e["type"] == "missing"}
    assert "sentAtUtc" in missing and "status" in missing


def test_placeholder_route_reports_first_contact(
    env: tuple[TestClient, AppDeps, FakeClock],
) -> None:
    client, _, _ = env
    assert post(client, heartbeat())["firstContact"] is True
    assert post(client, heartbeat())["firstContact"] is False


def test_internal_app_has_no_public_routes() -> None:
    client = TestClient(create_internal_app(AppDeps()))
    assert client.get("/telemetry/health/agents").status_code == 404
