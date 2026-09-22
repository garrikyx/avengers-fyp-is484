"""UBS-73 integration: raw FIX log bytes -> FixParser -> metrics_event
bridge -> MetricsAggregator -> snapshot() -> RuleEngine.

`FixSessionDown`, `SeqGapDetected` and `ClockSkew` shipped with UBS-7 but
had no producer for the counters they read, so they could only ever read 0.
This proves the whole chain now carries real signal: a Logout, a sequence
jump and a batch of skewed SendingTimes in the log turn into `logouts`,
`seq_gaps` and `clock_skew_events` in the aggregator, and those fire the
three rules as configured.

Not a re-test of either side's own logic — RE-01..04 cover the FSM and the
rule table, and test_metrics_event.py covers the derivation. This covers
the seam between them, on real bytes.

Following `test_RE_04_default_rules.py`'s `_fire` convention, a rule's
`for` delay is cleared by re-evaluating the *same* snapshot at a later
`now`: the snapshot is a frozen observation, so re-presenting it models
"the condition still holds". The FSM timing itself is RE-01's subject.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.metrics_event import (
    build_parsed_message_event,
    derive_session_counters,
)
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import RuleEngine
from telemetry_agent.rules.types import RuleConfig
from telemetry_shared.models.alerts import AlertEvent

_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_KEY = b"integration-test-key"
_INSTANCE = "magic-prod-01"

# A clean session: logon, one order, its ack. Sequence numbers run 1,2,3
# with no jumps, and every SendingTime matches the read time.
_HEALTHY = [
    b"8=FIX.4.2|35=A|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|",
    b"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=2|52=20260101-10:00:00|"
    b"11=C1|55=AAPL|54=1|40=2|38=100|10=000|",
    b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=3|52=20260101-10:00:00|"
    b"11=C1|37=O1|17=E1|55=AAPL|54=1|150=0|39=0|10=000|",
]

# The session destabilises: MsgSeqNum jumps 3 -> 7 (three messages lost),
# then the counterparty logs us out.
_UNSTABLE = [
    b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=7|52=20260101-10:00:00|10=000|",
    b"8=FIX.4.2|35=5|49=MAGIC|56=EXCH1|34=8|52=20260101-10:00:00|10=000|",
]

# Eleven heartbeats whose SendingTime claims noon while the agent read them
# at 10:00 — two hours past FixParser's default five-minute max_clock_skew.
# ClockSkew's threshold is > 10, so eleven is the first firing count.
_SKEWED = [
    b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=%d|52=20260101-12:00:00|10=000|" % seq
    for seq in range(9, 20)
]


def _rule(name: str) -> RuleConfig:
    return next(r for r in DEFAULT_RULES if r.name == name)


def _ingest(lines: list[bytes]) -> MetricsAggregator:
    """The production wiring a future pipeline worker will do: parse, bridge
    to the aggregator's contract type, then merge the event-derived and
    telemetry-derived counters into one ingest call.
    """
    parser = FixParser(hash_key=_KEY)
    config = AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS))
    aggregator = MetricsAggregator(config=config, clock=lambda: _T0.timestamp())
    meta = SourceMeta(
        instance_id=_INSTANCE, path="Fix.log", log_type="fix", read_at=_T0
    )
    for line in lines:
        result = parser.parse(line, meta)
        event = build_parsed_message_event(result, meta)
        if event is None or result.telemetry is None:
            continue
        counters = derive_counters(event) | derive_session_counters(result.telemetry)
        aggregator.ingest_counters(event, counters)
    return aggregator


def _counters(aggregator: MetricsAggregator, window: str) -> dict[str, Decimal]:
    row = aggregator.snapshot(window, group_by=()).get(())
    return {} if row is None else dict(row.counters)


def _fire(rule_names: tuple[str, ...], aggregator: MetricsAggregator, window: str) -> (
    list[AlertEvent]
):
    rules = tuple(_rule(name) for name in rule_names)
    engine = RuleEngine(
        rules=rules,
        instance_id=_INSTANCE,
        application="Magic",
        agent_id="agent-sg-01",
        started_at=_T0 - timedelta(hours=1),  # past FR-RUL-019's startup grace
    )
    snap = snapshot(aggregator, window, group_by=(), now=_T0)
    engine.evaluate(snap, _T0)  # -> pending
    longest_for = max(rule.for_seconds for rule in rules)
    return engine.evaluate(snap, _T0 + timedelta(seconds=longest_for + 1))


def test_healthy_session_produces_no_session_counters_and_fires_nothing() -> None:
    aggregator = _ingest(_HEALTHY)
    counters = _counters(aggregator, "1m")
    assert counters["logons"] == Decimal(1)
    for absent in ("logouts", "seq_gaps", "seq_regressions", "clock_skew_events"):
        assert absent not in counters
    assert _fire(("FixSessionDown", "SeqGapDetected"), aggregator, "1m") == []


def test_logout_in_the_log_fires_fix_session_down_as_critical() -> None:
    aggregator = _ingest(_HEALTHY + _UNSTABLE)
    assert _counters(aggregator, "1m")["logouts"] == Decimal(1)

    alerts = _fire(("FixSessionDown",), aggregator, "1m")
    assert [alert.rule_name for alert in alerts] == ["FixSessionDown"]
    assert alerts[0].severity == "critical"
    assert alerts[0].status == "firing"
    assert alerts[0].observed_value == 1.0


def test_sequence_jump_in_the_log_fires_seq_gap_detected() -> None:
    aggregator = _ingest(_HEALTHY + _UNSTABLE)
    counters = _counters(aggregator, "1m")
    assert counters["seq_gaps"] == Decimal(1)
    # 34 jumped 3 -> 7, so one gap event covering three lost messages.
    assert counters["seq_gap_messages"] == Decimal(3)

    alerts = _fire(("SeqGapDetected",), aggregator, "1m")
    assert [alert.rule_name for alert in alerts] == ["SeqGapDetected"]
    assert alerts[0].severity == "warning"


def test_skewed_sending_times_fire_clock_skew_over_its_threshold() -> None:
    aggregator = _ingest(_HEALTHY + _UNSTABLE + _SKEWED)
    assert _counters(aggregator, "5m")["clock_skew_events"] == Decimal(11)

    alerts = _fire(("ClockSkew",), aggregator, "5m")
    assert [alert.rule_name for alert in alerts] == ["ClockSkew"]
    assert alerts[0].severity == "warning"
    assert alerts[0].observed_value == 11.0


def test_ten_skewed_messages_stay_under_the_threshold() -> None:
    """Guard against the rule firing on any skew at all — the threshold is
    > 10, so ten must not fire.
    """
    aggregator = _ingest(_HEALTHY + _SKEWED[:10])
    assert _counters(aggregator, "5m")["clock_skew_events"] == Decimal(10)
    assert _fire(("ClockSkew",), aggregator, "5m") == []


def test_fix_session_down_fires_without_any_heartbeat_timeouts_producer() -> None:
    """`FixSessionDown` sums `logouts` + `heartbeat_timeouts`, and nothing
    produces the latter yet (it needs a timer, so it belongs to the Health
    Reporter). The rule must still work off `logouts` alone rather than
    reading as insufficient data.
    """
    aggregator = _ingest(_HEALTHY + _UNSTABLE)
    assert "heartbeat_timeouts" not in _counters(aggregator, "1m")
    assert _fire(("FixSessionDown",), aggregator, "1m")[0].severity == "critical"


def test_session_counters_are_scoped_to_the_session_not_the_symbol() -> None:
    """FR-MET-030: session counters declare `SESSION_DIMS`, so they answer a
    per-session query and are absent from a per-symbol one rather than
    inventing an "unspecified" symbol label for a Logout.
    """
    aggregator = _ingest(_HEALTHY + _UNSTABLE)

    by_session = aggregator.snapshot("1m", group_by=("session_id",))
    assert by_session[("MAGIC->EXCH1",)].counters["logouts"] == Decimal(1)

    by_symbol = aggregator.snapshot("1m", group_by=("symbol",))
    assert all(
        "logouts" not in row.counters and "seq_gaps" not in row.counters
        for row in by_symbol.values()
    )
