"""UBS-113: RuleEvaluator — the periodic loop between the metrics store and
AlertRouter.

Each test uses a real aggregator, engine, router, publisher and dispatcher,
and drives time with one shared clock. Rules are the shipped defaults with
`for`/`resolve` delays zeroed (`dataclasses.replace`): the FSM's timing is
the engine's own tests' subject; here a tick that matches pends and the
next one fires, so each test is about what the *loop* feeds the engine.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import CallbackResult
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS
from telemetry_agent.parser.fix.session_tracker import SessionHeartbeatTracker
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.pipeline.evaluator import RuleEvaluator
from telemetry_agent.publishing.config import parse_publish_config
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.sink import PublishResult
from telemetry_agent.rules.config_loader import SighupRuleReloader
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import RuleConfig
from telemetry_shared.models.alerts import AlertEvent
from test_UBS_109_alert_router import _AGENT, _APPLICATION, _ENDPOINT, _alert

_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_INSTANCE = "magic-prod-01"
_SHIPPED_RULES = Path(__file__).resolve().parents[4] / "config" / "rules.yaml"


class _Clock:
    """One wall clock for the aggregator (epoch floats) and the evaluator
    (datetimes), so a window and a `now` never disagree."""

    def __init__(self) -> None:
        self.now = _T0

    def __call__(self) -> datetime:
        return self.now

    def epoch(self) -> float:
        return self.now.timestamp()

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class _NullCallbackSink:
    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> CallbackResult:
        return CallbackResult(status_code=200, latency_ms=1.0)


class _StatusSink:
    def __init__(self, status: int) -> None:
        self.status = status

    async def send(self, *, body: bytes, headers: Mapping[str, str]) -> PublishResult:
        return PublishResult(status_code=self.status, latency_ms=1.0)


def _rule(name: str) -> RuleConfig:
    rule = next(r for r in DEFAULT_RULES if r.name == name)
    return replace(rule, for_seconds=0, resolve_after_seconds=0)


class _Stack:
    def __init__(
        self,
        rules: tuple[RuleConfig, ...],
        *,
        publish_status: int = 202,
        tracker: SessionHeartbeatTracker | None = None,
        reloader_path: Path | None = None,
        lock: threading.Lock | None = None,
    ) -> None:
        self.clock = _Clock()
        self.aggregator = MetricsAggregator(
            config=AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS)),
            clock=self.clock.epoch,
        )
        self.engine = RuleEngine(
            rules=rules,
            instance_id=_INSTANCE,
            application=_APPLICATION,
            agent_id=_AGENT,
            started_at=_T0 - timedelta(hours=1),
        )
        self.publish_sink = _StatusSink(publish_status)
        self.publisher = BackendPublisher(
            self.publish_sink,
            parse_publish_config({"endpoint": _ENDPOINT}),
            agent_id=_AGENT,
            application=_APPLICATION,
        )
        self.dispatcher = CallbackDispatcher(
            _NullCallbackSink(),
            parse_callbacks_config({"endpoint": "https://magic.example/cb"}),
            b"secret",
        )
        self.router = AlertRouter(
            self.publisher,
            agent_id=_AGENT,
            application=_APPLICATION,
            dispatcher=self.dispatcher,
        )
        self.tracker = tracker
        self.monotonic = 0.0
        self.evaluator = RuleEvaluator(
            self.engine,
            self.aggregator,
            self.router,
            instance_id=_INSTANCE,
            session_tracker=tracker,
            publisher=self.publisher,
            dispatcher=self.dispatcher,
            reloader=(
                SighupRuleReloader(self.engine, reloader_path)
                if reloader_path is not None
                else None
            ),
            clock=self.clock,
            monotonic=lambda: self.monotonic,
            lock=lock,
        )

    def seed(self, **counters: int) -> None:
        """Write counters straight into the store, labelled with placeholder
        dimension values — the snapshot sums them back to instance level."""
        for metric, amount in counters.items():
            dims = dict.fromkeys(self.aggregator.config.metric_dimensions[metric], "x")
            dims["instance_id"] = _INSTANCE
            self.aggregator.ingest_agent_counters(
                dims=dims, counters={metric: Decimal(amount)}, at=self.clock.now
            )

    def tick(self, advance: float = 1.0) -> list[AlertEvent]:
        self.clock.advance(advance)
        return self.evaluator.evaluate_once()

    def fire(self) -> list[AlertEvent]:
        """Pending on this tick, firing on the next."""
        assert self.tick() == []
        return self.tick()

    def pending_callback(self, alert_id: str) -> bool:
        return self.dispatcher.tracker.status_of(alert_id) is not None


def _names(alerts: list[AlertEvent]) -> list[tuple[str, str]]:
    return [(a.rule_name, a.status) for a in alerts]


# --- each signal path reaches the engine --------------------------------


def test_a_counter_rule_fires_and_reaches_both_paths() -> None:
    stack = _Stack((_rule("RejectSpike"),))
    stack.seed(orders_rejected=51)

    fired = stack.fire()

    assert _names(fired) == [("RejectSpike", "firing")]
    assert stack.publisher.queue_depth() == 1
    assert stack.pending_callback(fired[0].alert_id)


def test_rules_on_different_windows_are_each_evaluated() -> None:
    """RejectSpike reads 1m, HighRejectRate reads 5m: one tick, both."""
    stack = _Stack((_rule("RejectSpike"), _rule("HighRejectRate")))
    stack.seed(orders_rejected=60, orders_acked=40)

    fired = stack.fire()

    assert sorted(_names(fired)) == [
        ("HighRejectRate", "firing"),
        ("RejectSpike", "firing"),
    ]


def test_the_publisher_gauge_reaches_backend_unreachable() -> None:
    stack = _Stack((_rule("BackendUnreachable"),), publish_status=503)
    at = _T0
    for i in range(5):
        stack.publisher.enqueue_alert(_alert(f"filler-{i}"), now=at)
        asyncio.run(stack.publisher.publish_once(now=at))
        at += timedelta(seconds=120)  # past the backoff cap
    assert stack.publisher.consecutive_failures == 5

    assert _names(stack.fire()) == [("BackendUnreachable", "firing")]


def test_a_silent_session_fires_fix_session_down_once() -> None:
    """The tracker latches each silence: many ticks after the timeout still
    put exactly one heartbeat_timeouts into the store."""
    tracker = SessionHeartbeatTracker(timeout_seconds=60)
    tracker.observe(msg_type="Heartbeat", sender="MAGIC", target="EXCH1", at=0.0)
    stack = _Stack((_rule("FixSessionDown"),), tracker=tracker)

    stack.monotonic = 61.0
    fired = stack.fire()
    for _ in range(5):
        stack.monotonic += 10
        stack.tick()

    assert _names(fired) == [("FixSessionDown", "firing")]
    row = stack.aggregator.snapshot("1m", group_by=())[()]
    assert row.counters["heartbeat_timeouts"] == Decimal(1)


def test_dispatcher_failures_reach_callback_failing_without_double_counting() -> None:
    stack = _Stack((_rule("CallbackFailing"),))
    stack.dispatcher.counters.increment("callback_failures", 4)

    fired = stack.fire()
    for _ in range(3):
        stack.tick()  # resampling an unchanged registry adds nothing

    assert _names(fired) == [("CallbackFailing", "firing")]
    row = stack.aggregator.snapshot("5m", group_by=())[()]
    assert row.counters["callback_failures"] == Decimal(4)


def test_a_cleared_condition_resolves_on_both_paths() -> None:
    stack = _Stack((_rule("RejectSpike"),))
    stack.seed(orders_rejected=51)
    firing = stack.fire()

    stack.tick(advance=61)  # burst ages out of the 1m window -> resolving
    resolved = stack.tick()

    assert _names(resolved) == [("RejectSpike", "resolved")]
    assert resolved[0].alert_id == firing[0].alert_id
    assert stack.publisher.queue_depth() == 2  # firing + resolved


# --- reload --------------------------------------------------------------


def _write_rules(path: Path, names: list[str]) -> None:
    """A rules file the loader accepts, from the shipped config's own
    entries, so the test doesn't restate the YAML schema."""
    shipped = yaml.safe_load(_SHIPPED_RULES.read_text())
    kept = [r for r in shipped["rules"] if r["name"] in names]
    assert len(kept) == len(names)
    path.write_text(yaml.safe_dump({**shipped, "rules": kept}))


