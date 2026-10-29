"""FR-CBK-014/017: a callback action reuses the §3 dispatcher, and a failing
action never affects the Magic callback or publishing (UBS-35)."""

import asyncio
from datetime import datetime

import httpx
from action_fixtures import callback_action, make_alert
from telemetry_agent.actions.runner import ActionRunner
from telemetry_agent.callbacks.signing import sign
from telemetry_agent.callbacks.status import DeliveryTracker
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_shared.models.alerts import AlertEvent


class _Recorder:
    def __init__(self) -> None:
        self.alerts: list[AlertEvent] = []
        # The router reads delivery state off the dispatcher to enrich the
        # alert it publishes (FR-CBK-009).
        self.tracker = DeliveryTracker()

    def enqueue(self, alert: AlertEvent) -> None:
        self.alerts.append(alert)

    def enqueue_alert(self, alert: AlertEvent, *, now: datetime | None = None) -> None:
        self.alerts.append(alert)


class _ExplodingRunner:
    def enqueue(self, alert: AlertEvent) -> int:
        raise RuntimeError("action runner is broken")


def test_a_failing_action_path_leaves_callback_and_publish_untouched() -> None:
    publisher, dispatcher = _Recorder(), _Recorder()
    router = AlertRouter(
        publisher,  # type: ignore[arg-type]
        agent_id="magic-agent-sg-01",
        application="Magic",
        dispatcher=dispatcher,  # type: ignore[arg-type]
        actions=_ExplodingRunner(),  # type: ignore[arg-type]
    )

    assert router.route([make_alert()]) == 1

    assert len(publisher.alerts) == 1
    assert len(dispatcher.alerts) == 1
    assert router.counters.snapshot()["alerts_action_enqueue_failed"] == 1


def _runner(
    handler: httpx.MockTransport, *, dry_run: bool = False, timeout: float = 5.0
) -> ActionRunner:
    action = callback_action(dry_run=dry_run, timeout_seconds=timeout)
    return ActionRunner(
        {action.name: action},
        lambda _rule: (action.name,),
        secret=b"hook-secret",
        callback_transport=handler,
    )


def test_a_callback_action_is_signed_like_the_magic_callback() -> None:
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    runner = _runner(httpx.MockTransport(handle))
    assert asyncio.run(runner.execute(make_alert(), "ops-webhook")) == "ok"

    (request,) = seen
    assert str(request.url) == "https://ops.example/hooks/telemetry"
    timestamp = request.headers["X-Telemetry-Timestamp"]
    assert request.headers["X-Telemetry-Signature"] == sign(
        b"hook-secret", timestamp, request.content
    )
    assert request.headers["X-Telemetry-Idempotency-Key"] == "alert-1:firing:1"


def test_a_failed_callback_action_counts_as_failed_on_its_own_counters() -> None:
    runner = _runner(httpx.MockTransport(lambda _r: httpx.Response(400)))
    assert asyncio.run(runner.execute(make_alert(), "ops-webhook")) == "failed"
    counters = runner.counters.snapshot()
    assert counters["action_runs:ops-webhook:failed"] == 1
    # Nothing named like the Magic dispatcher's counters, which feed
    # CallbackFailing, is touched by a hook.
    assert not any(name.startswith("callback_") for name in counters)


def test_a_hanging_callback_action_times_out() -> None:
    async def hang(_request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(30)
        return httpx.Response(200)

    runner = _runner(httpx.MockTransport(hang), timeout=0.3)
    assert asyncio.run(runner.execute(make_alert(), "ops-webhook")) == "timeout"


def test_a_dry_run_callback_action_sends_nothing() -> None:
    def refuse(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("dry run must not send")

    runner = _runner(httpx.MockTransport(refuse), dry_run=True)
    assert asyncio.run(runner.execute(make_alert(), "ops-webhook")) == "dry_run"
