"""UBS-113: the periodic loop that drives the Rule Engine.

`RuleEngine.evaluate()` is a pure function of one `MetricsSnapshot`; something
has to build those snapshots on a schedule, feed the engine the signals that
only a clock can produce, and hand what it returns to `AlertRouter`. Before
this, only demos and tests did that by hand.

Each tick, in order:

1. a SIGHUP-requested rule reload, whose `resolved` events must be routed;
2. aging — `MetricsAggregator.tick` / `LatencyCorrelator.tick` — so an idle
   agent's counters decay and stale orders expire;
3. absence signals: FIX sessions that went silent (UBS-106), which no parsed
   line can report because the signal *is* the missing line;
4. the agent's own since-startup counters, sampled into the windowed store so
   `CallbackFailing` can see them (UBS-74/75);
5. one snapshot per rule window in use, each evaluated — plus, for windows
   with `signature` rules, one grouped by error signature, so each rule
   counts only its own pattern (UBS-122);
6. routing everything that changed (UBS-109/110).

Only reads the aggregator, correlator and session tracker it is given — who
fills them (the ingest fan-in, UBS-112) is not this module's concern. Two
things the two must agree on are documented on `RuleEvaluator`.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from typing import Any

from telemetry_shared.models.alerts import AlertEvent

from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.common.self_metrics import CounterRegistry
from telemetry_agent.metrics.agent_counters import (
    DEFAULT_AGENT_METRICS,
    PUBLISH_AGENT_METRICS,
    AgentCounterSampler,
)
from telemetry_agent.metrics.aggregator import MetricsAggregator
from telemetry_agent.metrics.correlation import LatencyCorrelator
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_agent.parser.fix.session_tracker import SessionHeartbeatTracker
from telemetry_agent.parser.metrics_event import derive_heartbeat_timeout_counters
from telemetry_agent.pipeline.alert_router import AlertRouter
from telemetry_agent.publishing.publisher import BackendPublisher
from telemetry_agent.publishing.snapshot_bridge import SnapshotEmitter
from telemetry_agent.rules.config_loader import SighupRuleReloader
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import SIGNATURE_DIMENSION, RuleKind

DEFAULT_EVALUATION_INTERVAL_SECONDS = 10.0


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RuleEvaluator:
    """Runs the Rule Engine every `interval_seconds` and routes its alerts.

    Shared conventions with the ingest side (UBS-112):

    - **Session clock.** `SessionHeartbeatTracker` compares caller-supplied
      floats, so `observe(at=...)` there and `timed_out(now)` here must use
      the same clock. Both default to `time.monotonic()`.
    - **Locking.** Nothing in `metrics/` locks. If ingest runs on another
      thread (the monitor adapter does), pass one `threading.Lock` to both
      sides; this holds it for steps 1-5 so a snapshot never iterates a dict
      that ingest is resizing. Routing happens outside it.
    """

    def __init__(
        self,
        engine: RuleEngine,
        aggregator: MetricsAggregator,
        router: AlertRouter,
        *,
        instance_id: str,
        correlator: LatencyCorrelator | None = None,
        session_tracker: SessionHeartbeatTracker | None = None,
        publisher: BackendPublisher | None = None,
        dispatcher: CallbackDispatcher | None = None,
        reloader: SighupRuleReloader | None = None,
        interval_seconds: float = DEFAULT_EVALUATION_INTERVAL_SECONDS,
        clock: Callable[[], datetime] = _utc_now,
        monotonic: Callable[[], float] = time.monotonic,
        lock: AbstractContextManager[Any] | None = None,
        counters: CounterRegistry | None = None,
        logger: logging.Logger | None = None,
        snapshot_emitter: SnapshotEmitter | None = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        self._engine = engine
        self._aggregator = aggregator
        self._router = router
        self._instance_id = instance_id
        self._correlator = correlator
        self._session_tracker = session_tracker
        self._publisher = publisher
        self._dispatcher = dispatcher
        self._reloader = reloader
        self._interval_seconds = interval_seconds
        self._clock = clock
        self._monotonic = monotonic
        self._lock: AbstractContextManager[Any] = lock or contextlib.nullcontext()
        self._counters = counters or CounterRegistry()
        self._logger = logger or logging.getLogger(__name__)
        self._reload_requested = False
        self._snapshot_emitter = snapshot_emitter
        # One sampler per registry: `AgentCounterSampler` keeps a baseline,
        # and sharing one would diff each registry against the other's.
        self._callback_sampler = AgentCounterSampler(
            aggregator, instance_id=instance_id, metrics=DEFAULT_AGENT_METRICS
        )
        self._publish_sampler = AgentCounterSampler(
            aggregator, instance_id=instance_id, metrics=PUBLISH_AGENT_METRICS
        )

    @property
    def interval_seconds(self) -> float:
        return self._interval_seconds

    @property
    def counters(self) -> CounterRegistry:
        return self._counters

    def request_reload(self) -> None:
        """Signal-safe: only sets a flag. Register it with
        `loop.add_signal_handler(signal.SIGHUP, evaluator.request_reload)`.
        The reload itself runs at the start of the next tick, under the
        lock — never mid-`evaluate()` — and its `resolved` events are routed.
        """
        self._reload_requested = True

    def evaluate_once(
        self,
        *,
        now: datetime | None = None,
        monotonic_now: float | None = None,
    ) -> list[AlertEvent]:
        """One tick. Returns every alert routed, in routing order."""
        now = now or self._clock()
        monotonic_now = self._monotonic() if monotonic_now is None else monotonic_now

        with self._lock:
            changed = self._reload(now)
            self._age(now)
            self._publish_metrics_snapshot(now)
            self._ingest_session_timeouts(now, monotonic_now)
            self._sample_agent_counters(now)
            changed.extend(self._evaluate(now))

        if changed:
            self._router.route(changed, now=now)
        self._counters.increment("evaluations")
        return changed

    async def run(self, stop: asyncio.Event | None = None) -> None:
        """Tick every `interval_seconds` until `stop` is set; the first tick
        is immediate. A tick that raises is logged and counted, never
        propagated — one bad tick must not end alerting (`NFR-REL-003`)."""
        stop = stop or asyncio.Event()
        while not stop.is_set():
            try:
                self.evaluate_once()
            except Exception:
                self._counters.increment("evaluation_errors")
                self._logger.exception("rule evaluation tick failed")
            try:
                await asyncio.wait_for(stop.wait(), timeout=self._interval_seconds)
            except TimeoutError:
                continue

    def _reload(self, now: datetime) -> list[AlertEvent]:
        if not self._reload_requested or self._reloader is None:
            return []
        self._reload_requested = False
        return self._reloader.reload(now=now)

    def _age(self, now: datetime) -> None:
        self._aggregator.tick(now.timestamp())
        if self._correlator is not None:
            self._correlator.tick()

    def _publish_metrics_snapshot(self, now: datetime) -> None:
        """UBS-115/UBS-123: publish every completed metrics bucket. Runs
        after aging, so the emitter's retention bound matches what the
        aggregator actually still holds."""
        if self._snapshot_emitter is not None:
            self._snapshot_emitter.emit(now)

    def _ingest_session_timeouts(self, now: datetime, monotonic_now: float) -> None:
        if self._session_tracker is None:
            return
        timeouts = self._session_tracker.timed_out(monotonic_now)
        for dims, counters in derive_heartbeat_timeout_counters(
            timeouts, instance_id=self._instance_id
        ):
            self._aggregator.ingest_agent_counters(dims=dims, counters=counters, at=now)

    def _sample_agent_counters(self, now: datetime) -> None:
        if self._dispatcher is not None:
            self._callback_sampler.sample(self._dispatcher.counters.snapshot(), at=now)
        if self._publisher is not None:
            self._publish_sampler.sample(self._publisher.counters.snapshot(), at=now)

    def _evaluate(self, now: datetime) -> list[AlertEvent]:
        windows = sorted({r.window for r in self._engine.rules if r.window is not None})
        if not windows:
            # Gauge-only rule set: gauges don't vary by window, any one will do.
            windows = [next(iter(self._aggregator.config.windows))]
        failures = (
            self._publisher.consecutive_failures
            if self._publisher is not None
            else None
        )
        signature_windows = {
            r.window for r in self._engine.rules if r.kind is RuleKind.SIGNATURE
        }
        changed: list[AlertEvent] = []
        for window in windows:
            group_bys: list[tuple[str, ...]] = [()]
            if window in signature_windows:
                group_bys.append((SIGNATURE_DIMENSION,))
            for group_by in group_bys:
                snap = snapshot(
                    self._aggregator,
                    window,
                    group_by=group_by,
                    correlator=self._correlator,
                    now=now,
                    consecutive_publish_failures=failures,
                )
                changed.extend(self._engine.evaluate(snap, now))
        return changed
