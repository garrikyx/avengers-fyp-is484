"""UBS-106: SessionHeartbeatTracker — the `heartbeat_timeouts` producer.

A heartbeat timeout is the absence of a message, so the interesting
behaviour is all about *not* over-reporting: one event per silence, not one
per tick, and a clean logout that is not a timeout at all.
"""

from telemetry_agent.parser.fix.seq_tracker import SeqTracker
from telemetry_agent.parser.fix.session_tracker import (
    DEFAULT_SESSION_TIMEOUT_SECONDS,
    SessionHeartbeatTracker,
)
from telemetry_agent.parser.fix.telemetry import session_id_for


def _keys(timeouts) -> tuple[str, ...]:
    """Session keys from a timed_out() result, for terse assertions."""
    return tuple(t.session_key for t in timeouts)

_SENDER = "MAGIC"
_TARGET = "EXCH1"


def _tracker(timeout: float = 60.0) -> SessionHeartbeatTracker:
    return SessionHeartbeatTracker(timeout_seconds=timeout)


def _observe(
    tracker: SessionHeartbeatTracker, *, at: float, msg_type: str = "Heartbeat"
) -> None:
    tracker.observe(
        msg_type=msg_type, sender=_SENDER, target=_TARGET, at=at
    )


def _key(tracker: SessionHeartbeatTracker) -> str:
    return tracker.session_key(_SENDER, _TARGET)


# --- the threshold --------------------------------------------------------


def test_silence_past_the_threshold_times_out() -> None:
    tracker = _tracker(60.0)
    _observe(tracker, at=0.0)
    assert _keys(tracker.timed_out(61.0)) == (_key(tracker),)


def test_silence_at_exactly_the_threshold_does_not_time_out() -> None:
    """Strictly greater-than, so a session heard from exactly one interval
    ago is still considered alive."""
    tracker = _tracker(60.0)
    _observe(tracker, at=0.0)
    assert _keys(tracker.timed_out(60.0)) == ()


def test_a_session_still_speaking_never_times_out() -> None:
    tracker = _tracker(60.0)
    now = 0.0
    for _ in range(20):
        _observe(tracker, at=now)
        now += 10.0
        assert _keys(tracker.timed_out(now)) == ()


def test_default_threshold_mirrors_the_backend_registry() -> None:
    """FR-RUL-030's missingHeartbeatThreshold is 60s; agent and backend must
    agree on what a missing heartbeat is."""
    assert DEFAULT_SESSION_TIMEOUT_SECONDS == 60.0
    assert SessionHeartbeatTracker().timeout_seconds == 60.0


# --- latching: the whole point -------------------------------------------


def test_one_timeout_per_silence_not_one_per_tick() -> None:
    """The health tick is 10s and the threshold 60s. Without latching, a
    five-minute outage would post ~30 `heartbeat_timeouts` into a counter
    `FixSessionDown` reads at `>= 1` critical — turning one dead session
    into a stream of critical alerts.
    """
    tracker = _tracker(60.0)
    _observe(tracker, at=0.0)

    reports = [_keys(tracker.timed_out(t)) for t in range(61, 361, 10)]
    non_empty = [r for r in reports if r]

    assert len(non_empty) == 1, f"expected a single report, got {non_empty}"
    assert non_empty[0] == (_key(tracker),)


def test_a_session_that_recovers_can_time_out_again() -> None:
    """Re-arm. A second silence is a second incident, not a suppressed
    duplicate of the first."""
    tracker = _tracker(60.0)
    _observe(tracker, at=0.0)
    assert _keys(tracker.timed_out(61.0)) == (_key(tracker),)
    assert _keys(tracker.timed_out(71.0)) == ()  # still latched

    _observe(tracker, at=100.0)  # back to life
    assert _keys(tracker.timed_out(110.0)) == ()
    assert _keys(tracker.timed_out(161.0)) == (_key(tracker),)  # new incident


def test_is_timed_out_reflects_the_latch() -> None:
    tracker = _tracker(60.0)
    _observe(tracker, at=0.0)
    assert not tracker.is_timed_out(_key(tracker))
    tracker.timed_out(61.0)
    assert tracker.is_timed_out(_key(tracker))
    _observe(tracker, at=62.0)
    assert not tracker.is_timed_out(_key(tracker))


# --- logout is not a timeout ---------------------------------------------


def test_a_clean_logout_never_times_out() -> None:
    """A logged-out session is silent forever. Counting that as a timeout
    would double-count against `logouts` inside the same FixSessionDown
    rule, making one orderly shutdown look like two critical signals.
    """
    tracker = _tracker(60.0)
    _observe(tracker, at=0.0)
    _observe(tracker, at=5.0, msg_type="Logout")

    assert _keys(tracker.timed_out(600.0)) == ()
    assert tracker.tracked_sessions() == ()


def test_logout_by_raw_tag_value_is_also_honoured() -> None:
    """SeqTracker accepts both normalized names and raw tag values
    ("Logon"/"A"); match that so an unnormalized caller behaves the same."""
    tracker = _tracker(60.0)
    _observe(tracker, at=0.0)
    _observe(tracker, at=5.0, msg_type="5")
    assert _keys(tracker.timed_out(600.0)) == ()


