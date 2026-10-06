"""UBS-109: AlertRouter — the seam from Rule Engine output to the Backend
Publisher.

Most of this file is about the identity guard, because that is the only part
with teeth: `test_an_unguarded_mismatch_poisons_the_whole_batch` pins the
failure the router exists to prevent, so if someone later decides the guard is
redundant ceremony, that test says otherwise.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import PublishResult
from telemetry_shared.models.alerts import AlertEvent

_AGENT = "magic-agent-sg-01"
_APPLICATION = "Magic"
_ENDPOINT = "https://backend.example/telemetry/batch"
_NOW = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)


class _RecordingSink:
    """Accepts everything and remembers each body, so a test can prove an
    alert actually reached the wire rather than just the buffer."""

    def __init__(self) -> None:
        self.bodies: list[bytes] = []

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> PublishResult:
        self.bodies.append(body)
        return PublishResult(status_code=202, latency_ms=1.0)


def _alert(
    alert_id: str = "alert-1",
    *,
    agent_id: str = _AGENT,
    application: str = _APPLICATION,
) -> AlertEvent:
    return AlertEvent(
        alert_id=alert_id,
        rule_name="HighRejectRate",
        severity="critical",
        status="firing",
        application=application,
        instance_id="magic-prod-01",
        agent_id=agent_id,
        matched_condition="rejectRate > 0.05 for 5 minutes",
        observed_value=0.064,
        threshold=0.05,
        first_observed_utc=_NOW,
        last_observed_utc=_NOW,
        notification_count=1,
    )


def _publisher(sink: _RecordingSink | None = None) -> BackendPublisher:
    config = parse_publish_config({"endpoint": _ENDPOINT})
    return BackendPublisher(
        sink or _RecordingSink(),
        config,
        agent_id=_AGENT,
        application=_APPLICATION,
    )


def _router(
    publisher: BackendPublisher, *, logger: logging.Logger | None = None
) -> AlertRouter:
    return AlertRouter(
        publisher, agent_id=_AGENT, application=_APPLICATION, logger=logger
    )


# --- the happy path ------------------------------------------------------


def test_routed_alerts_reach_the_buffer_and_the_count_is_returned() -> None:
    publisher = _publisher()
    router = _router(publisher)

    routed = router.route([_alert("a1"), _alert("a2")], now=_NOW)

    assert routed == 2
    assert publisher.queue_depth() == 2
    assert router.counters.snapshot()["alerts_routed"] == 2


def test_a_routed_alert_reaches_the_wire_in_the_batch() -> None:
    """Buffering is not publishing — this follows the alert all the way out
    through `publish_once` and checks it is in the serialised batch."""
    sink = _RecordingSink()
    publisher = _publisher(sink)
    _router(publisher).route([_alert("alert-on-the-wire")], now=_NOW)

    asyncio.run(publisher.publish_once(now=_NOW))

    assert len(sink.bodies) == 1
    body = sink.bodies[0].decode()
    assert "alert-on-the-wire" in body
    # camelCase, because the shared models are CamelModel and the batch is
    # dumped by alias (models/ingestion.py).
    assert '"alerts"' in body
    assert '"agentId"' in body


def test_an_empty_list_is_a_no_op() -> None:
    publisher = _publisher()
    router = _router(publisher)

    assert router.route([], now=_NOW) == 0
    assert publisher.queue_depth() == 0
    # No `alerts_routed: 0` key either — a counter that never moved should
    # not appear, so a sampler sees nothing rather than a zero delta.
    assert router.counters.snapshot() == {}


# --- the identity guard --------------------------------------------------


@pytest.mark.parametrize(
    ("agent_id", "application"),
    [
        ("someone-elses-agent", _APPLICATION),
        (_AGENT, "SomeOtherApp"),
        ("someone-elses-agent", "SomeOtherApp"),
    ],
)
def test_a_mismatched_alert_is_dropped_before_it_reaches_the_buffer(
    agent_id: str, application: str
) -> None:
    publisher = _publisher()
    router = _router(publisher)

    routed = router.route(
        [_alert("bad", agent_id=agent_id, application=application)], now=_NOW
    )

    assert routed == 0
    assert publisher.queue_depth() == 0
    assert router.counters.snapshot()["alerts_rejected_identity"] == 1


def test_good_alerts_survive_a_mismatched_one_in_the_same_call() -> None:
    """The containment that matters: the bad alert is dropped, the good ones
    are published."""
    sink = _RecordingSink()
    publisher = _publisher(sink)
    router = _router(publisher)

    routed = router.route(
        [
            _alert("good-1"),
            _alert("poison", agent_id="someone-elses-agent"),
            _alert("good-2"),
        ],
        now=_NOW,
    )

    assert routed == 2
    assert publisher.queue_depth() == 2
    asyncio.run(publisher.publish_once(now=_NOW))

    body = sink.bodies[0].decode()
    assert "good-1" in body
    assert "good-2" in body
    assert "poison" not in body


def test_the_mismatch_is_logged_once_not_once_per_alert(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A misconfigured agent raises this for every alert it ever fires; the
    line is identical each time, so repeating it is just noise."""
    logger = logging.getLogger(f"{__name__}.router")
    router = _router(_publisher(), logger=logger)

    with caplog.at_level(logging.ERROR, logger=logger.name):
        router.route(
            [_alert(f"bad-{i}", agent_id="wrong") for i in range(5)], now=_NOW
        )

    assert len(caplog.records) == 1
    assert router.counters.snapshot()["alerts_rejected_identity"] == 5


def test_rejection_never_raises() -> None:
    """The Rule Engine has already done its work by the time we are called,
    and the same alert may still be owed to the callback path — so a routing
    problem must not propagate."""
    router = _router(_publisher())
    router.route([_alert("bad", agent_id="wrong")], now=_NOW)  # must not raise


# --- why the guard exists ------------------------------------------------


def test_an_unguarded_mismatch_poisons_the_whole_batch() -> None:
    """The failure `AlertRouter` prevents, demonstrated against the real
    publisher by bypassing the router.

    `TelemetryBatch.identities_match_batch` runs inside `build_batch`, inside
    `publish_once`, and nothing catches `ValidationError`. So one mismatched
    alert raises out of the publish loop *and* destroys the good alerts
    batched with it: they were already taken off the buffer when the raise
    happened, so they are never sent and never requeued.
    """
    sink = _RecordingSink()
    publisher = _publisher(sink)

    publisher.enqueue_alert(_alert("good-1"), now=_NOW)
    publisher.enqueue_alert(_alert("poison", agent_id="wrong"), now=_NOW)
    publisher.enqueue_alert(_alert("good-2"), now=_NOW)
    assert publisher.queue_depth() == 3

    with pytest.raises(ValidationError):
        asyncio.run(publisher.publish_once(now=_NOW))

    assert sink.bodies == []  # nothing sent
    assert publisher.queue_depth() == 0  # and the two good alerts are gone
