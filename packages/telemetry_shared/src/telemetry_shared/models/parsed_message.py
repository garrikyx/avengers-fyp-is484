"""Contract between the Parser Engine and the Metrics Aggregator.

Spec 003 §4 (field allowlist) and spec 004 §4.1 (counter derivation).
Pydantic per FR-ING-022 / ADR 0006: shared cross-component schemas live in
packages/telemetry_shared as Pydantic models. Agent-internal types (the
metrics store, counters, correlation map) are plain dataclasses instead,
matching apps/agent/src/telemetry_agent/parser/protocol.py's own style —
they aren't a contract another component imports.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator


class ParsedMessageEvent(BaseModel):
    """Base envelope for every parsed FIX message.

    Also the concrete type for administrative messages (Logon, Logout,
    Heartbeat, SequenceReset, TestRequest, ResendRequest, or any msg_type not
    listed in EVENT_CLASS_BY_MSG_TYPE) — those carry no order-lifecycle
    fields, so the base class alone is the right shape for them. Note that
    session-level Reject (35=3) also uses this base class directly rather
    than a dedicated subclass: it only ever needs reject_reason_code/text,
    both already optional fields here, so a subclass would add a name
    without narrowing anything.

    For everything else, the parser should construct the matching subclass
    below instead of this base class directly; look it up via
    EVENT_CLASS_BY_MSG_TYPE. The Metrics Aggregator only ever type-hints
    against this base class and reads fields uniformly across every
    subclass — it never branches on the concrete type.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_time_utc: datetime
    instance_id: str
    session_id: str
    msg_type: str

    # tag 60 TransactTime — optional alternative timestamp basis for MA-03's
    # latency calculation (spec 003 allowlist §4); event_time_utc remains the
    # single source spec 003 FR-PRS-025 defines (SendingTime, falling back to
    # log read time), so the two fields answer different questions and both
    # are kept.
    transact_time_utc: datetime | None = None

    cl_ord_id: str | None = None
    orig_cl_ord_id: str | None = None
    order_id: str | None = None
    exec_id: str | None = None

    symbol: str | None = None
    side: str | None = None
    ord_type: str | None = None
    ord_status: str | None = None
    exec_type: str | None = None

    # Decimal, never float (MA-02 AC): FIX quantities must not accumulate
    # binary floating-point error across many fills.
    order_qty: Decimal | None = None
    last_qty: Decimal | None = None
    # tags 14/151 (spec 003 §4 allowlist, "fill progress") — leaves_qty is
    # what spec 004 §4.1 actually keys fills_full/fills_partial on (LeavesQty
    # = 0 vs > 0), not ord_status; cum_qty is carried for completeness with
    # the allowlist even though no counter derives from it yet.
    cum_qty: Decimal | None = None
    leaves_qty: Decimal | None = None

    reject_reason_code: str | None = None
    reject_reason_text: str | None = None


class NewOrderEvent(ParsedMessageEvent):
    """35=D NewOrderSingle."""

    msg_type: str = "NewOrderSingle"
    cl_ord_id: str
    symbol: str
    side: str
    ord_type: str
    order_qty: Decimal


class CancelRequestEvent(ParsedMessageEvent):
    """35=F OrderCancelRequest."""

    msg_type: str = "OrderCancelRequest"
    cl_ord_id: str
    orig_cl_ord_id: str
    symbol: str
    side: str
    order_qty: Decimal


class CancelReplaceEvent(ParsedMessageEvent):
    """35=G OrderCancelReplaceRequest."""

    msg_type: str = "OrderCancelReplaceRequest"
    cl_ord_id: str
    orig_cl_ord_id: str
    symbol: str
    side: str
    ord_type: str
    order_qty: Decimal


class ExecutionReportEvent(ParsedMessageEvent):
    """35=8 ExecutionReport.

    reject_reason_code / reject_reason_text stay optional even when
    ord_status is Rejected: FR-PRS-024 (spec 003) treats "neither present" as
    the valid, well-defined "unspecified" case, not a parser error.
    """

    msg_type: str = "ExecutionReport"
    cl_ord_id: str
    order_id: str
    exec_id: str
    exec_type: str
    ord_status: str
    symbol: str
    side: str

    @model_validator(mode="after")
    def _trade_requires_last_qty(self) -> ExecutionReportEvent:
        if self.exec_type == "Trade" and self.last_qty is None:
            raise ValueError("ExecutionReport with exec_type=Trade is missing last_qty")
        return self


class CancelRejectEvent(ParsedMessageEvent):
    """35=9 OrderCancelReject.

    reject_reason_code here is sourced from CxlRejReason (tag 102), not
    OrdRejReason (103) — same field, different source tag depending on
    msg_type (see docs/telemetry-schema.md). Tag 102 is not in spec 003's
    original field allowlist (§4); enabling its extraction is a coordination
    item for the Parser Engine owner, not a schema widening on this side.
    """

    msg_type: str = "OrderCancelReject"
    cl_ord_id: str
    orig_cl_ord_id: str


# Convenience for the Parser Engine: pick the right constructor by msg_type.
# Anything not in this map (Logon, Logout, Heartbeat, session-level Reject,
# an unrecognised msg_type, ...) is administrative — construct
# ParsedMessageEvent itself.
EVENT_CLASS_BY_MSG_TYPE: dict[str, type[ParsedMessageEvent]] = {
    "NewOrderSingle": NewOrderEvent,
    "OrderCancelRequest": CancelRequestEvent,
    "OrderCancelReplaceRequest": CancelReplaceEvent,
    "ExecutionReport": ExecutionReportEvent,
    "OrderCancelReject": CancelRejectEvent,
}
