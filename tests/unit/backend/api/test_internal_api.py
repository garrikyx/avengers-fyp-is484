"""UBS-96: /healthz, /readyz, /metrics on the internal app (FR-HLT-010/012)."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from telemetry_backend.config import BackendHealthConfig, StreamProcessorConfig
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app, create_internal_app
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.ingestion import Heartbeat, ResourceUsage
from telemetry_shared.models.snapshot import SeriesEntry, Snapshot

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)

Env = tuple[TestClient, TestClient, AppDeps, "FakeClock", StreamProcessor]


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


@pytest.fixture
def env() -> Env:
    clock = FakeClock()
    deps = AppDeps(
        config=BackendHealthConfig(
            warmup_window_seconds=120, missing_heartbeat_threshold_seconds=60
        ),
        clock=clock,
    )
    processor = StreamProcessor(
        StreamProcessorConfig(warmup_window_seconds=120), started_at=T0
    )
    public = TestClient(create_app(processor=processor, deps=deps))
    return TestClient(create_internal_app(deps)), public, deps, clock, processor


def heartbeat(agent_id: str) -> Heartbeat:
    return Heartbeat(
        schema_version=1,
        agent_id=agent_id,
        instance_ids=["i"],
        sent_at_utc=T0,
        agent_version="0.1.0",
        uptime_seconds=1,
        status="healthy",
        files=[],
        parse_error_count_last5_min=0,
        callback_failures_last5_min=0,
        publish_queue_depth=0,
        publish_buffer_bytes=0,
        dropped_events_last5_min=0,
        active_alert_count=0,
        resource_usage=ResourceUsage(rss_mb=1, cpu_percent=0, active_tasks=1),
    )


def post_heartbeat(public: TestClient, agent_id: str) -> None:
    resp = public.post(
        "/telemetry/heartbeat",
        content=heartbeat(agent_id).model_dump_json(by_alias=True),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 202, resp.text


def merge_snapshot(processor: StreamProcessor, at: datetime) -> None:
    processor.process_snapshot(
        Snapshot(
            schema_version=1,
            agent_id="agent-a",
            application="Magic",
            instance_id="magic-prod-01",
            bucket_start_utc=at,
            bucket_seconds=10,
            series=[SeriesEntry(dimensions={"session": "S"}, counters={})],
        ),
        now=at,
    )


# --- /healthz ------------------------------------------------------------------------


def test_healthz_is_liveness_only(env: Env) -> None:
    internal, *_ = env
    resp = internal.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- /readyz: same StreamProcessor.is_ready() as the public probe --------------------


def test_readyz_warming_while_no_data_has_arrived(env: Env) -> None:
    internal, _, _, clock, _ = env
    clock.advance(600)  # up a long time, but nothing merged
    resp = internal.get("/readyz")
    assert resp.status_code == 503
    assert resp.json() == {
        "status": "warming",
        "warmupWindowSeconds": 120.0,
        "hasData": False,
    }


def test_readyz_ready_once_window_elapsed_and_data_exists(env: Env) -> None:
    internal, _, _, clock, processor = env
    merge_snapshot(processor, T0)
    clock.advance(119)
    resp = internal.get("/readyz")
    assert resp.status_code == 503
    assert resp.json()["hasData"] is True
    clock.advance(1)
    resp = internal.get("/readyz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_heartbeats_do_not_count_as_data_for_warmup(env: Env) -> None:
    """FR-QRY-005: an empty store must not read as ready because agents said hello."""
    internal, public, _, clock, _ = env
    post_heartbeat(public, "a")
    clock.advance(1000)
    assert internal.get("/readyz").status_code == 503


def test_internal_app_needs_a_built_public_app() -> None:
    with pytest.raises(ValueError):
        create_internal_app(AppDeps())


# --- /metrics ------------------------------------------------------------------------


def test_metrics_exposition_is_prometheus_text(env: Env) -> None:
    internal, *_ = env
    resp = internal.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    for name in (
        "telemetry_backend_ingest_batches",
        "telemetry_backend_ingest_validation_failures",
        "telemetry_backend_ingest_dedupe_hits",
        "telemetry_backend_dropped_payloads",
        "telemetry_backend_ingest_queue_depth",
        "telemetry_backend_store_memory_bytes",
        "telemetry_backend_query_latency_seconds",
        "telemetry_backend_agents_known",
        "telemetry_backend_agents_stale",
        "telemetry_backend_warming_up",
    ):
        assert f"# TYPE {name}" in resp.text, name


def test_routes_feed_the_counters(env: Env) -> None:
    internal, public, *_ = env
    post_heartbeat(public, "a")
    batch = {
        "schemaVersion": 1,
        "batchId": "0192f000-0000-7000-8000-000000000001",
        "batchSeq": 1,
        "agentId": "b",
        "application": "Magic",
        "sentAtUtc": T0.isoformat(),
        "snapshots": [],
        "events": [],
        "alerts": [],
        "heartbeat": heartbeat("b").model_dump(mode="json", by_alias=True),
    }
    assert public.post("/telemetry/batch", json=batch).status_code == 202
    assert public.post("/telemetry/batch", json={"bad": 1}).status_code == 400
    text = internal.get("/metrics").text
    assert "telemetry_backend_ingest_batches_total 1.0" in text
    assert "telemetry_backend_heartbeats_received_total 2.0" in text
    assert "telemetry_backend_ingest_validation_failures_total 1.0" in text


def test_metrics_reflect_per_agent_staleness(env: Env) -> None:
    internal, public, deps, clock, _ = env
    for agent_id in ("a", "b"):
        post_heartbeat(public, agent_id)
    clock.advance(61)
    deps.registry.record_heartbeat(heartbeat("b"), received_at=clock())
    text = internal.get("/metrics").text
    assert "telemetry_backend_agents_known 2.0" in text
    assert "telemetry_backend_agents_stale 1.0" in text
    assert 'telemetry_backend_agent_stale{agent_id="a"} 1.0' in text
    assert 'telemetry_backend_agent_stale{agent_id="b"} 0.0' in text
    assert 'telemetry_backend_agent_heartbeat_age_seconds{agent_id="a"} 61.0' in text


def test_decommissioned_agent_leaves_the_exposition(env: Env) -> None:
    internal, _, deps, _, _ = env
    deps.registry.record_heartbeat(heartbeat("gone"))
    assert 'agent_id="gone"' in internal.get("/metrics").text
    deps.registry.remove("gone")
    assert 'agent_id="gone"' not in internal.get("/metrics").text


def test_query_latency_is_observed_by_route_template(env: Env) -> None:
    internal, public, deps, _, _ = env
    deps.registry.record_heartbeat(heartbeat("magic-agent-sg-01"))
    public.get("/telemetry/health/agents/magic-agent-sg-01")
    public.get("/telemetry/health/agents")
    public.get("/nope")
    text = internal.get("/metrics").text
    count = "telemetry_backend_query_latency_seconds_count"
    assert f'{count}{{route="/telemetry/health/agents/{{agent_id}}"}} 1.0' in text
    assert f'{count}{{route="/telemetry/health/agents"}} 1.0' in text
    assert 'route="unmatched"' in text
    assert "magic-agent-sg-01" not in "\n".join(
        line
        for line in text.splitlines()
        if line.startswith("telemetry_backend_query_latency_seconds")
    )


# --- FR-HLT-012: listener split ---------------------------------------------------


def test_metrics_is_not_on_the_public_app(env: Env) -> None:
    _, public, *_ = env
    assert public.get("/metrics").status_code == 404


def test_public_routes_are_not_on_the_internal_app(env: Env) -> None:
    internal, *_ = env
    assert internal.get("/telemetry/health/agents").status_code == 404
    assert internal.post("/telemetry/heartbeat", json={}).status_code == 404
