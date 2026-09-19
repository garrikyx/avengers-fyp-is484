"""RE-05: Metrics Aggregator -> snapshot() -> Rule Engine, using real
`MetricsAggregator`/`LatencyCorrelator`/`snapshot()` objects instead of the
hand-built `MetricsSnapshot` fixtures the rest of the rules test suite uses.

Not a re-test of either side's own logic — MA-01-04's 101 tests and RE's 44
already cover that exhaustively. This exists to prove the *shape* `snapshot()`
actually emits matches what RuleEngine's evaluators actually read: one rule
per snapshot substructure (`indicators`, `latency`, `gauges`, `counters`).

Uses hand-built `ParsedMessageEvent` objects, same as MA-04's own tests —
Log Monitor and the Parser Engine's field extraction don't exist yet
(that integration test is separate, later scope).
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import RuleConfig, RuleKind, SeverityTier, ValueSource
from telemetry_shared.models.metrics import MetricsSnapshot
from telemetry_shared.models.parsed_message import (
    ExecutionReportEvent,
    NewOrderEvent,
    ParsedMessageEvent,
)

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
_ENVELOPE = dict(instance_id="magic-prod-01", session_id="MAGIC->EXCH1")


class _Clock:
    """Mutable clock shared by the aggregator and correlator, same pattern
    as `tests/unit/agent/metrics/fixtures.py`'s `FakeClock` — not imported
    from there directly, since both metrics/ and rules/ ship a same-named
    `fixtures.py`/`rule_fixtures.py` and pytest's rootless import mode
    would make cross-importing between them ambiguous.
    """

    def __init__(self, start: float) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


def _new_order(cl_ord_id_hash: str, symbol: str) -> NewOrderEvent:
    return NewOrderEvent(
        **_ENVELOPE,
        event_time_utc=_T0,
        cl_ord_id_hash=cl_ord_id_hash,
        symbol=symbol,
        side="buy",
        ord_type="limit",
        order_qty=Decimal(100),
    )


def _ack(
    cl_ord_id_hash: str,
    order_id_hash: str,
    exec_id_hash: str,
    symbol: str,
    delay_ms: int,
) -> ExecutionReportEvent:
    return ExecutionReportEvent(
        **_ENVELOPE,
        event_time_utc=_T0 + timedelta(milliseconds=delay_ms),
        cl_ord_id_hash=cl_ord_id_hash,
        order_id_hash=order_id_hash,
        exec_id_hash=exec_id_hash,
        exec_type="New",
        ord_status="New",
        symbol=symbol,
        side="buy",
    )


def _rejected(
    cl_ord_id_hash: str, order_id_hash: str, exec_id_hash: str, symbol: str
) -> ExecutionReportEvent:
    return ExecutionReportEvent(
        **_ENVELOPE,
        event_time_utc=_T0,
        cl_ord_id_hash=cl_ord_id_hash,
        order_id_hash=order_id_hash,
        exec_id_hash=exec_id_hash,
        exec_type="Rejected",
        ord_status="Rejected",
        symbol=symbol,
        side="buy",
        reject_reason_code="OrderExceedsLimit",
    )


def _session_reject() -> ParsedMessageEvent:
    return ParsedMessageEvent(
        **_ENVELOPE, event_time_utc=_T0, msg_type="Reject", reject_reason_text="garbled"
    )


def _ingest(
    aggregator: MetricsAggregator,
    correlator: LatencyCorrelator,
    event: ParsedMessageEvent,
) -> None:
    aggregator.ingest_counters(event, derive_counters(event))
    correlator.ingest(event)


def test_real_snapshot_output_drives_the_rule_engine_correctly() -> None:
    clock = _Clock(_T0.timestamp())
    config = AggregatorConfig(
        metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS}
    )
    aggregator = MetricsAggregator(config=config, clock=clock)
    correlator = LatencyCorrelator(aggregator, clock=clock)

    # indicators path: 3 acked + 1 rejected -> rejectRate 25%. The 3 acks
    # also feed the latency path (ack_latency_ms).
    for i, symbol in enumerate(("AAPL", "MSFT", "GOOG")):
        _ingest(aggregator, correlator, _new_order(f"ORD-{i}", symbol))
        _ingest(
            aggregator,
            correlator,
            _ack(f"ORD-{i}", f"OID-{i}", f"EXEC-{i}", symbol, delay_ms=50 + i * 10),
        )
    _ingest(aggregator, correlator, _new_order("ORD-REJ", "TSLA"))
    _ingest(aggregator, correlator, _rejected("ORD-REJ", "OID-REJ", "EXEC-REJ", "TSLA"))

    # gauges path: an order that never gets acked.
    _ingest(aggregator, correlator, _new_order("ORD-STUCK", "AMZN"))

    # counters path: session-level rejects.
    for _ in range(3):
        _ingest(aggregator, correlator, _session_reject())

    clock.advance(5)  # so the stuck order's pending age is observable

    rules = (
        RuleConfig(
            name="RejectRate",
            kind=RuleKind.RATE,
            source=ValueSource.INDICATOR,
            metric="reject_rate",
            operator=">",
            tiers=(SeverityTier("warning", Decimal("0.1")),),
            window="5m",
            min_samples=2,
            for_seconds=0,
            resolve_after_seconds=0,
        ),
        RuleConfig(
            name="AckLatency",
            kind=RuleKind.LATENCY,
            source=ValueSource.LATENCY_P95,
            metric="ack_latency_ms",
            operator=">",
            tiers=(SeverityTier("warning", Decimal(10)),),
            window="5m",
            min_samples=2,
            for_seconds=0,
            resolve_after_seconds=0,
        ),
        RuleConfig(
            name="StuckOrder",
            kind=RuleKind.THRESHOLD,
            source=ValueSource.GAUGE,
            metric="oldest_pending_age_seconds",
            operator=">",
            tiers=(SeverityTier("warning", Decimal(1)),),
            window=None,
            for_seconds=0,
            resolve_after_seconds=0,
        ),
        RuleConfig(
            name="SessionRejects",
            kind=RuleKind.THRESHOLD,
            source=ValueSource.COUNTER,
            metric="session_rejects",
            operator=">",
            tiers=(SeverityTier("warning", Decimal(2)),),
            window="5m",
            for_seconds=0,
            resolve_after_seconds=0,
        ),
    )
    engine = RuleEngine(
        rules=rules,
        instance_id="magic-prod-01",
        application="Magic",
        agent_id="agent-1",
        started_at=_T0 - timedelta(hours=1),
    )

    def _snapshot_now() -> MetricsSnapshot:
        now = datetime.fromtimestamp(clock(), tz=UTC)
        # min_sample_size must be <= the smallest rule.min_samples that reads
        # a latency percentile — snapshot() nulls p95 below its own
        # min_sample_size regardless of what the rule itself would accept
        # (unlike indicators, which only null on denominator == 0). Real
        # callers must size this from their configured rule set, not just
        # take MA-04's default(20).
        return snapshot(
            aggregator, "5m", correlator=correlator, min_sample_size=2, now=now
        )

    engine.evaluate(
        _snapshot_now(), datetime.fromtimestamp(clock(), tz=UTC)
    )  # -> pending
    clock.advance(1)
    events = engine.evaluate(_snapshot_now(), datetime.fromtimestamp(clock(), tz=UTC))

    fired = {event.rule_name: event for event in events}
    assert set(fired) == {"RejectRate", "AckLatency", "StuckOrder", "SessionRejects"}
    assert all(event.status == "firing" for event in fired.values())
    assert all(event.observed_value is not None for event in fired.values())
    assert fired["RejectRate"].observed_value == 0.25
    assert fired["SessionRejects"].observed_value == 3.0
    assert fired["StuckOrder"].observed_value is not None
    assert fired["StuckOrder"].observed_value >= 5.0
    assert fired["AckLatency"].observed_value is not None
    assert fired["AckLatency"].observed_value > 10.0