def test_a_session_relogging_on_after_logout_is_tracked_again() -> None:
    tracker = _tracker(60.0)
    _observe(tracker, at=0.0, msg_type="Logout")
    _observe(tracker, at=10.0, msg_type="Logon")
    assert tracker.tracked_sessions() == (_key(tracker),)
    assert _keys(tracker.timed_out(71.0)) == (_key(tracker),)


def test_forget_is_idempotent_on_an_unknown_session() -> None:
    _tracker().forget("NOPE->NOPE:out")  # must not raise


# --- any traffic counts as liveness --------------------------------------


def test_business_messages_count_as_liveness_not_just_heartbeats() -> None:
    """FIX only requires a Heartbeat when the session is otherwise idle, so
    a session busy with orders is demonstrably alive. Counting only 35=0
    would flag the busiest sessions as dead."""
    tracker = _tracker(60.0)
    now = 0.0
    for msg in ("NewOrderSingle", "ExecutionReport", "OrderCancelRequest"):
        _observe(tracker, at=now, msg_type=msg)
        now += 30.0
        assert _keys(tracker.timed_out(now)) == ()


# --- multiple sessions ---------------------------------------------------


def test_sessions_time_out_independently_and_sorted() -> None:
    tracker = _tracker(60.0)
    tracker.observe(msg_type="Heartbeat", sender="MAGIC", target="EXCH_B", at=0.0)
    tracker.observe(msg_type="Heartbeat", sender="MAGIC", target="EXCH_A", at=0.0)
    tracker.observe(msg_type="Heartbeat", sender="MAGIC", target="EXCH_C", at=50.0)

    # Only A and B are past the threshold at t=61, and output is sorted so
    # ingestion order is deterministic.
    assert _keys(tracker.timed_out(61.0)) == (
        "MAGIC->EXCH_A:out",
        "MAGIC->EXCH_B:out",
    )
    assert _keys(tracker.timed_out(111.0)) == ("MAGIC->EXCH_C:out",)


def test_direction_separates_sessions() -> None:
    tracker = _tracker(60.0)
    tracker.observe(
        msg_type="Heartbeat", sender=_SENDER, target=_TARGET, direction="in", at=0.0
    )
    tracker.observe(
        msg_type="Heartbeat", sender=_SENDER, target=_TARGET, direction="out", at=50.0
    )
    assert _keys(tracker.timed_out(61.0)) == ("MAGIC->EXCH1:in",)


# --- session_key parity with SeqTracker ----------------------------------


def test_timeout_carries_the_dimension_id_not_the_internal_key() -> None:
    """The two identifiers are different on purpose and must not be
    confused: `session_key` is direction-aware internal state (`"?"`
    fallbacks, `:out` suffix); `session_id` is the FR-MET-030 dimension
    label that `logouts` and `seq_gaps` already emit (`"unknown"`
    fallbacks, no suffix). Ingesting the key as the dimension would split
    one session into two rows and stop `FixSessionDown` seeing a logout and
    a timeout as the same session.
    """
    tracker = _tracker(60.0)
    _observe(tracker, at=0.0)
    (timeout,) = tracker.timed_out(61.0)

    assert timeout.session_key == "MAGIC->EXCH1:out"
    assert timeout.session_id == "MAGIC->EXCH1"
    assert timeout.session_id == session_id_for(_SENDER, _TARGET)
    assert timeout.session_key != timeout.session_id


def test_both_directions_share_one_dimension_id() -> None:
    """Inbound and outbound are tracked separately but belong to the same
    session as far as the metrics dimension is concerned."""
    tracker = _tracker(60.0)
    for direction in ("in", "out"):
        tracker.observe(
            msg_type="Heartbeat",
            sender=_SENDER,
            target=_TARGET,
            direction=direction,
            at=0.0,
        )
    timeouts = tracker.timed_out(61.0)
    assert _keys(timeouts) == ("MAGIC->EXCH1:in", "MAGIC->EXCH1:out")
    assert {t.session_id for t in timeouts} == {"MAGIC->EXCH1"}


def test_missing_comp_ids_fall_back_to_unknown_in_the_dimension() -> None:
    tracker = _tracker(60.0)
    tracker.observe(msg_type="Heartbeat", sender=None, target=None, at=0.0)
    (timeout,) = tracker.timed_out(61.0)
    assert timeout.session_key == "?->?:out"
    assert timeout.session_id == "unknown->unknown"


def test_silent_seconds_reports_the_actual_silence() -> None:
    tracker = _tracker(60.0)
    _observe(tracker, at=10.0)
    (timeout,) = tracker.timed_out(195.0)
    assert timeout.silent_seconds == 185.0


def test_session_key_matches_seq_tracker_exactly() -> None:
    """`logouts`, `seq_gaps` and `clock_skew_events` all label their
    `session_id` with SeqTracker's format. A different format here would
    split one session into two rows of the shared dimension table
    (FR-MET-030), so FixSessionDown could not see a logout and a timeout as
    the same session.
    """
    sessions = SessionHeartbeatTracker()
    seq = SeqTracker()
    for sender, target, direction in (
        ("MAGIC", "EXCH1", "out"),
        ("MAGIC", "EXCH1", "in"),
        (None, "EXCH1", "out"),
        ("MAGIC", None, "out"),
        (None, None, "out"),
    ):
        assert sessions.session_key(
            sender, target, direction=direction
        ) == seq.session_key(sender, target, direction=direction)
