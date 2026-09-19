"""FR-PRS-027 sequence gap tests."""

from __future__ import annotations

from telemetry_agent.parser.fix.seq_tracker import SeqTracker


def test_FR_PRS_027_detects_gap() -> None:
    tracker = SeqTracker()
    tracker.observe(msg_type="Logon", seq_num="1", sender="A", target="B")
    tracker.observe(msg_type="Heartbeat", seq_num="2", sender="A", target="B")
    gap = tracker.observe(msg_type="Heartbeat", seq_num="5", sender="A", target="B")
    assert gap is not None
    assert gap.is_regression is False
    assert gap.gap_size == 2


def test_FR_PRS_027_detects_regression() -> None:
    tracker = SeqTracker()
    tracker.observe(msg_type="Logon", seq_num="10", sender="A", target="B")
    gap = tracker.observe(msg_type="Heartbeat", seq_num="8", sender="A", target="B")
    assert gap is not None
    assert gap.is_regression is True


def test_FR_PRS_027_logon_resets_without_gap() -> None:
    tracker = SeqTracker()
    tracker.observe(msg_type="Heartbeat", seq_num="5", sender="A", target="B")
    reset = tracker.observe(msg_type="Logon", seq_num="1", sender="A", target="B")
    assert reset is None
    gap = tracker.observe(msg_type="Heartbeat", seq_num="2", sender="A", target="B")
    assert gap is None
