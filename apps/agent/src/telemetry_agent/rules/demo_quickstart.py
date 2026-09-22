"""Minimal walkthrough of the Rule Engine firing on real data.

    uv run python -m telemetry_agent.rules.demo_quickstart

One FIX session's life, start to finish: it runs clean, takes a burst of
rejects, sees its reject *rate* climb, then destabilises (sequence gap,
clock skew, forced logout), and finally the agent's own callbacks to Magic
start failing — so the last thing it reports is that its own alerts aren't
getting out.

Covers UBS-7 (reject rate), UBS-72 (reject spikes), UBS-73 (FIX session
instability), UBS-74 (callback failures) and the alert-storm safety valve.
Hot-reload (`FR-RUL-008`) needs a live process to signal, so it has its own
demo: `telemetry_agent.rules.demo_reload`.

Every counter here is produced from raw FIX log bytes through the real
`FixParser` and the real `CallbackDispatcher`, not hand-built, and the rules
are read from the live `config/rules.yaml` — this exists to show the whole
chain, which `metrics/demo_quickstart.py` (aggregator only) and
`callbacks/demo_quickstart.py` (dispatch only) each cover one half of.

Uses a fixed ingest clock, like `parser/demo_metrics_bridge.py`: the windows
the rules read are minutes wide, and a wall clock would age the demo's own
events out from under it mid-run.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import httpx
from telemetry_agent.callbacks.config import parse_callbacks_config
from telemetry_agent.callbacks.dispatcher import CallbackDispatcher
from telemetry_agent.callbacks.sink import HttpsCallbackSink
from telemetry_agent.metrics.agent_counters import AgentCounterSampler
from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.metrics_event import (
    build_parsed_message_event,
    derive_parser_counters,
    derive_session_counters,
    parser_counter_dims,
)
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.rules.config_loader import load_rules
from telemetry_agent.rules.engine import RuleEngine
from telemetry_shared.models.alerts import AlertEvent
from telemetry_shared.models.metrics import MetricsSnapshot

_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_HASH_KEY = b"demo-hash-key"
_INSTANCE = "magic-prod-01"
_ENDPOINT = "https://magic.example/callbacks"

# The live rule config, so this demo and `config/rules.yaml` can never drift.
# parents[5] is the repo root: rules -> telemetry_agent -> src -> agent ->
# apps -> root. `load_rules` falls back to DEFAULT_RULES for a missing file,
# so getting this wrong would silently demo the fallback while claiming to
# read the config — hence the explicit check below rather than trusting it.
_RULES_PATH = Path(__file__).resolve().parents[5] / "config" / "rules.yaml"

_SESSION_COUNTERS = (
    "logons",
    "logouts",
    "seq_gaps",
    "seq_gap_messages",
    "seq_regressions",
    "clock_skew_events",
)


def _step(title: str) -> None:
    print(f"\n--- {title} ---")


def _show_alerts(alerts: list[AlertEvent]) -> None:
    if not alerts:
        print("  (no alerts)")
        return
    for alert in alerts:
        value = alert.observed_value
        observed = "n/a" if value is None else f"{value:g}"
        print(
            f"  [{alert.severity.upper():<8}] {alert.rule_name:<16} "
            f"{alert.status:<8} observed={observed:<7} "
            f"threshold={alert.threshold:g}  alertId={alert.alert_id[:8]}"
        )
        print(f"             {alert.matched_condition}")


class _Demo:
    """Holds the one parser/aggregator/engine trio the whole story runs on,
    so each act builds on the last rather than resetting.

    Owns the FIX sequence counter too: every line it builds is numbered in
    order, so the one deliberate gap in act 5 is the only gap in the run and
    the alert it raises is traceable to exactly one line.
    """

    def __init__(
        self,
        *,
        max_active_alerts: int = 100,
        renotify_interval_seconds: int = 1800,
        rules_path: Path = _RULES_PATH,
    ) -> None:
        if not rules_path.exists():
            msg = (
                f"rule config not found at {rules_path} — load_rules would "
                "silently fall back to DEFAULT_RULES and this demo would "
                "claim to be reading a file it never opened"
            )
            raise FileNotFoundError(msg)
        self.rules_path = rules_path
        self.parser = FixParser(hash_key=_HASH_KEY)
        self.aggregator = MetricsAggregator(
            config=AggregatorConfig(
                metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS}
            ),
            clock=lambda: _T0.timestamp(),
        )
        # The correlator gets its *own* advanceable clock, unlike the pinned
        # ingest clock: `oldest_pending_age_seconds` is measured against it,
        # so the pending-order act has to be able to move time forward. Its
        # 15-minute TTL is well past anything this demo advances by, so
        # nothing gets evicted mid-story.
        self._correlator_now = _T0.timestamp()
        self.correlator = LatencyCorrelator(
            self.aggregator, clock=lambda: self._correlator_now
        )
        self.meta = SourceMeta(
            instance_id=_INSTANCE, path="Fix.log", log_type="fix", read_at=_T0
        )
        self.rules = load_rules(rules_path)
        self.engine = RuleEngine(
            rules=self.rules,
            instance_id=_INSTANCE,
            application="Magic",
            agent_id="agent-sg-01",
            # Well before _T0: FR-RUL-019's startup grace would otherwise
            # swallow every alert in this demo.
            started_at=_T0 - timedelta(hours=1),
            max_active_alerts=max_active_alerts,
            renotify_interval_seconds=renotify_interval_seconds,
        )
        self._seq = 0
        # Engine-side clock. Advances past each rule's `for` delay so alerts
        # actually fire; the *ingest* clock stays pinned at _T0 so nothing
        # this demo feeds ages out of its window mid-story.
        self.now = _T0

    # --- line builders ---------------------------------------------------

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def skip_sequence(self, by: int) -> None:
        """Pretend `by` messages were lost in transit."""
        self._seq += by

    def logon(self) -> bytes:
        return (
            b"8=FIX.4.2|35=A|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00|10=000|"
            % self._next_seq()
        )

    def logout(self) -> bytes:
        return (
            b"8=FIX.4.2|35=5|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00|10=000|"
            % self._next_seq()
        )

    def heartbeat(self, *, sending_time: bytes = b"20260101-10:00:00") -> bytes:
        return b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=%d|52=%s|10=000|" % (
            self._next_seq(),
            sending_time,
        )

    def order(self, tag: int) -> bytes:
        return (
            b"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00|"
            b"11=C%d|55=AAPL|54=1|40=2|38=100|10=000|"
            % (self._next_seq(), tag)
        )

    def ack(self, tag: int) -> bytes:
        return (
            b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00|"
            b"11=C%d|37=O%d|17=E%d|55=AAPL|54=1|150=0|39=0|10=000|"
            % (self._next_seq(), tag, tag, tag)
        )

    def reject(self, tag: int) -> bytes:
        """ExecType/OrdStatus 8 = Rejected, OrdRejReason 3 = ExchangeClosed."""
        return (
            b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00|"
            b"11=C%d|37=O%d|17=E%d|55=AAPL|54=1|150=8|39=8|103=3|10=000|"
            % (self._next_seq(), tag, tag, tag)
        )

    def session_reject(self) -> bytes:
        """35=3, a session-level Reject — a FIX plumbing problem rather than
        a trading one, which is why it lands on `session_rejects` and never
        dilutes `orders_rejected`.
        """
        return (
            b"8=FIX.4.2|35=3|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00|"
            b"45=1|373=1|10=000|" % self._next_seq()
        )

    def cancel_reject(self, tag: int) -> bytes:
        """35=9, a rejected cancel/replace — counted as `cancel_rejects`,
        kept apart from `orders_rejected` because refusing to cancel is not
        the same failure as refusing to trade.
        """
        return (
            b"8=FIX.4.2|35=9|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00|"
            b"11=C%d|41=O%d|434=1|102=1|10=000|"
            % (self._next_seq(), tag, tag)
        )

    def slow_ack(self, tag: int, *, delay_ms: int) -> bytes:
        """An ack whose SendingTime is `delay_ms` after its order.

        Latency is measured from event timestamps, not the ingest clock, so
        this is what actually moves `ack_latency_ms` — not advancing a clock.
        """
        return (
            b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00.%03d|"
            b"11=C%d|37=O%d|17=E%d|55=AAPL|54=1|150=0|39=0|10=000|"
            % (self._next_seq(), delay_ms, tag, tag, tag)
        )

    def accepted_orders(self, count: int, *, start: int) -> list[bytes]:
        """`count` orders that each get acked — the healthy baseline volume a
        reject *rate* is measured against.
        """
        lines: list[bytes] = []
        for i in range(start, start + count):
            lines.append(self.order(i))
            lines.append(self.ack(i))
        return lines

    def rejected_orders(self, count: int, *, start: int) -> list[bytes]:
        lines: list[bytes] = []
        for i in range(start, start + count):
            lines.append(self.order(i))
            lines.append(self.reject(i))
        return lines

    # --- pipeline --------------------------------------------------------

    def feed(self, lines: list[bytes]) -> None:
        """The production wiring, all three counter families.

        Parser health is counted for *every* line, parsed or not — it's
        `parse_error_rate`'s denominator, so it can't skip the failures, and
        it has no event to hang dimensions off. Order counters come off the
        bridged event; session-health counters off the parser's own
        `FixTelemetry`.
        """
        for line in lines:
            result = self.parser.parse(line, self.meta)
            self.aggregator.ingest_agent_counters(
                dims=parser_counter_dims(result, instance_id=_INSTANCE),
                counters=derive_parser_counters(result),
                at=_T0,
            )
            event = build_parsed_message_event(result, self.meta)
            if event is None or result.telemetry is None:
                continue
            self.correlator.ingest(event)
            counters = derive_counters(event) | derive_session_counters(
                result.telemetry
            )
            self.aggregator.ingest_counters(event, counters)

    def advance_correlator(self, seconds: float) -> None:
        """Age the open-order book without aging anything else — what
        `PendingOrderTimeout`'s gauge reads.
        """
        self._correlator_now += seconds

    def snapshot(self, window: str) -> MetricsSnapshot:
        """Always with the correlator attached — that's what populates the
        `latency` summaries and the `gauges` block the rules read.
        """
        return snapshot(
            self.aggregator,
            window,
            group_by=(),
            now=self.now,
            correlator=self.correlator,
        )

    def counters(self, window: str, names: tuple[str, ...]) -> dict[str, Decimal]:
        row = self.aggregator.snapshot(window, group_by=()).get(())
        if row is None:
            return {}
        return {name: row.counters[name] for name in names if name in row.counters}

    def session_counters(self, window: str) -> dict[str, Decimal]:
        return self.counters(window, _SESSION_COUNTERS)

    def indicator(self, window: str, name: str, *, of: str) -> str:
        snap = self.snapshot(window)
        if not snap.groups:
            return "n/a"
        ind = getattr(snap.groups[0].indicators, name)
        if ind.value is None:
            return f"insufficient_data (denominator {ind.denominator})"
        return f"{ind.value:.2%} (of {ind.denominator} {of})"

    def reject_rate(self, window: str) -> str:
        return self.indicator(window, "reject_rate", of="acked+rejected")

    def ack_latency(self, window: str) -> str:
        summary = self.snapshot(window).groups[0].latency.get("ack_latency_ms")
        if summary is None:
            return "no samples"
        p95 = "null" if summary.p95 is None else f"{summary.p95:.0f}ms"
        return f"p95={p95} over {summary.count} samples"

    def gauges(self, window: str) -> str:
        g = self.snapshot(window).gauges
        age = (
            "none pending"
            if g.oldest_pending_age_seconds is None
            else f"{g.oldest_pending_age_seconds:.0f}s"
        )
        return f"pendingOrders={g.pending_orders}  oldestPendingAge={age}"

    def settle(self, window: str, *, for_seconds: int) -> list[AlertEvent]:
        """Evaluate twice: once to move a matched rule to `pending`, then
        again past its `for` delay, which is the transition that fires
        (`FR-RUL-004`). Returns only what changed — the FSM emits on
        transitions, so a still-firing alert stays quiet.
        """
        self.engine.evaluate(
            self.snapshot(window), self.now
        )
        self.now += timedelta(seconds=for_seconds + 1)
        return self.engine.evaluate(
            self.snapshot(window), self.now
        )

    def tick(self, window: str, *, advance: int = 1) -> list[AlertEvent]:
        """One evaluation a moment later — enough for a tier escalation,
        which takes effect immediately rather than re-serving the `for`
        delay (`FR-RUL-022`).
        """
        self.now += timedelta(seconds=advance)
        return self.engine.evaluate(
            self.snapshot(window), self.now
        )

    def rule_for_seconds(self, name: str) -> int:
        return next(rule.for_seconds for rule in self.rules if rule.name == name)


def _run_dispatcher_against_a_broken_magic(count: int) -> dict[str, int]:
    """`count` alerts to a Magic endpoint that answers 400 every time. A
    permanent rejection is not retried (FR-CBK-006), so each alert produces
    exactly one terminal failure — the dispatcher only ever counts a
    failure once it has given up, never per attempt.
    """
    config = parse_callbacks_config(
        {"endpoint": _ENDPOINT, "retry": {"base": "0s", "cap": "0s"}, "maxAttempts": 3}
    )
    sink = HttpsCallbackSink(
        _ENDPOINT,
        transport=httpx.MockTransport(lambda _req: httpx.Response(400)),
    )
    # Quiet the dispatcher's own error logging here — it writes to stderr,
    # which would interleave ahead of this demo's stdout narration. Watching
    # that logging happen live is `callbacks/demo_quickstart.py`'s job.
    quiet = logging.getLogger(f"{__name__}.dispatcher")
    quiet.addHandler(logging.NullHandler())
    quiet.propagate = False
    dispatcher = CallbackDispatcher(sink, config, b"demo-secret", logger=quiet)

    async def drive() -> None:
        for i in range(count):
            dispatcher.enqueue(
                AlertEvent(
                    alert_id=f"demo-alert-{i}",
                    rule_name="FixSessionDown",
                    severity="critical",
                    status="firing",
                    application="Magic",
                    instance_id=_INSTANCE,
                    agent_id="agent-sg-01",
                    matched_condition="logouts >= 1",
                    observed_value=1.0,
                    threshold=1.0,
                    first_observed_utc=_T0,
                    last_observed_utc=_T0,
                    notification_count=1,
                )
            )
        task = asyncio.create_task(dispatcher.run())
        await asyncio.sleep(0.3)
        task.cancel()

    asyncio.run(drive())
    return dispatcher.counters.snapshot()


def _no_log_activity_act() -> None:
    """UBS-20. Needs an instance that has read *nothing*, so it can't share
    the main story's aggregator — that one has thousands of messages in
    every window by this point.
    """
    quiet = _Demo()
    print("  a second instance, started but reading no log lines at all")
    print(f"  messages_total = {quiet.counters('1m', ('messages_total',)) or 0}")
    _show_alerts(
        quiet.settle("1m", for_seconds=quiet.rule_for_seconds("NoLogActivity"))
    )
    print("  While this fires, FR-RUL-021 suppresses the order-flow rules for")
    print("  this instance: absence of data is not evidence of absence of")
    print("  rejects, and alerting as though it were would be a lie.")


def _dedup_act() -> None:
    """UBS-21. Its own instance so the renotify interval can be shortened
    from the 30-minute default to something a demo can wait out.
    """
    dedup = _Demo(renotify_interval_seconds=60)
    dedup.feed([dedup.logon()])
    dedup.feed(dedup.rejected_orders(60, start=1))

    first = dedup.settle("1m", for_seconds=dedup.rule_for_seconds("RejectSpike"))
    print("  first fire:")
    _show_alerts(first)

    repeats: list[AlertEvent] = []
    for _ in range(10):
        repeats += dedup.tick("1m", advance=2)
    print(f"\n  10 more evaluations, condition still true -> {len(repeats)} alerts")
    print("  One active alert per rule+instance, not one per evaluation: the")
    print("  FSM only emits on a transition (FR-RUL-011/012).")

    print("\n  renotifyInterval = 60s here (default is 1800s). Waiting it out:")
    renotified = dedup.tick("1m", advance=61)
    _show_alerts(renotified)
    if first and renotified:
        print(f"  same alertId: {first[0].alert_id == renotified[0].alert_id}")
        print(
            f"  notificationCount {first[0].notification_count} -> "
            f"{renotified[0].notification_count} — a reminder about the same"
        )
        print("  incident, not a second incident")


def _alert_storm_act() -> None:
    """A deliberately tiny `maxActiveAlerts` so the safety valve is visible.

    Production default is 100 (`FR-RUL-017`) — at demo scale nothing would
    ever reach that, so this act runs its own `_Demo` with a cap of 3 rather
    than pretending the main story hit a hundred concurrent alerts.
    """
    storm = _Demo(max_active_alerts=3)

    # Everything goes wrong at once: session down, sequence gap, a reject
    # burst, clock skew, and a run of session-level rejects — five rules
    # across the 1m and 5m windows, against a cap of three.
    storm.feed([storm.logon(), storm.logout()])
    storm.skip_sequence(4)
    storm.feed([storm.heartbeat()])
    storm.feed(storm.rejected_orders(51, start=90_000))
    storm.feed([storm.heartbeat(sending_time=b"20260101-12:00:00") for _ in range(11)])
    storm.feed([storm.session_reject() for _ in range(6)])

    print("  maxActiveAlerts = 3 (production default is 100)")
    fired: list[AlertEvent] = []
    for _ in range(3):
        for window in ("1m", "5m"):
            fired += storm.tick(window, advance=61)

    _show_alerts(fired)
    storms = [alert for alert in fired if alert.rule_name == "AlertStorm"]
    suppressed = [alert for alert in fired if alert.rule_name != "AlertStorm"]
    print(
        f"  {len(suppressed)} alerts notified, then the cap held at "
        f"{storm.engine.active_alert_count()} active"
    )
    print(
        f"  AlertStorm events emitted: {len(storms)} — the cap pages once, not"
    )
    print("  once per suppressed alert, so a cascading outage can't self-DoS")


def _part(title: str) -> None:
    print(f"\n{'=' * 72}\n  {title}\n{'=' * 72}")


def main() -> None:
    demo = _Demo()

    print("=" * 72)
    print("RULE ENGINE — one FIX session from healthy to falling apart")
    print(f"rules: {len(demo.rules)} loaded from config/rules.yaml")
    print("=" * 72)

    _part("PART 1 — order-flow alerts  (UBS-7, UBS-72, UBS-17, UBS-19)")

    _step("1. A healthy session — logon, 2000 orders, every one acked")
    demo.feed([demo.logon()])
    demo.feed(demo.accepted_orders(2000, start=1))
    print(f"  rejectRate = {demo.reject_rate('5m')}")
    print(f"  session counters: {demo.session_counters('1m')}")
    _show_alerts(demo.settle("1m", for_seconds=60))

    _step("2. UBS-72 — a burst of 51 rejects, but the *rate* stays low")
    demo.feed(demo.rejected_orders(51, start=10_000))
    print(f"  orders_rejected = {demo.counters('1m', ('orders_rejected',))}")
    print(f"  rejectRate      = {demo.reject_rate('5m')}")
    print("  HighRejectRate's warning tier is 3% and the rate is under it, so a")
    print("  percentage-only rule stays silent at this volume. RejectSpike")
    print("  (> 50 in 1m) is the one that catches the absolute burst:")
    _show_alerts(demo.settle("1m", for_seconds=demo.rule_for_seconds("RejectSpike")))

    _step("3. UBS-72 — 21 cancels refused, the other half of the same story")
    demo.feed([demo.cancel_reject(i) for i in range(40_000, 40_021)])
    print(f"  cancel_rejects = {demo.counters('5m', ('cancel_rejects',))}")
    print("  Refusing to cancel is a different failure from refusing to trade,")
    print("  so it gets its own counter and its own rule:")
    _show_alerts(
        demo.settle("5m", for_seconds=demo.rule_for_seconds("CancelRejectSpike"))
    )

    _step("4. UBS-7 — now the reject rate itself climbs, warning -> critical")
    demo.feed(demo.rejected_orders(19, start=20_000))
    print(f"  rejectRate = {demo.reject_rate('5m')}  (past the 3% warning tier)")
    warning = demo.settle("5m", for_seconds=demo.rule_for_seconds("HighRejectRate"))
    _show_alerts(warning)

    demo.feed(demo.rejected_orders(45, start=30_000))
    print(f"\n  rejectRate = {demo.reject_rate('5m')}  (past the 5% critical tier)")
    critical = demo.tick("5m")
    _show_alerts(critical)
    if warning and critical:
        print(f"  same alertId across the escalation: "
              f"{warning[0].alert_id == critical[0].alert_id}")
        print("  FR-RUL-022 raises the severity of the alert already open rather")
        print("  than opening a second one — one incident, not two pages")

    _step("5. UBS-17 — six session-level rejects, a FIX plumbing problem")
    demo.feed([demo.session_reject() for _ in range(6)])
    print(f"  session_rejects = {demo.counters('5m', ('session_rejects',))}")
    _show_alerts(demo.settle("5m", for_seconds=demo.rule_for_seconds("SessionRejects")))

    # Enough slow acks to actually move the 95th percentile: with 2000 fast
    # acks already in the window, anything under ~105 slow ones leaves p95
    # sitting inside the fast group. That is the rule behaving correctly —
    # a p95 is meant to ignore a handful of outliers — so the demo has to
    # show a real degradation, not a blip.
    _step("6. UBS-19 — 220 orders acked 800ms late, enough to move the p95")
    demo.feed(
        [
            line
            for i in range(50_000, 50_220)
            for line in (demo.order(i), demo.slow_ack(i, delay_ms=800))
        ]
    )
    print(f"  ack latency: {demo.ack_latency('5m')}")
    print("  AckLatencyBreach wants >= 50 samples before it trusts a p95 — a")
    print("  stricter bar than the rate rules' 20, since a percentile is")
    print("  unstable at low counts:")
    _show_alerts(
        demo.settle("5m", for_seconds=demo.rule_for_seconds("AckLatencyBreach"))
    )

    _part("PART 2 — session and delivery alerts  (UBS-73, UBS-74)")

    _step("7. UBS-73 — MsgSeqNum jumps, so four messages were lost in transit")
    demo.skip_sequence(4)
    gap_line = demo.heartbeat()
    print(f"  {gap_line.decode()}")
    demo.feed([gap_line])
    print(f"  session counters: {demo.session_counters('1m')}")
    _show_alerts(demo.settle("1m", for_seconds=demo.rule_for_seconds("SeqGapDetected")))

    _step("8. UBS-73 — 11 messages timestamped two hours in the future")
    skewed = [demo.heartbeat(sending_time=b"20260101-12:00:00") for _ in range(11)]
    print(f"  {skewed[0].decode()}   (x{len(skewed)})")
    demo.feed(skewed)
    print(f"  clock_skew_events = {demo.session_counters('5m')['clock_skew_events']}")
    print("  ClockSkew's threshold is > 10, so the 11th is the one that trips it")
    _show_alerts(demo.settle("5m", for_seconds=demo.rule_for_seconds("ClockSkew")))

    _step("9. UBS-73 — the counterparty finally logs us out")
    logout_line = demo.logout()
    print(f"  {logout_line.decode()}")
    demo.feed([logout_line])
    print(f"  session counters: {demo.session_counters('1m')}")
    _show_alerts(demo.settle("1m", for_seconds=demo.rule_for_seconds("FixSessionDown")))

    _step("10. UBS-74 — Magic rejects every callback the agent sends it")
    registry = _run_dispatcher_against_a_broken_magic(4)
    print(f"  dispatcher's own counters: {registry}")
    AgentCounterSampler(demo.aggregator, instance_id=_INSTANCE).sample(
        registry, at=_T0
    )
    print("  sampled into the aggregator as a delta, not an absolute count —")
    print("  the registry counts since startup, the rule asks 'in the last 5m'")
    _show_alerts(
        demo.settle("5m", for_seconds=demo.rule_for_seconds("CallbackFailing"))
    )

    _part("PART 3 — absence, parser health, lifecycle, safety")

    # NoExecutions must come before anything that produces a fill (150=F):
    # one execution anywhere in the 15m window and this rule correctly goes
    # quiet. Nothing in this demo fills an order today — keep it that way, or
    # move this act ahead of whatever does.
    _step("11. UBS-17 — orders submitted all session, not one execution")
    print(f"  {demo.counters('15m', ('orders_submitted', 'executions'))}")
    print("  Guarded on orders_submitted > 0, so a genuinely idle instance")
    print("  stays quiet rather than paging about a quiet market:")
    _show_alerts(demo.settle("15m", for_seconds=demo.rule_for_seconds("NoExecutions")))

    _step("12. UBS-17 — an order that never got a response at all")
    demo.feed([demo.order(60_000)])
    print(f"  gauges: {demo.gauges('1m')}")
    demo.advance_correlator(45)
    print(f"  45s later: {demo.gauges('1m')}")
    print("  Measures time to *first response* (ack or cancel outcome), never")
    print("  time to fill — a resting limit order is not a stuck one:")
    _show_alerts(
        demo.settle("1m", for_seconds=demo.rule_for_seconds("PendingOrderTimeout"))
    )

    _step("13. UBS-18 — the log starts emitting lines the parser can't frame")
    def rate() -> str:
        return demo.indicator("5m", "parse_error_rate", of="lines read")

    print(f"  before: parseErrorRate = {rate()}")
    demo.feed([b"8=FIX.4.2|35=D|49=SENDER|56=T|34=999"] * 200)
    print(f"  after:  parseErrorRate = {rate()}")
    print("  Warning at 1%; the critical tier is 25%, which at this line volume")
    print("  would mean the log had become mostly unparseable. Deliberately not")
    print("  suppressed by NoLogActivity — it has to keep evaluating when the")
    print("  log pipeline itself is what's going wrong:")
    _show_alerts(demo.settle("5m", for_seconds=demo.rule_for_seconds("ParseErrorRate")))

    _step("14. UBS-20 — a different instance goes completely silent")
    _no_log_activity_act()

    _step("15. UBS-21 — one alert per incident, however often it's evaluated")
    _dedup_act()

    _step("16. UBS-76 — an alert storm collapses into one meta-alert")
    _alert_storm_act()

    _part("Closing")
    print("  Every alert above was produced locally, on the agent, from log")
    print("  bytes — no backend involved. Act 10 is the agent noticing that its")
    print("  own alerts are not reaching Magic, which is exactly the failure a")
    print("  centrally-hosted alerting system could not report (NFR-REL-003).")
    print("\n  Not shown: BackendUnreachable (UBS-75) reads publish_failures,")
    print("  which needs the Backend Publisher — not built yet.")
    print("\n  Hot-reload (FR-RUL-008) needs a live process to signal:")
    print("      make rules-reload-demo")


if __name__ == "__main__":
    main()
