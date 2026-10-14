"""UBS-112: MetricsIngestor feeds one parse result into the aggregator,
latency correlator, session tracker and Health Reporter, once each."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.pipeline.ingest import MetricsIngestor
from telemetry_agent.pipeline.types import ParsedEvent

T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
INSTANCE = "magic-prod-01"

# Three orders: two acked and filled, one rejected (the metrics demo's story).
STORY = [
    b"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|"
    b"11=C1|55=AAPL|54=1|40=2|38=100|10=000|",
    b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=2|52=20260101-10:00:00.008|"
    b"11=C1|37=O1|17=E1|55=AAPL|54=1|150=0|39=0|10=000|",
    b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=3|52=20260101-10:00:00.030|"
    b"11=C1|37=O1|17=E2|55=AAPL|54=1|150=F|39=2|32=100|151=0|10=000|",
    b"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=4|52=20260101-10:00:00|"
    b"11=C2|55=MSFT|54=1|40=2|38=50|10=000|",
    b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=5|52=20260101-10:00:00.005|"
    b"11=C2|37=O2|17=E3|55=MSFT|54=1|150=0|39=0|10=000|",
    b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=6|52=20260101-10:00:00.018|"
    b"11=C2|37=O2|17=E4|55=MSFT|54=1|150=F|39=2|32=50|151=0|10=000|",
    b"8=FIX.4.2|35=D|49=MAGIC|56=EXCH1|34=7|52=20260101-10:00:00|"
    b"11=C3|55=GOOG|54=2|40=1|38=200|10=000|",
    b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=8|52=20260101-10:00:00|"
    b"11=C3|37=O3|17=E5|55=GOOG|54=2|150=8|39=8|103=3|10=000|",
]
NO_MSG_TYPE = b"8=FIX.4.2|35=|49=MAGIC|56=EXCH1|10=000|"  # hard parse error
BAD_TIMESTAMP = (
    b"8=FIX.4.2|35=8|49=MAGIC|56=EXCH1|34=9|52=notatime|"
    b"11=C9|37=O9|17=E9|55=AMD|54=1|150=0|39=0|10=000|"
)
LOGON = b"8=FIX.4.2|35=A|49=MAGIC|56=EXCH1|34=1|52=20260101-10:00:00|10=000|"
LOGOUT = b"8=FIX.4.2|35=5|49=MAGIC|56=EXCH1|34=2|52=20260101-10:00:01|10=000|"


def _meta() -> SourceMeta:
    return SourceMeta(instance_id=INSTANCE, path="Fix.log", log_type="fix", read_at=T0)


def _reporter() -> HealthReporter:
    return HealthReporter({}, heartbeat=HeartbeatConfig(agent_id="a"), clock=lambda: T0)


def _ingestor(**kw: object) -> MetricsIngestor:
    return MetricsIngestor.build_default(
        clock=lambda: T0.timestamp(),
        monotonic=lambda: 100.0,
        **kw,  # type: ignore[arg-type]
    )


def _feed(ingestor: MetricsIngestor, lines: list[bytes]) -> None:
    parser = FixParser(hash_key=b"unit-test-key")
    for line in lines:
        ingestor.ingest(parser.parse(line, _meta()), _meta())


def _counters(ingestor: MetricsIngestor) -> dict[str, Decimal]:
    return dict(ingestor.aggregator.snapshot("1m", group_by=())[()].counters)


def test_story_lines_reach_the_aggregator_and_correlator() -> None:
    ingestor = _ingestor()
    _feed(ingestor, STORY)

    counters = _counters(ingestor)
    assert counters["log_lines_read"] == 8
    assert counters["orders_submitted"] == 3
    assert counters["orders_acked"] == 2
    assert counters["orders_rejected"] == 1
    assert counters["fills_full"] == 2
    assert counters["executed_qty"] == 150
    # The correlator turned order -> ack pairs into latency observations.
    histograms = ingestor.aggregator.snapshot("1m", group_by=())[()].histograms
    assert "ack_latency_ms" in histograms
    assert ingestor.stats() == {
        "lines_ingested": 8,
        "events_built": 8,
        "ingest_errors": 0,
    }


def test_a_hard_parse_error_counts_for_aggregator_and_reporter() -> None:
    reporter = _reporter()
    ingestor = _ingestor(health_reporter=reporter)
    _feed(ingestor, [STORY[0], NO_MSG_TYPE])

    counters = _counters(ingestor)
    assert counters["log_lines_read"] == 2  # failures are in the denominator
    assert counters["parse_errors"] == 1
    signals = reporter.snapshot()
    assert signals.lines_read == 2
    assert signals.parse_error_count == 1


def test_bad_timestamp_is_a_heartbeat_error_but_not_an_aggregator_one() -> None:
    """Known, documented difference (UBS-59 vs MA): the heartbeat counts an
    unreadable SendingTime as a parse error, the aggregator does not."""
    reporter = _reporter()
    ingestor = _ingestor(health_reporter=reporter)
    _feed(ingestor, [BAD_TIMESTAMP])

    assert reporter.snapshot().parse_error_count == 1
    assert "parse_errors" not in _counters(ingestor)
    assert _counters(ingestor)["log_lines_read"] == 1


def test_session_tracker_sees_the_session_and_logout_forgets_it() -> None:
    ingestor = _ingestor()
    tracker = ingestor.session_tracker
    assert tracker is not None

    _feed(ingestor, [LOGON])
    assert len(tracker.tracked_sessions()) == 1
    _feed(ingestor, [LOGOUT])
    assert tracker.tracked_sessions() == ()


def test_a_failing_component_never_escapes_and_is_counted() -> None:
    """The committer acks the offset before calling on_event, so an exception
    here would drop the rest of the drained batch."""

    class Boom:
        def record_parse_result(self, *_: object, **__: object) -> None:
            raise RuntimeError("reporter broke")

    ingestor = _ingestor(health_reporter=Boom())
    _feed(ingestor, STORY[:2])  # must not raise

    assert ingestor.stats()["ingest_errors"] == 2
    assert ingestor.stats()["lines_ingested"] == 2
    assert _counters(ingestor)["orders_submitted"] == 1  # earlier steps still ran


def test_optional_components_can_be_left_out() -> None:
    from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
    from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS

    aggregator = MetricsAggregator(
        config=AggregatorConfig(metric_dimensions=dict(COUNTER_DIMENSIONS)),
        clock=lambda: T0.timestamp(),
    )
    ingestor = MetricsIngestor(aggregator)
    _feed(ingestor, STORY)

    assert _counters(ingestor)["orders_submitted"] == 3
    assert ingestor.stats()["ingest_errors"] == 0


def test_on_event_is_the_committer_adapter() -> None:
    reporter = _reporter()
    ingestor = _ingestor(health_reporter=reporter)
    result = FixParser(hash_key=b"unit-test-key").parse(STORY[0], _meta())

    ingestor.on_event(ParsedEvent(meta=_meta(), result=result, line=STORY[0]))

    assert _counters(ingestor)["orders_submitted"] == 1
    assert reporter.snapshot().lines_read == 1


@pytest.mark.parametrize("bad", [b"", b"garbage", b"\xff\xfe"])
def test_junk_lines_are_counted_not_fatal(bad: bytes) -> None:
    ingestor = _ingestor(health_reporter=_reporter())
    _feed(ingestor, [bad])
    assert ingestor.stats() == {
        "lines_ingested": 1,
        "events_built": 0,
        "ingest_errors": 0,
    }
