"""The simulator's FIX output must give the agent real order flow.

Lines go through the agent's real parser and counter derivation, so this checks the
external contract: order counters appear, not the line text.
"""

from __future__ import annotations

import random
from collections import Counter
from datetime import UTC, datetime

from simulator.mock_logger import format_fix_line, generate_fix_order_messages
from telemetry_agent.metrics.counters import derive_counters
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.metrics_event import build_parsed_message_event
from telemetry_agent.parser.protocol import SourceMeta

_META = SourceMeta(
    instance_id="magic-prod-01",
    path="logs/Fix.log",
    log_type="fix",
    read_at=datetime(2026, 10, 22, 12, 0, tzinfo=UTC),
)
_TS = "2026-10-22 12:00:00.000"


def _counts(orders: int, reject_rate: float) -> Counter[str]:
    parser = FixParser(hash_key=b"test-key")
    totals: Counter[str] = Counter()
    for n in range(orders):
        for message in generate_fix_order_messages(f"ORD{n}", "AAPL", reject_rate):
            line = format_fix_line(_TS, message)
            event = build_parsed_message_event(
                parser.parse(line.encode(), _META), _META
            )
            assert event is not None, line
            for name, value in derive_counters(event).items():
                totals[name] += int(value)
    return totals


def test_every_order_is_counted_as_submitted() -> None:
    assert _counts(25, reject_rate=0.2)["orders_submitted"] == 25


def test_a_zero_reject_rate_acks_and_fills_every_order_with_no_rejects() -> None:
    totals = _counts(25, reject_rate=0.0)
    assert totals["orders_acked"] == 25
    assert totals["executions"] == 25
    assert totals["orders_rejected"] == 0


def test_a_full_reject_rate_rejects_every_order_with_no_fills() -> None:
    totals = _counts(25, reject_rate=1.0)
    assert totals["orders_rejected"] == 25
    assert totals["executions"] == 0


def test_the_default_mix_has_both_rejects_and_fills() -> None:
    random.seed(7)
    totals = _counts(200, reject_rate=0.2)
    assert 0 < totals["orders_rejected"] < 200
    assert totals["orders_rejected"] + totals["orders_acked"] == 200
    assert totals["executions"] == totals["orders_acked"]