def test_a_reload_that_drops_a_firing_rule_routes_its_resolution(
    tmp_path: Path,
) -> None:
    rules_file = tmp_path / "rules.yaml"
    _write_rules(rules_file, ["SeqGapDetected"])
    stack = _Stack((_rule("RejectSpike"),), reloader_path=rules_file)
    stack.seed(orders_rejected=51)
    firing = stack.fire()

    stack.evaluator.request_reload()  # what SIGHUP does: only a flag
    routed = stack.tick()

    assert _names(routed) == [("RejectSpike", "resolved")]
    assert routed[0].alert_id == firing[0].alert_id
    assert [r.name for r in stack.engine.rules] == ["SeqGapDetected"]
    assert stack.publisher.queue_depth() == 2


def test_a_rejected_reload_routes_nothing_and_keeps_the_rules(
    tmp_path: Path,
) -> None:
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("rules: [not, a, rule]")
    stack = _Stack((_rule("RejectSpike"),), reloader_path=rules_file)

    stack.evaluator.request_reload()

    assert stack.tick() == []
    assert [r.name for r in stack.engine.rules] == ["RejectSpike"]


def test_a_reload_request_waits_for_the_next_tick(tmp_path: Path) -> None:
    rules_file = tmp_path / "rules.yaml"
    _write_rules(rules_file, ["SeqGapDetected"])
    stack = _Stack((_rule("RejectSpike"),), reloader_path=rules_file)

    stack.evaluator.request_reload()

    assert [r.name for r in stack.engine.rules] == ["RejectSpike"]
    stack.tick()
    assert [r.name for r in stack.engine.rules] == ["SeqGapDetected"]


