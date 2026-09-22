"""Minimal walkthrough of parser/metrics_event.py: the same three-order
story as telemetry_agent.metrics.demo_quickstart (two accepted and filled,
one rejected), but starting from raw FIX log bytes through the real
FixParser instead of hand-built ParsedMessageEvent literals — end to end,
not a stand-in for it.

    uv run python -m telemetry_agent.parser.demo_metrics_bridge

Uses a fixed clock (matching the test suite's own `_fixed_now` convention,
e.g. tests/integration/agent/test_MA_integration.py) rather than
`datetime.now()`: LatencyCorrelator's TTL eviction compares event
timestamps against the real wall clock, so embedding a fixed historical
SendingTime while running for real would otherwise have every order evicted
as expired before its ack/fill arrives.
"""

from __future__ import annotations

from datetime import UTC, datetime

from telemetry_agent.metrics.aggregator import AggregatorConfig, MetricsAggregator
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.metrics.snapshot import snapshot
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.metrics_event import build_parsed_message_event
from telemetry_agent.parser.protocol import SourceMeta

_HASH_KEY = b"demo-hash-key"
_T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)

# Three orders, two accepted and filled, one rejected — the exact story
# metrics.demo_quickstart tells with hand-built events, here as raw FIX log
# bytes for the real FixParser to classify, frame and enrich.
_LINES = [
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


def _fixed_now() -> float:
    return _T0.timestamp()


def _step(title: str) -> None:
    print(f"\n--- {title} ---")


def main() -> None:
    print("=" * 60)
    print("PARSER ENGINE -> METRICS AGGREGATOR — same story, real FIX bytes")
    print("=" * 60)

    fix_parser = FixParser(hash_key=_HASH_KEY)
    config = AggregatorConfig(
        metric_dimensions={**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS}
    )
    aggregator = MetricsAggregator(config=config, clock=_fixed_now)
    correlator = LatencyCorrelator(aggregator, clock=_fixed_now)
    meta = SourceMeta(
        instance_id="magic-prod-01", path="demo", log_type="fix", read_at=_T0
    )

    _step("1. Parse raw FIX log lines and bridge each into a ParsedMessageEvent")
    events_built = 0
    for line in _LINES:
        result = fix_parser.parse(line, meta)
        event = build_parsed_message_event(result, meta)
        if event is None:
            continue
        events_built += 1
        correlator.ingest(event)
        aggregator.ingest_counters(event, derive_counters(event))
    print(f"  {events_built}/{len(_LINES)} lines became ParsedMessageEvents")

    _step("2. Read — MA-01's bucketed store, summed over the 1m window")
    row = aggregator.snapshot("1m", group_by=())[()]
    for metric, value in sorted(row.counters.items()):
        print(f"  {metric} = {value}")

    _step("3. MA-04 — same 1m window, grouped by side")
    snap = snapshot(aggregator, "1m", group_by=("side",), correlator=correlator)
    for group in sorted(snap.groups, key=lambda g: g.dimensions["side"]):
        side = group.dimensions["side"]
        fill_rate = group.indicators.fill_rate
        reject_rate = group.indicators.reject_rate
        print(
            f"  side={side:<4} fillRate={fill_rate.value}"
            f"  rejectRate={reject_rate.value}"
            f"  (denominator={reject_rate.denominator})"
        )


if __name__ == "__main__":
    main()
