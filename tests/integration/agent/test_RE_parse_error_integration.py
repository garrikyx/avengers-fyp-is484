"""UBS-18 integration: raw log bytes -> FixParser -> derive_parser_counters
-> MetricsAggregator -> snapshot() -> RuleEngine.

`ParseErrorRate` shipped with UBS-7 reading `parse_error_rate`, whose
numerator and denominator (`parse_errors` / `log_lines_read`, spec 004 §4.5)
were never declared as counters — they lived only in `metrics/demo_sink.py`
as a plain dict for the parser CLI. The rule therefore read
`insufficient_data` forever. This proves the producer closes that gap.

Unlike the order counters, these ride `ingest_agent_counters`: a line that
fails to parse produces no `ParsedMessageEvent` to read dimensions off.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.metrics_event import (
    derive_parser_counters,
    parser_counter_dims,
)
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.rules.defaults import DEFAULT_RULES
from telemetry_agent.rules.engine import RuleEngine
from telemetry_shared.models.alerts import AlertEvent

_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
_KEY = b"integration-test-key"
_INSTANCE = "magic-prod-01"

_GOOD = b"8=FIX.4.2|35=0|49=MAGIC|56=EXCH1|34=%d|52=20260101-10:00:00|10=000|"

# Two genuinely different failure modes, because they count differently.
#
# `_UNFRAMEABLE` has no checksum, so `LineJoiner` holds it as a possible
# continuation and only reports `incomplete_message` when it gives up after
# max_join_lines. Three of every four are absorbed, which caps this mode's
# achievable error rate just under 25% no matter how many arrive — it can
# never reach the critical tier on its own.
#
# `_NO_MSG_TYPE` carries a checksum, so it reaches the framer immediately and
# fails outright, one error per line.
_UNFRAMEABLE = b"8=FIX.4.2|35=D|49=SENDER|56=T|34=2"
_NO_MSG_TYPE = b"8=FIX.4.2|35=|49=MAGIC|56=EXCH1|10=000|"


def _ingest(
    good: int, bad: int, *, bad_line: bytes = _UNFRAMEABLE
) -> MetricsAggregator:
    parser = FixParser(hash_key=_KEY)
    aggregator = MetricsAggregator(
        config=AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS)),
        clock=lambda: _T0.timestamp(),
    )
    meta = SourceMeta(
        instance_id=_INSTANCE, path="Fix.log", log_type="fix", read_at=_T0
    )
    lines = [_GOOD % i for i in range(1, good + 1)] + [bad_line] * bad
    for line in lines:
        result = parser.parse(line, meta)
        aggregator.ingest_agent_counters(
            dims=parser_counter_dims(result, instance_id=_INSTANCE),
            counters=derive_parser_counters(result),
            at=_T0,
        )
    return aggregator


def _fire(aggregator: MetricsAggregator) -> list[AlertEvent]:
    rule = next(r for r in DEFAULT_RULES if r.name == "ParseErrorRate")
    engine = RuleEngine(
        rules=(rule,),
        instance_id=_INSTANCE,
        application="Magic",
        agent_id="agent-sg-01",
        started_at=_T0 - timedelta(hours=1),
    )
    snap = snapshot(aggregator, "5m", group_by=(), now=_T0)
    engine.evaluate(snap, _T0)  # -> pending
    return engine.evaluate(snap, _T0 + timedelta(seconds=rule.for_seconds + 1))


def _rate(aggregator: MetricsAggregator) -> float | None:
    return snapshot(aggregator, "5m", group_by=(), now=_T0).groups[
        0
    ].indicators.parse_error_rate.value


def test_a_clean_log_never_fires() -> None:
    aggregator = _ingest(good=100, bad=0)
    row = aggregator.snapshot("5m", group_by=())[()]
    assert row.counters["log_lines_read"] == Decimal(100)
    assert "parse_errors" not in row.counters
    assert _rate(aggregator) == 0.0
    assert _fire(aggregator) == []


def test_unparseable_lines_fire_parse_error_rate() -> None:
    # 40 unframeable lines yield 10 give-ups (LineJoiner buffers 4 at a
    # time), so 10/140 ≈ 7.1% — over the 1% warning tier.
    aggregator = _ingest(good=100, bad=40)
    row = aggregator.snapshot("5m", group_by=())[()]
    assert row.counters["log_lines_read"] == Decimal(140)
    assert row.counters["parse_errors"] == Decimal(10)

    alerts = _fire(aggregator)
    assert [alert.rule_name for alert in alerts] == ["ParseErrorRate"]
    assert alerts[0].severity == "warning"


def test_a_mostly_unparseable_log_escalates_to_critical() -> None:
    """Needs a failure mode that errors once per line — see `_NO_MSG_TYPE`.
    The buffered `incomplete_message` mode asymptotes just below 25% and
    could never reach this tier however many bad lines arrive.
    """
    aggregator = _ingest(good=10, bad=30, bad_line=_NO_MSG_TYPE)
    rate = _rate(aggregator)
    assert rate is not None and rate > 0.25
    assert _fire(aggregator)[0].severity == "critical"


def test_buffered_failures_alone_cannot_reach_the_critical_tier() -> None:
    """Documents the asymptote above as behaviour, not accident: three of
    every four unframeable lines are absorbed as possible continuations, so
    this mode tops out just under the 25% critical threshold.
    """
    rate = _rate(_ingest(good=1, bad=4000))
    assert rate is not None
    assert 0.24 < rate < 0.25


def test_below_min_samples_reads_insufficient_data_not_a_fire() -> None:
    """`min_samples` is 20 for this rule. Under that, a single bad line in a
    handful would otherwise read as a catastrophic error rate.
    """
    aggregator = _ingest(good=4, bad=8)
    row = aggregator.snapshot("5m", group_by=())[()]
    assert row.counters["log_lines_read"] < Decimal(20)
    assert _fire(aggregator) == []


def test_errors_are_attributable_to_a_reason() -> None:
    """spec 004 §4.3 gives `parse_errors` a `reason` dimension so a spike
    can be pinned to one failure mode rather than just counted.
    """
    parser = FixParser(hash_key=_KEY)
    aggregator = MetricsAggregator(
        config=AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS)),
        clock=lambda: _T0.timestamp(),
    )
    meta = SourceMeta(
        instance_id=_INSTANCE, path="Fix.log", log_type="fix", read_at=_T0
    )
    for line in [_UNFRAMEABLE] * 40 + [_NO_MSG_TYPE] * 7:
        result = parser.parse(line, meta)
        aggregator.ingest_agent_counters(
            dims=parser_counter_dims(result, instance_id=_INSTANCE),
            counters=derive_parser_counters(result),
            at=_T0,
        )

    by_reason = aggregator.snapshot("5m", group_by=("instance_id", "reason"))
    errors = {
        label[1]: row.counters["parse_errors"]
        for label, row in by_reason.items()
        if "parse_errors" in row.counters
    }
    # Two distinct failure modes, separately attributable rather than
    # collapsed into one opaque count.
    assert errors == {"incomplete_message": Decimal(10), "no_msg_type": Decimal(7)}
