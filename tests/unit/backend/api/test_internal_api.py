"""UBS-96: /healthz, /readyz, /metrics on the internal listener (FR-HLT-010/012)."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from telemetry_backend.app import create_internal_app, create_public_app
from telemetry_backend.config import BackendHealthConfig
from telemetry_backend.deps import AppDeps
from telemetry_shared.models.health import AgentHeartbeat

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


@pytest.fixture
def env() -> tuple[TestClient, TestClient, AppDeps, FakeClock]:
    clock = FakeClock()
    deps = AppDeps(
        config=BackendHealthConfig(
            warmup_window_seconds=120, missing_heartbeat_threshold_seconds=60
        ),
        clock=clock,
    )
    return (
        TestClient(create_internal_app(deps)),
        TestClient(create_public_app(deps)),
        deps,
        clock,
    )


def heartbeat(agent_id: str) -> AgentHeartbeat:
    return AgentHeartbeat(
        agent_id=agent_id,
        instance_ids=["i"],
        sent_at_utc=T0,
        agent_version="0.1.0",
        uptime_seconds=1,
        status="healthy",
    )


# --- /healthz ------------------------------------------------------------------------


def test_healthz_is_liveness_only(
    env: tuple[TestClient, TestClient, AppDeps, FakeClock],
) -> None:
    internal, _, _, _ = env
    resp = internal.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- /readyz -------------------------------------------------------------------------


def test_readyz_warming_until_first_ingest(
    env: tuple[TestClient, TestClient, AppDeps, FakeClock],
) -> None:
    internal, _, _, clock = env
    clock.advance(600)  # process has been up a long time, but nothing arrived
    resp = internal.get("/readyz")
    assert resp.status_code == 503
    assert resp.json() == {
        "status": "warming",
        "warmupWindowSeconds": 120.0,
        "sinceFirstIngestSeconds": None,
    }


def test_readyz_becomes_ready_after_warmup_window(
    env: tuple[TestClient, TestClient, AppDeps, FakeClock],
) -> None:
    internal, _, deps, clock = env
    deps.warmup.mark_ingest()
    clock.advance(119)
    resp = internal.get("/readyz")
    assert resp.status_code == 503
    assert resp.json()["status"] == "warming"
    assert resp.json()["sinceFirstIngestSeconds"] == 119.0
    clock.advance(1)
    resp = internal.get("/readyz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_heartbeats_do_not_count_as_data_for_warmup(
    env: tuple[TestClient, TestClient, AppDeps, FakeClock],
) -> None:
    """FR-QRY-005: an empty store must not read as ready because agents said hello."""
    internal, public, _, clock = env
    public.post(
        "/telemetry/heartbeat",
        content=heartbeat("a").model_dump_json(by_alias=True),
        headers={"Content-Type": "application/json"},
    )
    clock.advance(1000)
    assert internal.get("/readyz").status_code == 503


# --- /metrics ------------------------------------------------------------------------


def test_metrics_exposition_is_prometheus_text(
    env: tuple[TestClient, TestClient, AppDeps, FakeClock],
) -> None:
    internal, _, _, _ = env
    resp = internal.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    body = resp.text
    for name in (
        "telemetry_backend_ingest_batches_total",
        "telemetry_backend_ingest_validation_failures_total",
        "telemetry_backend_ingest_dedupe_hits_total",
        "telemetry_backend_dropped_payloads_total",
        "telemetry_backend_ingest_queue_depth",
        "telemetry_backend_store_memory_bytes",
        "telemetry_backend_query_latency_seconds",
        "telemetry_backend_agents_known",
        "telemetry_backend_agents_stale",
        "telemetry_backend_warming_up",
    ):
        assert f"# TYPE {name}" in body, name
    # Present from the first scrape even with no producer wired yet.
    assert "telemetry_backend_ingest_batches_total 0.0" in body
    assert "telemetry_backend_warming_up 1.0" in body


def test_metrics_reflect_per_agent_staleness(
    env: tuple[TestClient, TestClient, AppDeps, FakeClock],
) -> None:
    internal, public, deps, clock = env
    for agent_id in ("a", "b"):
        public.post(
            "/telemetry/heartbeat",
            content=heartbeat(agent_id).model_dump_json(by_alias=True),
            headers={"Content-Type": "application/json"},
        )
    clock.advance(61)
    deps.registry.record_heartbeat(heartbeat("b"), received_at=clock())  # b refreshed
    body = internal.get("/metrics").text
    assert "telemetry_backend_agents_known 2.0" in body
    assert "telemetry_backend_agents_stale 1.0" in body
    assert 'telemetry_backend_agent_stale{agent_id="a"} 1.0' in body
    assert 'telemetry_backend_agent_stale{agent_id="b"} 0.0' in body
    assert 'telemetry_backend_agent_heartbeat_age_seconds{agent_id="a"} 61.0' in body
    assert "telemetry_backend_heartbeats_received_total 2.0" in body


def test_decommissioned_agent_leaves_the_exposition(
    env: tuple[TestClient, TestClient, AppDeps, FakeClock],
) -> None:
    internal, _, deps, _ = env
    deps.registry.record_heartbeat(heartbeat("gone"))
    assert 'agent_id="gone"' in internal.get("/metrics").text
    deps.registry.remove("gone")
    assert 'agent_id="gone"' not in internal.get("/metrics").text


def test_query_latency_is_observed_by_route_template(
    env: tuple[TestClient, TestClient, AppDeps, FakeClock],
) -> None:
    internal, public, deps, _ = env
    deps.registry.record_heartbeat(heartbeat("magic-agent-sg-01"))
    public.get("/telemetry/health/agents/magic-agent-sg-01")
    public.get("/telemetry/health/agents")
    public.get("/nope")
    body = internal.get("/metrics").text
    # template, not the concrete agent id -> bounded cardinality
    count = "telemetry_backend_query_latency_seconds_count"
    assert f'{count}{{route="/telemetry/health/agents/{{agent_id}}"}} 1.0' in body
    assert f'{count}{{route="/telemetry/health/agents"}} 1.0' in body
    assert 'route="unmatched"' in body
    latency_lines = [
        line
        for line in body.splitlines()
        if line.startswith("telemetry_backend_query_latency_seconds")
    ]
    assert latency_lines  # the histogram is there ...
    assert not any(
        "magic-agent-sg-01" in line for line in latency_lines
    )  # ... unlabelled by id


# --- FR-HLT-012: listener split ---------------------------------------------------


def test_probes_are_not_on_the_public_app(
    env: tuple[TestClient, TestClient, AppDeps, FakeClock],
) -> None:
    _, public, _, _ = env
    for path in ("/metrics", "/healthz", "/readyz"):
        assert public.get(path).status_code == 404, path


def test_public_routes_are_not_on_the_internal_app(
    env: tuple[TestClient, TestClient, AppDeps, FakeClock],
) -> None:
    internal, _, _, _ = env
    assert internal.get("/telemetry/health/agents").status_code == 404
    assert internal.post("/telemetry/heartbeat", json={}).status_code == 404