# --- the loop itself -----------------------------------------------------


def test_run_survives_a_failing_tick_and_stops_on_request() -> None:
    stack = _Stack((_rule("RejectSpike"),))
    evaluator = RuleEvaluator(
        stack.engine,
        stack.aggregator,
        stack.router,
        instance_id=_INSTANCE,
        interval_seconds=0.01,
        clock=stack.clock,
    )
    calls = 0
    real = evaluator.evaluate_once

    def flaky() -> list[AlertEvent]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("bad tick")
        return real()

    evaluator.evaluate_once = flaky  # type: ignore[method-assign]

    async def drive() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(evaluator.run(stop))
        while calls < 3 and not task.done():  # a dead loop fails, not hangs
            await asyncio.sleep(0.005)
        stop.set()
        await asyncio.wait_for(task, timeout=1.0)

    asyncio.run(drive())

    counters = evaluator.counters.snapshot()
    assert counters["evaluation_errors"] == 1
    assert counters["evaluations"] >= 2


def test_evaluation_holds_the_shared_lock() -> None:
    lock = threading.Lock()
    stack = _Stack((_rule("RejectSpike"),), lock=lock)
    held: list[bool] = []
    real_tick = stack.aggregator.tick

    def spy(now: float | None = None) -> None:
        held.append(lock.locked())
        real_tick(now)

    stack.aggregator.tick = spy  # type: ignore[method-assign]
    stack.tick()

    assert held and all(held)
    assert not lock.locked()


def test_interval_must_be_positive() -> None:
    stack = _Stack((_rule("RejectSpike"),))
    with pytest.raises(ValueError):
        RuleEvaluator(
            stack.engine,
            stack.aggregator,
            stack.router,
            instance_id=_INSTANCE,
            interval_seconds=0,
        )
