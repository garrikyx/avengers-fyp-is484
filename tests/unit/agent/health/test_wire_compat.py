"""UBS-58/66 wire compatibility: our heartbeat flattened to the Ingestion
Service's contract (see apps/agent/src/telemetry_agent/health/wire.py and
docs/plan/ubs58-60-notes.md "Wire compatibility with UBS-66").
"""

import json
from datetime import UTC, datetime

from telemetry_agent.health.heartbeat import HttpHeartbeatSink, heartbeat_json
from telemetry_agent.health.wire import to_ingestion_heartbeat
from telemetry_shared.models.health import AgentHeartbeat, FileReadHealth
from telemetry_shared.models.health import ResourceUsage as HealthResourceUsage
from telemetry_shared.models.ingestion import Heartbeat

T0 = datetime(2026, 9, 22, 4, 0, 0, tzinfo=UTC)


def make(**kw: object) -> AgentHeartbeat:
    base: dict[str, object] = {
        "agent_id": "magic-agent-sg-01",
        "instance_ids": ["magic-prod-01"],
        "sent_at_utc": T0,
        "agent_version": "0.1.0",
        "uptime_seconds": 42.7,
        "status": "healthy",
    }
    base.update(kw)
    return AgentHeartbeat(**base)  # type: ignore[arg-type]


def test_unmeasured_signals_become_zero_not_null() -> None:
    """The ingestion contract has no null for these; the cost is recorded in
    the notes doc, and the reporter keeps its own Nones internally."""
    wire = to_ingestion_heartbeat(make())
    assert wire.parse_error_count_last5_min == 0
    assert wire.callback_failures_last5_min == 0
    assert wire.publish_queue_depth == 0
    assert wire.publish_buffer_bytes == 0
    assert wire.dropped_events_last5_min == 0
    assert wire.active_alert_count == 0
    assert (wire.resource_usage.rss_mb, wire.resource_usage.active_tasks) == (0.0, 0)


def test_measured_signals_are_carried_through_unchanged() -> None:
    wire = to_ingestion_heartbeat(
        make(
            parse_error_count_last5_min=7,
            publish_queue_depth=12,
            active_alert_count=3,
            resource_usage=HealthResourceUsage(
                rss_mb=84.0, cpu_percent=1.8, active_tasks=42
            ),
        )
    )
    assert wire.parse_error_count_last5_min == 7
    assert wire.publish_queue_depth == 12
    assert wire.active_alert_count == 3
    assert wire.resource_usage.rss_mb == 84.0


def test_uptime_is_truncated_never_rounded_up() -> None:
    """Never claim a second of uptime the agent has not had."""
    assert to_ingestion_heartbeat(make(uptime_seconds=42.9)).uptime_seconds == 42


def test_files_get_an_instance_id_which_the_contract_requires() -> None:
    hb = make(
        files=[
            FileReadHealth(
                path="/var/log/magic/fix.log",
                offset=918273645,
                read_lag_ms=120.0,
                state="reading",
                rotations_detected=3,
            )
        ]
    )
    wire = to_ingestion_heartbeat(hb)
    assert wire.files[0].instance_id == "magic-prod-01"  # agent's first instance
    assert wire.files[0].path == "/var/log/magic/fix.log"
    assert wire.files[0].read_lag_ms == 120.0
    assert wire.files[0].state == "reading"
    assert wire.files[0].rotations_detected == 3
    # an explicit per-file instance wins when the monitor knows it
    hb2 = make(files=[FileReadHealth(path="/l", offset=0, instance_id="other")])
    assert to_ingestion_heartbeat(hb2).files[0].instance_id == "other"


def test_status_survives_but_reasons_are_dropped() -> None:
    """The ingestion model is extra='forbid' and has no statusReasons field.
    Losing FR-HLT-003's reasons is the known cost of adapting - if this test
    starts failing because the field was added upstream, switch the sink back
    to wire='health' and delete the adapter."""
    hb = make(status="degraded", status_reasons=["Fix.log: read lag 6200ms exceeds"])
    wire = to_ingestion_heartbeat(hb)
    assert wire.status == "degraded"
    assert not hasattr(wire, "status_reasons")


def test_ingestion_payload_validates_against_the_real_contract() -> None:
    """The whole point: the Ingestion Service must accept what we send."""
    body = heartbeat_json(make(status="unhealthy"), "ingestion")
    rehydrated = Heartbeat.model_validate_json(body)  # would raise on drift
    assert rehydrated.agent_id == "magic-agent-sg-01"
    assert json.loads(body)["schemaVersion"] == 1


def test_health_wire_still_available_for_the_reversal() -> None:
    hb = make(status="degraded", status_reasons=["because"])
    payload = json.loads(heartbeat_json(hb, "health"))
    assert payload["statusReasons"] == ["because"]
    assert payload["parseErrorCountLast5Min"] is None  # null preserved


def test_http_sink_defaults_to_the_ingestion_contract() -> None:
    assert HttpHeartbeatSink("http://x/telemetry/heartbeat").wire == "ingestion"
    assert HttpHeartbeatSink("http://x", wire="health").wire == "health"
