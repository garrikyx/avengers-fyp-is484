"""FR-MET-020/021/022/023: bounded events, independently of alert decisions."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

import pytest
from telemetry_agent.parser.applog.telemetry import AppLogTelemetry
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import (
    LineClassification,
    ParseError,
    ParseResult,
    SourceMeta,
)
from telemetry_agent.publishing.config import PublishConfigError, parse_publish_config
from telemetry_agent.publishing.events import EventEmitter
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import PublishResult
from telemetry_backend.services.ingestion import AcceptedIngestion, IngestionService
from telemetry_shared.models.ingestion import TelemetryEvent

from tests.unit.agent.publishing.publish_fixtures import make_alert

NOW = datetime(2026, 10, 18, 1, 0, tzinfo=UTC)


class Sink:
    def __init__(self) -> None:
        self.bodies: list[dict] = []
        self.status = 202

    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> PublishResult:
        self.bodies.append(json.loads(body))
        return PublishResult(status_code=self.status, latency_ms=0)


def stack(**kwargs):
    sink = Sink()
    publisher = BackendPublisher(
        sink,
        parse_publish_config({"endpoint": "https://backend/telemetry/batch"}),
        agent_id="magic-agent-sg-01",
        application="Magic",
    )
    emitter = EventEmitter(
        publisher,
        agent_id="magic-agent-sg-01",
        application="Magic",
        instance_id="magic-prod-01",
        **kwargs,
    )
    return emitter, publisher, sink


def meta(now=NOW):
    return SourceMeta(
        instance_id="magic-prod-01",
        path="/private/Application.log",
        log_type="auto",
        read_at=now,
    )


def app(level, signature=None):
    return ParseResult(
        classification=LineClassification.APP_LOG,
        app_log_telemetry=AppLogTelemetry(
            "01:00:00.000001",
            "123456",
            level,
            "PRIVATE_COMPONENT",
            "PRIVATE_MESSAGE account=PRIVATE_ACCOUNT",
            signature,
        ),
    )


def sent(publisher, sink):
    asyncio.run(publisher.publish_once())
    return sink.bodies[-1]["events"]


def test_errors_are_aggregated_without_signatures_or_alerts_and_severity_is_preserved():
    emitter, publisher, sink = stack()
    for level in "NIEWFEF":
        emitter.observe(app(level), meta())
    assert publisher.queue_depth() == 0
    emitter.flush(NOW + timedelta(seconds=10))
    events = sent(publisher, sink)
    assert {
        (e["dimensions"]["level"], e["severity"], e["fields"]["count"]) for e in events
    } == {("E", "warning", 2), ("F", "critical", 2)}
    assert all(e["eventType"] == "app.error" for e in events)
    assert all(e["fields"]["bucketSeconds"] == 10 for e in events)
    assert all(e["timeSource"] == "agent" for e in events)
    assert sink.bodies[-1]["alerts"] == []
    assert "PRIVATE_" not in json.dumps(sink.bodies)
    assert all(TelemetryEvent.model_validate(e).event_id.version == 7 for e in events)
    emitter.flush(NOW + timedelta(seconds=20))
    assert publisher.queue_depth() == 0


@pytest.mark.parametrize(
    ("level", "severity"),
    [
        ("N", "info"),
        ("I", "info"),
        ("W", "warning"),
        ("E", "warning"),
        ("F", "critical"),
    ],
)
def test_signature_is_an_observation_at_any_level_without_an_alert_rule(
    level, severity
):
    emitter, publisher, sink = stack()
    emitter.observe(app(level, "connection_disconnected"), meta())
    (event,) = sent(publisher, sink)
    assert event["eventType"] == "app.error_signature"
    assert event["dimensions"] == {
        "level": level,
        "errorSignature": "connection_disconnected",
    }
    assert event["severity"] == severity
    assert event["timeSource"] == "agent"
    assert sink.bodies[-1]["alerts"] == []


def test_backlogged_error_is_counted_in_active_processing_bucket():
    emitter, publisher, sink = stack()
    emitter.flush(NOW + timedelta(seconds=10))
    emitter.observe(app("E"), meta(NOW))
    emitter.flush(NOW + timedelta(seconds=20))
    (event,) = sent(publisher, sink)
    parsed = TelemetryEvent.model_validate(event)
    assert parsed.timestamp_utc == NOW + timedelta(seconds=10)
    assert parsed.fields["count"] == 1


def test_parse_errors_are_aggregated_by_closed_reason_with_no_details():
    emitter, publisher, sink = stack()
    for _ in range(20):
        emitter.observe(
            ParseResult(
                classification=LineClassification.FIX,
                error=ParseError("malformed_field", "PRIVATE_DETAILS"),
            ),
            meta(),
        )
    emitter.flush(NOW + timedelta(seconds=10))
    (event,) = sent(publisher, sink)
    assert event["eventType"] == "parse.error"
    assert event["dimensions"] == {"reason": "malformed_field"}
    assert event["fields"]["count"] == 20
    assert "PRIVATE_DETAILS" not in json.dumps(event)


def test_non_fix_event_cannot_carry_fix_only_fields():
    emitter, publisher, _ = stack()
    assert not emitter.emit("agent.started", at=NOW, fields={"msgType": "A"})
    assert publisher.queue_depth() == 0
    assert emitter.counters.snapshot()["event_emit_errors"] == 1


def test_fix_reject_gap_session_and_execution_sampling_use_only_sanitised_fields():
    emitter, publisher, sink = stack(execution_sample_every=2)
    parser = FixParser(hash_key=b"test-key")
    for seq, msg, extra in (
        (1, "A", ""),
        (4, "8", "150=8|39=8|103=3|"),
        (3, "3", "373=1|"),
        (4, "9", ""),
        (5, "8", "150=F|39=2|"),
        (6, "8", "150=F|39=2|"),
        (7, "5", ""),
    ):
        line = (
            f"8=FIX.4.2|9=999|35={msg}|34={seq}|49=MAGIC|56=VENUE|"
            f"11=PRIVATE_ORDER|1=PRIVATE_ACCOUNT|44=999.12345|58=PRIVATE_TEXT|"
            f"{extra}10=000|"
        ).encode()
        emitter.observe(parser.parse(line, meta()), meta())
    events = sent(publisher, sink)
    types = [e["eventType"] for e in events]
    assert types.count("fix.order_reject") == 2
    assert types.count("fix.seq_gap") == 2
    assert types.count("fix.session_state") == 2
    assert types.count("fix.execution") == 1
    assert types.count("fix.session_reject") == 1
    assert {
        e["fields"]["isRegression"] for e in events if e["eventType"] == "fix.seq_gap"
    } == {True, False}
    assert "PRIVATE_" not in json.dumps(events)
    assert "999.12345" not in json.dumps(events)
    assert any("clOrdIdHash" in e["fields"] for e in events)
    service = IngestionService()
    assert (
        service.validate_and_reserve(
            AcceptedIngestion(
                events=tuple(TelemetryEvent.model_validate(e) for e in events)
            )
        )
        == ()
    )


def test_rate_limit_is_per_type_and_instance_and_uses_monotonic_time():
    clock = [0.0]
    drops = []
    emitter, publisher, sink = stack(
        max_events_per_minute=2,
        monotonic=lambda: clock[0],
        on_drop=lambda: drops.append(1),
    )
    for _ in range(5):
        emitter.observe(app("F", "out_of_memory"), meta())
    emitter.flush(NOW, force=True)  # another event type has its own allowance
    assert len(drops) == 3
    assert len(sent(publisher, sink)) == 3
    clock[0] = 60
    emitter.observe(app("F", "out_of_memory"), meta())
    assert len(sent(publisher, sink)) == 1
    assert emitter.counters.snapshot()["events_rate_limited"] == 3


def test_alert_mirror_suppresses_reminders_but_keeps_escalation_and_resolution():
    emitter, publisher, sink = stack()
    alert = make_alert().model_copy(update={"severity": "warning"})
    emitter.alert(alert)
    emitter.alert(alert.model_copy(update={"notification_count": 2}))
    emitter.alert(alert.model_copy(update={"severity": "critical"}))
    emitter.alert(
        alert.model_copy(update={"status": "resolved", "resolved_at_utc": NOW})
    )
    emitter.alert(alert.model_copy(update={"agent_id": "different-agent"}))
    events = sent(publisher, sink)
    assert [e["eventType"] for e in events] == [
        "alert.fired",
        "alert.fired",
        "alert.resolved",
    ]
    assert {e["fields"]["alertId"] for e in events} == {alert.alert_id}
    assert emitter.counters.snapshot()["events_rejected_identity"] == 1


def test_retry_reuses_event_id_instead_of_creating_duplicate_observations():
    emitter, publisher, sink = stack()
    emitter.emit("agent.started", at=NOW)
    sink.status = 503
    sent(publisher, sink)
    sink.status = 202
    asyncio.run(publisher.publish_once(now=datetime.now(UTC) + timedelta(seconds=120)))
    assert sink.bodies[0]["events"] == sink.bodies[1]["events"]


@pytest.mark.parametrize("key", ["maxEventsPerMinute", "executionSampleEvery"])
def test_invalid_event_limits_fail_at_config_load(key):
    with pytest.raises(PublishConfigError):
        parse_publish_config({"endpoint": "https://backend", key: 0})
