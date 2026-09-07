from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError
from telemetry_shared.models.parsed_message import (
    EVENT_CLASS_BY_MSG_TYPE,
    CancelRejectEvent,
    CancelReplaceEvent,
    CancelRequestEvent,
    ExecutionReportEvent,
    NewOrderEvent,
    ParsedMessageEvent,
)

ENVELOPE = dict(
    event_time_utc=datetime.now(tz=UTC),
    instance_id="magic-prod-01",
    session_id="MAGIC->EXCH1",
)


def test_administrative_message_uses_base_class_directly() -> None:
    event = ParsedMessageEvent(**ENVELOPE, msg_type="Heartbeat")
    assert event.cl_ord_id is None
    assert event.reject_reason_code is None
    assert event.order_qty is None
    assert event.transact_time_utc is None


def test_missing_envelope_field_raises() -> None:
    incomplete = dict(ENVELOPE)
    del incomplete["session_id"]
    with pytest.raises(ValidationError):
        ParsedMessageEvent(msg_type="Heartbeat", **incomplete)  # type: ignore[arg-type]


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ParsedMessageEvent(**ENVELOPE, msg_type="Heartbeat", price=150.50)  # type: ignore[call-arg]


def test_event_is_immutable() -> None:
    event = ParsedMessageEvent(**ENVELOPE, msg_type="Heartbeat")
    with pytest.raises(ValidationError):
        event.symbol = "AAPL"  # type: ignore[misc]


def test_new_order_event_requires_its_order_fields() -> None:
    with pytest.raises(ValidationError, match="symbol"):
        NewOrderEvent(**ENVELOPE, cl_ord_id="ORD-1")  # type: ignore[call-arg]


def test_new_order_event_with_all_required_fields_succeeds() -> None:
    event = NewOrderEvent(
        **ENVELOPE,
        cl_ord_id="ORD-1",
        symbol="AAPL",
        side="buy",
        ord_type="limit",
        order_qty=Decimal(100),
    )
    assert event.msg_type == "NewOrderSingle"
    assert isinstance(event.order_qty, Decimal)
    assert isinstance(
        event, ParsedMessageEvent
    )  # aggregator ingests it as the base type


def test_order_qty_never_coerces_through_float_imprecision() -> None:
    # A string input is the safe path (matches how a parser would build this
    # from raw text); Decimal(str) is exact, unlike Decimal(float).
    event = NewOrderEvent(
        **ENVELOPE,
        cl_ord_id="ORD-1",
        symbol="AAPL",
        side="buy",
        ord_type="limit",
        order_qty="100.10",  # type: ignore[arg-type]
    )
    assert event.order_qty == Decimal("100.10")


def test_execution_report_requires_exec_fields() -> None:
    with pytest.raises(ValidationError, match="order_id"):
        ExecutionReportEvent(
            **ENVELOPE,
            cl_ord_id="ORD-1",
            symbol="AAPL",
            side="buy",
        )  # type: ignore[call-arg]


def test_execution_report_trade_requires_last_qty() -> None:
    with pytest.raises(ValidationError, match="last_qty"):
        ExecutionReportEvent(
            **ENVELOPE,
            cl_ord_id="ORD-1",
            order_id="OID-1",
            exec_id="EXEC-1",
            exec_type="Trade",
            ord_status="Filled",
            symbol="AAPL",
            side="buy",
        )


def test_execution_report_rejected_does_not_require_reject_reason() -> None:
    # FR-PRS-024: coded reason, else normalised text, else "unspecified" —
    # a rejection with neither is valid, the aggregator treats it as unspecified.
    event = ExecutionReportEvent(
        **ENVELOPE,
        cl_ord_id="ORD-1",
        order_id="OID-1",
        exec_id="EXEC-1",
        exec_type="Rejected",
        ord_status="Rejected",
        symbol="AAPL",
        side="buy",
    )
    assert event.reject_reason_code is None
    assert event.reject_reason_text is None


def test_cancel_reject_requires_orig_cl_ord_id() -> None:
    with pytest.raises(ValidationError, match="orig_cl_ord_id"):
        CancelRejectEvent(**ENVELOPE, cl_ord_id="ORD-1")  # type: ignore[call-arg]


def test_cancel_request_event_requires_its_order_fields() -> None:
    with pytest.raises(ValidationError, match="orig_cl_ord_id"):
        CancelRequestEvent(**ENVELOPE, cl_ord_id="ORD-1")  # type: ignore[call-arg]


def test_cancel_replace_event_requires_its_order_fields() -> None:
    with pytest.raises(ValidationError, match="ord_type"):
        CancelReplaceEvent(
            **ENVELOPE,
            cl_ord_id="ORD-1",
            orig_cl_ord_id="ORD-0",
            symbol="AAPL",
            side="buy",
            order_qty=Decimal(100),
        )  # type: ignore[call-arg]


def test_event_class_lookup_covers_exactly_the_order_lifecycle_msg_types() -> None:
    assert EVENT_CLASS_BY_MSG_TYPE == {
        "NewOrderSingle": NewOrderEvent,
        "OrderCancelRequest": CancelRequestEvent,
        "OrderCancelReplaceRequest": CancelReplaceEvent,
        "ExecutionReport": ExecutionReportEvent,
        "OrderCancelReject": CancelRejectEvent,
    }
    assert "Heartbeat" not in EVENT_CLASS_BY_MSG_TYPE
