"""UBS-120: one Teams card per firing and per resolved alert transition."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from prometheus_client import generate_latest
from telemetry_backend.config import AlertingConfig, BackendConfigError
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app, create_internal_app
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.alert_notifier import (
    TOKEN_ENV,
    AlertNotifier,
    HttpNotifySink,
    NotifyingAlertStore,
    Outcome,
    TeamsNotifyConfig,
    load_teams_notify_config,
    notify_token,
    transition_kind,
)
from telemetry_backend.services.heartbeat_monitor import HeartbeatMonitor
from telemetry_shared.models.ingestion import Heartbeat
from telemetry_shared.models.notifications import AlertNotification

from tests.unit.backend.services.alert_fixtures import (
    AGENT_ID,
    BASE_TIME,
    make_alert_event,
    make_resolved_event,
)

FAST = TeamsNotifyConfig(retry_base_seconds=0.0)


class RecordingSink:
    def __init__(self, outcomes: list[Outcome] | None = None) -> None:
        self.sent: list[AlertNotification] = []
        self._outcomes = list(outcomes or [])
        self.closed = False

    async def send(self, notification: AlertNotification) -> Outcome:
        self.sent.append(notification)
        return self._outcomes.pop(0) if self._outcomes else "delivered"

    async def aclose(self) -> None:
        self.closed = True

    @property
    def kinds(self) -> list[tuple[str, str]]:
        return [(n.alert.alert_id, n.kind) for n in self.sent]


def run_store(
    events: list[Any], *, config: TeamsNotifyConfig = FAST
) -> tuple[RecordingSink, AlertNotifier]:
    """Merge `events` into a NotifyingAlertStore with a started notifier and
    let the sender drain."""
    sink = RecordingSink()
    notifier = AlertNotifier(sink, config)
    store = NotifyingAlertStore(notifier)

    async def scenario() -> None:
        notifier.start()
        for event in events:
            store.merge(event)
        for _ in range(50):
            await asyncio.sleep(0)
        await notifier.aclose()

    asyncio.run(scenario())
    return sink, notifier


# --- what is a transition ------------------------------------------------------


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (None, "firing", "firing"),
        ("pending", "firing", "firing"),
        ("firing", "firing", None),  # renotify / severity change / re-merge
        ("resolving", "firing", None),  # flap back: same occurrence
        ("firing", "resolving", None),
        ("firing", "resolved", "resolved"),
        ("resolving", "resolved", "resolved"),
        ("pending", "resolved", None),  # never fired: nothing to resolve
        (None, "resolved", None),  # synthetic: never saw it fire
        (None, "pending", None),
    ],
)
def test_transition_kind(before: str | None, after: str, expected: str | None) -> None:
    assert transition_kind(before, after) == expected


def test_an_agent_alert_lifecycle_posts_exactly_one_firing_and_one_resolved() -> None:
    later = BASE_TIME + timedelta(minutes=1)
    sink, notifier = run_store(
        [
            make_alert_event(status="pending"),
            make_alert_event(status="firing"),
            make_alert_event(status="firing", notification_count=2),  # renotify
            make_alert_event(
                status="firing", severity="warning", last_observed_utc=later
            ),
            make_alert_event(status="resolving", last_observed_utc=later),
            make_alert_event(status="firing", last_observed_utc=later),  # flap back
            make_resolved_event(),
            make_resolved_event(),  # delivered twice
        ]
    )
    assert sink.kinds == [("alert-1024", "firing"), ("alert-1024", "resolved")]
    assert notifier.counts["delivered"] == 2
    assert sink.closed


def test_a_card_carries_the_stored_alert() -> None:
    sink, _ = run_store([make_alert_event(), make_resolved_event()])
    firing, resolved = sink.sent
    assert firing.alert.rule_name == "HighRejectRate"
    assert firing.alert.status == "firing"
    assert resolved.alert.resolved_at_utc is not None


def test_a_resolve_for_an_alert_never_seen_firing_posts_nothing() -> None:
    sink, _ = run_store([make_resolved_event(alert_id="seen-only-resolved")])
    assert sink.sent == []


def test_a_stale_firing_after_resolve_does_not_post_again() -> None:
    # FR-QRY-019: the store ignores it, so no transition either.
    sink, _ = run_store([make_alert_event(), make_resolved_event(), make_alert_event()])
    assert sink.kinds == [("alert-1024", "firing"), ("alert-1024", "resolved")]


def test_each_occurrence_gets_its_own_cards() -> None:
    sink, _ = run_store(
        [
            make_alert_event(alert_id="occ-1"),
            make_resolved_event(alert_id="occ-1"),
            make_alert_event(alert_id="occ-2"),
            make_resolved_event(alert_id="occ-2"),
        ]
    )
    assert [k for _, k in sink.kinds] == ["firing", "resolved", "firing", "resolved"]


# --- the backend's own AgentHeartbeatMissing -------------------------------------


def _heartbeat(sent_at: Any) -> Heartbeat:
    return Heartbeat.model_validate(
        {
            "schemaVersion": 1,
            "agentId": AGENT_ID,
            "instanceIds": ["magic-prod-01"],
            "sentAtUtc": sent_at.isoformat(),
            "agentVersion": "1",
            "uptimeSeconds": 1,
            "status": "healthy",
            "parseErrorCountLast5Min": 0,
            "callbackFailuresLast5Min": 0,
            "publishQueueDepth": 0,
            "publishBufferBytes": 0,
            "droppedEventsLast5Min": 0,
            "activeAlertCount": 0,
            "resourceUsage": {"rssMb": 1, "cpuPercent": 1, "activeTasks": 1},
        }
    )


def _heartbeat_scenario(outages: int) -> RecordingSink:
    now = [BASE_TIME]
    sink = RecordingSink()
    notifier = AlertNotifier(sink, FAST)
    store = NotifyingAlertStore(notifier)
    registry = AgentRegistry(missing_threshold_seconds=60, clock=lambda: now[0])
    monitor = HeartbeatMonitor(
        registry=registry,
        alert_store=store,
        config=AlertingConfig(),
        now_fn=lambda: now[0],
    )

    async def scenario() -> None:
        notifier.start()
        registry.record_heartbeat(_heartbeat(now[0]))
        for _ in range(outages):
            now[0] += timedelta(seconds=90)
            for _tick in range(3):  # the monitor re-merges `firing` every tick
                await asyncio.to_thread(monitor.evaluate_once)
            registry.record_heartbeat(_heartbeat(now[0]))
            monitor.on_heartbeat(AGENT_ID)
        for _ in range(50):
            await asyncio.sleep(0)
        await notifier.aclose()

    asyncio.run(scenario())
    return sink


def test_heartbeat_missing_posts_once_per_outage_despite_re_merges() -> None:
    sink = _heartbeat_scenario(outages=1)
    assert [n.kind for n in sink.sent] == ["firing", "resolved"]
    assert sink.sent[0].alert.rule_name == "AgentHeartbeatMissing"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known bug (flagged for next sprint): HeartbeatMonitor reuses one "
        "alertId per agent, and the Alert Store will not reopen a resolved "
        "alertId (FR-QRY-019), so a second outage of the same agent never "
        "fires. Remove this xfail when the monitor rotates alertId per outage."
    ),
)
def test_a_second_outage_of_the_same_agent_posts_again() -> None:
    sink = _heartbeat_scenario(outages=2)
    assert [n.kind for n in sink.sent] == ["firing", "resolved", "firing", "resolved"]


# --- the notifier itself ---------------------------------------------------------


def test_observe_from_another_thread_reaches_the_sink() -> None:
    sink = RecordingSink()
    notifier = AlertNotifier(sink, FAST)
    store = NotifyingAlertStore(notifier)

    async def scenario() -> None:
        notifier.start()
        worker = threading.Thread(target=store.merge, args=(make_alert_event(),))
        worker.start()
        await asyncio.to_thread(worker.join)
        for _ in range(50):
            await asyncio.sleep(0)
        await notifier.aclose()

    asyncio.run(scenario())
    assert sink.kinds == [("alert-1024", "firing")]


def test_merges_before_start_are_counted_not_lost_silently() -> None:
    notifier = AlertNotifier(RecordingSink(), FAST)
    NotifyingAlertStore(notifier).merge(make_alert_event())
    assert notifier.counts["dropped_not_running"] == 1


def test_a_full_queue_drops_the_oldest_and_counts_it() -> None:
    sink = RecordingSink()
    notifier = AlertNotifier(sink, TeamsNotifyConfig(queue_size=2))
    store = NotifyingAlertStore(notifier)

    async def scenario() -> None:
        notifier.start()
        # No await between merges, so the sender cannot drain in between.
        for i in range(4):
            store.merge(make_alert_event(alert_id=f"a{i}"))
        for _ in range(50):
            await asyncio.sleep(0)
        await notifier.aclose()

    asyncio.run(scenario())
    assert [n.alert.alert_id for n in sink.sent] == ["a2", "a3"]
    assert notifier.counts["dropped_queue_full"] == 2


def test_retries_then_delivers() -> None:
    sink = RecordingSink(outcomes=["retry", "retry", "delivered"])
    notifier = AlertNotifier(sink, FAST)
    notification = AlertNotification(
        kind="firing",
        alert=_record(),
    )
    assert asyncio.run(notifier.deliver(notification)) == "delivered"
    assert len(sink.sent) == 3
    assert notifier.counts["delivered"] == 1


def test_gives_up_after_max_attempts() -> None:
    sink = RecordingSink(outcomes=["retry"] * 5)
    notifier = AlertNotifier(
        sink, TeamsNotifyConfig(max_attempts=2, retry_base_seconds=0)
    )
    outcome = asyncio.run(
        notifier.deliver(AlertNotification(kind="firing", alert=_record()))
    )
    assert outcome == "retry"
    assert len(sink.sent) == 2
    assert notifier.counts["failed"] == 1


def test_a_raising_sink_never_escapes() -> None:
    class Boom(RecordingSink):
        async def send(self, notification: AlertNotification) -> Outcome:
            raise RuntimeError("boom")

    notifier = AlertNotifier(Boom(), TeamsNotifyConfig(max_attempts=1))
    outcome = asyncio.run(
        notifier.deliver(AlertNotification(kind="firing", alert=_record()))
    )
    assert outcome == "retry"
    assert notifier.counts["failed"] == 1


def _record() -> Any:
    store = NotifyingAlertStore(AlertNotifier(RecordingSink(), FAST))
    store.merge(make_alert_event())
    detail = store.get_alert("alert-1024")
    assert detail is not None
    return detail.alert


# --- the HTTP sink ---------------------------------------------------------------


def _sink_with(status: int | Exception) -> tuple[HttpNotifySink, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if isinstance(status, Exception):
            raise status
        return httpx.Response(status)

    sink = HttpNotifySink(
        "http://127.0.0.1:3978/api/notify",
        "s3cret",
        transport=httpx.MockTransport(handler),
    )
    return sink, seen


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (202, "delivered"),
        (200, "delivered"),
        (409, "drop"),  # no group chat registered yet
        (400, "drop"),
        (401, "drop"),
        (429, "retry"),
        (502, "retry"),
        (httpx.ConnectError("refused"), "retry"),
    ],
)
def test_http_sink_outcomes(status: int | Exception, expected: str) -> None:
    sink, seen = _sink_with(status)

    async def scenario() -> Outcome:
        try:
            return await sink.send(AlertNotification(kind="firing", alert=_record()))
        finally:
            await sink.aclose()

    assert asyncio.run(scenario()) == expected
    assert seen[0].headers["Authorization"] == "Bearer s3cret"
    body = json.loads(seen[0].content)
    assert body["kind"] == "firing"
    assert body["alert"]["alertId"] == "alert-1024"


# --- config ----------------------------------------------------------------------


def test_config_defaults_off_and_loads_from_yaml(tmp_path: Path) -> None:
    assert load_teams_notify_config(None).enabled is False
    path = tmp_path / "backend.yaml"
    path.write_text(
        "notifications:\n"
        "  teams:\n"
        "    enabled: true\n"
        "    endpoint: http://localhost:3978/api/notify\n"
        "    timeout: 3s\n"
        "    maxAttempts: 5\n",
        encoding="utf-8",
    )
    config = load_teams_notify_config(path)
    assert config.enabled
    assert config.timeout_seconds == 3.0
    assert config.max_attempts == 5


def test_config_rejects_typos(tmp_path: Path) -> None:
    path = tmp_path / "backend.yaml"
    path.write_text("notifications:\n  teams:\n    enabeld: true\n", encoding="utf-8")
    with pytest.raises(BackendConfigError):
        load_teams_notify_config(path)


def test_config_refuses_plain_http_off_this_host() -> None:
    with pytest.raises(BackendConfigError, match="https"):
        TeamsNotifyConfig(endpoint="http://teams.example.com/api/notify")
    TeamsNotifyConfig(endpoint="https://teams.example.com/api/notify")


def test_token_is_required_with_no_dev_fallback() -> None:
    with pytest.raises(BackendConfigError, match=TOKEN_ENV):
        notify_token({})
    assert notify_token({TOKEN_ENV: "abc"}) == "abc"


# --- end to end through the real ingestion route ---------------------------------


def _batch_with(alert: dict[str, Any], seq: int) -> dict[str, Any]:
    from uuid import uuid4

    return {
        "schemaVersion": 1,
        "batchId": str(uuid4()),
        "batchSeq": seq,
        "agentId": AGENT_ID,
        "application": "Magic",
        "sentAtUtc": BASE_TIME.isoformat(),
        "snapshots": [],
        "events": [],
        "alerts": [alert],
    }


def test_agent_alerts_posted_to_the_batch_route_become_cards() -> None:
    sink = RecordingSink()
    notifier = AlertNotifier(sink, FAST)
    deps = AppDeps(alert_store=NotifyingAlertStore(notifier))
    deps.self_metrics.registry.register(notifier.collector())
    app = create_app(deps=deps, enable_heartbeat_monitor=False)

    firing = make_alert_event().model_dump(mode="json", by_alias=True)
    renotify = make_alert_event(notification_count=2).model_dump(
        mode="json", by_alias=True
    )
    resolved = make_resolved_event().model_dump(mode="json", by_alias=True)

    with TestClient(app) as client:
        for seq, alert in enumerate([firing, renotify, resolved], start=1):
            response = client.post("/telemetry/batch", json=_batch_with(alert, seq))
            assert response.status_code == 202, response.text
        deadline = time.monotonic() + 5
        while len(sink.sent) < 2 and time.monotonic() < deadline:
            time.sleep(0.02)
        metrics = TestClient(create_internal_app(deps)).get("/metrics").text

    assert sink.kinds == [("alert-1024", "firing"), ("alert-1024", "resolved")]
    assert sink.closed  # the app's lifespan closed it on shutdown
    assert (
        'telemetry_backend_teams_notifications_total{outcome="delivered"} 2.0'
        in metrics
    )
    assert generate_latest(deps.self_metrics.registry)  # still renders after close
