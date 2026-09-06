"""Shared test support for the metrics package: a hand-labelled synthetic
FIX-derived event set (MA-02's own framing: one dispatch, one fixture set —
not one per counter family) plus a deterministic clock used by MA-01's and
MA-03's tests, both of which need to advance wall-clock time without
sleeping.

Every event below is commented with which counter(s) it should produce;
EXPECTED_TOTALS is the hand-computed sum, independent of the aggregator or
counters.py's own logic, so a bug in either can't hide behind a
self-consistent-but-wrong fixture. Counter names match spec 004 §4.1.
"""

from datetime import UTC, datetime
from decimal import Decimal

from telemetry_shared.models.parsed_message import (
    CancelReplaceEvent,
    CancelRequestEvent,
    ExecutionReportEvent,
    NewOrderEvent,
    ParsedMessageEvent,
)

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
_ENVELOPE = dict(instance_id="magic-prod-01", session_id="MAGIC->EXCH1")


class FakeClock:
    """A `Clock` (`() -> float`) that only advances when told to — lets a
    test assert TTL/window-decay behaviour without a real sleep.
    """

    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


def hand_labelled_events() -> list[ParsedMessageEvent]:
    return [
        # 1. orders_submitted, order_qty += 100
        NewOrderEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-1",
            symbol="AAPL",
            side="buy",
            ord_type="limit",
            order_qty=Decimal(100),
        ),
        # 2. orders_acked
        ExecutionReportEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-1",
            order_id="OID-1",
            exec_id="EXEC-1",
            exec_type="New",
            ord_status="New",
            symbol="AAPL",
            side="buy",
        ),
        # 3. executions=1, fills_full=1 (LeavesQty=0), executed_qty += 100
        ExecutionReportEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-1",
            order_id="OID-1",
            exec_id="EXEC-2",
            exec_type="Trade",
            ord_status="Filled",
            symbol="AAPL",
            side="buy",
            last_qty=Decimal(100),
            leaves_qty=Decimal(0),
        ),
        # 4. orders_submitted, order_qty += 50
        NewOrderEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-2",
            symbol="MSFT",
            side="sell",
            ord_type="market",
            order_qty=Decimal(50),
        ),
        # 5. executions=1, fills_partial=1 (LeavesQty=30>0), executed_qty += 20
        ExecutionReportEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-2",
            order_id="OID-2",
            exec_id="EXEC-3",
            exec_type="Trade",
            ord_status="PartiallyFilled",
            symbol="MSFT",
            side="sell",
            last_qty=Decimal(20),
            leaves_qty=Decimal(30),
        ),
        # 6. orders_submitted, order_qty += 10
        NewOrderEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-3",
            symbol="GOOG",
            side="buy",
            ord_type="limit",
            order_qty=Decimal(10),
        ),
        # 7. orders_rejected=1, rejects_total+=1; reason "OrderExceedsLimit" is
        #    already spec 003's own canonical OrdRejReason name, so it maps to
        #    itself by default (DEFAULT_REASON_MAP is identity, not a second
        #    renaming layer).
        ExecutionReportEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-3",
            order_id="OID-3",
            exec_id="EXEC-4",
            exec_type="Rejected",
            ord_status="Rejected",
            symbol="GOOG",
            side="buy",
            reject_reason_code="OrderExceedsLimit",
        ),
        # 8. orders_cancel_requested
        CancelRequestEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-4",
            orig_cl_ord_id="ORD-1",
            symbol="AAPL",
            side="buy",
            order_qty=Decimal(100),
        ),
        # 9. orders_replaced
        CancelReplaceEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-5",
            orig_cl_ord_id="ORD-2",
            symbol="MSFT",
            side="sell",
            ord_type="market",
            order_qty=Decimal(30),
        ),
        # 10. cancel_rejects=1, rejects_total+=1; reason "UnknownOrder" is also
        #     already a spec 003 canonical name, identity-mapped.
        ParsedMessageEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            msg_type="OrderCancelReject",
            cl_ord_id="ORD-6",
            orig_cl_ord_id="ORD-4",
            reject_reason_code="UnknownOrder",
        ),
        # 11. session_rejects=1, rejects_total+=1; reason_text unmapped -> "Other"
        ParsedMessageEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            msg_type="Reject",
            reject_reason_text="garbled message",
        ),
        # 12. orders_canceled=1
        ExecutionReportEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-7",
            order_id="OID-7",
            exec_id="EXEC-5",
            exec_type="Canceled",
            ord_status="Canceled",
            symbol="TSLA",
            side="sell",
        ),
        # 13. orders_expired=1
        ExecutionReportEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            cl_ord_id="ORD-8",
            order_id="OID-8",
            exec_id="EXEC-6",
            exec_type="Expired",
            ord_status="Expired",
            symbol="AMZN",
            side="buy",
        ),
        # 14. unclassified_messages
        ParsedMessageEvent(
            **_ENVELOPE,
            event_time_utc=_T0,
            msg_type="CustomVendorMsg",
        ),
    ]


EXPECTED_TOTALS: dict[str, Decimal] = {
    "messages_total": Decimal(14),
    "orders_submitted": Decimal(3),
    "order_qty": Decimal(160),  # 100 + 50 + 10
    "orders_acked": Decimal(1),
    "executions": Decimal(2),  # events 3 and 5, both ExecType=Trade
    "fills_full": Decimal(1),
    "fills_partial": Decimal(1),
    "executed_qty": Decimal(120),  # 100 + 20
    "orders_rejected": Decimal(1),
    "orders_cancel_requested": Decimal(1),
    "orders_replaced": Decimal(1),
    "cancel_rejects": Decimal(1),
    "session_rejects": Decimal(1),
    "rejects_total": Decimal(3),
    "orders_canceled": Decimal(1),
    "orders_expired": Decimal(1),
    "unclassified_messages": Decimal(1),
}

# canonical reject_reason label -> rejects_total contribution
EXPECTED_REJECT_REASON_TOTALS: dict[str, Decimal] = {
    "OrderExceedsLimit": Decimal(1),
    "UnknownOrder": Decimal(1),
    "Other": Decimal(1),
}

EXPECTED_UNMAPPED_REASONS: tuple[str, ...] = ("garbled message",)
