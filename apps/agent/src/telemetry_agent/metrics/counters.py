"""MA-02: order / execution / reject counters and reject-reason normalisation.

Counter names match spec 004 §4.1's own catalogue verbatim (not MA-02's
ticket wording, which used different names for the same conditions) —
they're the vocabulary a Rule Engine or NL query layer built against spec
004 will look for; inventing different names here would silently break
that contract even though nothing catches it locally. One dispatch per
event (the ticket's own framing: "all four counter families walk the same
event dispatch"). Agent-internal — plain functions and a plain class, not a
telemetry_shared contract.
"""

from __future__ import annotations

from decimal import Decimal

from telemetry_agent.metrics.aggregator import MetricsAggregator
from telemetry_shared.models.parsed_message import ParsedMessageEvent

# The full known FIX MsgType set (spec 003 §6) that this dispatch recognises
# at all, whether or not it produces a counter for it. Anything outside this
# set increments unclassified_messages rather than being dropped silently.
KNOWN_MSG_TYPES: frozenset[str] = frozenset(
    {
        "Heartbeat",
        "TestRequest",
        "ResendRequest",
        "Reject",
        "SequenceReset",
        "Logout",
        "Logon",
        "NewOrderSingle",
        "OrderCancelRequest",
        "OrderCancelReplaceRequest",
        "ExecutionReport",
        "OrderCancelReject",
        "NewOrderMultileg",
        "MultilegOrderCancelReplace",
    }
)

BASE_DIMS: tuple[str, ...] = ("instance_id", "session_id", "symbol", "side", "ord_type")
REJECT_DIMS: tuple[str, ...] = (*BASE_DIMS, "reject_reason")

# FR-MET-030's "one shared table", spec 004 §4.1 names.
COUNTER_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "messages_total": BASE_DIMS,
    "unclassified_messages": BASE_DIMS,
    "orders_submitted": BASE_DIMS,
    "order_qty": BASE_DIMS,
    "orders_cancel_requested": BASE_DIMS,
    "orders_replaced": BASE_DIMS,
    "orders_acked": BASE_DIMS,
    "executions": BASE_DIMS,
    "executed_qty": BASE_DIMS,
    "fills_full": BASE_DIMS,
    "fills_partial": BASE_DIMS,
    "orders_canceled": BASE_DIMS,
    "orders_expired": BASE_DIMS,
    "orders_rejected": REJECT_DIMS,
    "cancel_rejects": REJECT_DIMS,
    "session_rejects": REJECT_DIMS,
    "rejects_total": REJECT_DIMS,
}

# spec 003 §6's own OrdRejReason(103) and SessionRejectReason(373) canonical
# names, identity-mapped by default: the parser already normalises the raw
# FIX code to one of these strings (FR-PRS-023), so the *default* behaviour
# here is pass-through, not a second renaming layer — "PriceExceedsLimit"
# for "OrderExceedsLimit" would be a deployment's own relabelling choice,
# not something to bake in as ground truth. "Other" is already spec 003's
# own fallback name (OrdRejReason code 99 / SessionRejectReason code 99),
# so it also doubles as this normaliser's unmapped-fallback label.
_KNOWN_REASON_NAMES: frozenset[str] = frozenset(
    {
        "BrokerOption",
        "UnknownSymbol",
        "ExchangeClosed",
        "OrderExceedsLimit",
        "TooLateToEnter",
        "UnknownOrder",
        "DuplicateOrder",
        "DuplicateOfVerballyCommunicated",
        "StaleOrder",
        "TradeAlongRequired",
        "InvalidInvestorId",
        "UnsupportedOrderCharacteristic",
        "SurveillanceOption",
        "IncorrectQuantity",
        "IncorrectAllocatedQuantity",
        "UnknownAccount",
        "InvalidTagNumber",
        "RequiredTagMissing",
        "TagNotDefinedForMessageType",
        "UndefinedTag",
        "TagSpecifiedWithoutValue",
        "ValueIsIncorrect",
        "IncorrectDataFormat",
        "CompIdProblem",
        "SendingTimeAccuracyProblem",
        "InvalidMsgType",
        "Other",
    }
)
DEFAULT_REASON_MAP: dict[str, str] = {name: name for name in _KNOWN_REASON_NAMES}


def derive_counters(event: ParsedMessageEvent) -> dict[str, Decimal]:
    """All four counter families in one event walk."""
    counters: dict[str, Decimal] = {"messages_total": Decimal(1)}

    if event.msg_type not in KNOWN_MSG_TYPES:
        counters["unclassified_messages"] = Decimal(1)
        return counters

    if event.msg_type == "NewOrderSingle":
        counters["orders_submitted"] = Decimal(1)
        if event.order_qty is not None:
            counters["order_qty"] = event.order_qty
    elif event.msg_type == "OrderCancelRequest":
        counters["orders_cancel_requested"] = Decimal(1)
    elif event.msg_type == "OrderCancelReplaceRequest":
        counters["orders_replaced"] = Decimal(1)
    elif event.msg_type == "OrderCancelReject":
        # Kept apart from ExecutionReport's orders_rejected and from
        # session_rejects: a cancel/replace reject is neither a new-order
        # trading rejection nor a FIX session problem.
        counters["cancel_rejects"] = Decimal(1)
        counters["rejects_total"] = Decimal(1)
    elif event.msg_type == "Reject":
        # Session-level (35=3): a FIX plumbing problem, not a trading
        # problem — kept apart so it can't dilute a Rule Engine's reject
        # rate for actual order flow.
        counters["session_rejects"] = Decimal(1)
        counters["rejects_total"] = Decimal(1)
    elif event.msg_type == "ExecutionReport":
        _derive_execution_report_counters(event, counters)

    return counters


def _derive_execution_report_counters(
    event: ParsedMessageEvent, counters: dict[str, Decimal]
) -> None:
    if event.exec_type == "New":
        counters["orders_acked"] = Decimal(1)
    elif event.exec_type == "Trade":
        counters["executions"] = Decimal(1)
        if event.last_qty is not None:
            counters["executed_qty"] = event.last_qty
        _derive_fill_split(event, counters)
    elif event.exec_type == "Canceled":
        counters["orders_canceled"] = Decimal(1)
    elif event.exec_type == "Expired":
        counters["orders_expired"] = Decimal(1)

    # spec 004: "35=8 with ExecType/OrdStatus Rejected" — either signal counts.
    if event.ord_status == "Rejected" or event.exec_type == "Rejected":
        counters["orders_rejected"] = Decimal(1)
        counters["rejects_total"] = Decimal(1)


def _derive_fill_split(event: ParsedMessageEvent, counters: dict[str, Decimal]) -> None:
    """fills_full / fills_partial split on LeavesQty (spec 004 §4.1), not
    OrdStatus — LeavesQty is the authoritative fill-progress signal (tag 151);
    OrdStatus is a reasonable fallback only when the parser didn't populate
    LeavesQty, not the primary basis.
    """
    if event.leaves_qty is not None:
        if event.leaves_qty == 0:
            counters["fills_full"] = Decimal(1)
        else:
            counters["fills_partial"] = Decimal(1)
    elif event.ord_status == "Filled":
        counters["fills_full"] = Decimal(1)
    elif event.ord_status == "PartiallyFilled":
        counters["fills_partial"] = Decimal(1)


class ReasonNormalizer:
    """Config-driven raw-reason -> canonical-label mapping.

    Backs MetricsAggregator's `resolve_reject_reason` callable, so the
    "reject_reason" dimension value the aggregator groups by is always the
    canonical label. Defaults to identity for spec 003's own known reason
    names (see DEFAULT_REASON_MAP) — pass `reason_map` to relabel for a
    deployment's own preferred display names. Unmapped raw reasons fold to
    "Other" (the reason-mapping fallback — distinct from the aggregator's own
    "__other__" cardinality-overflow sentinel, which is a different concept
    that can apply to any dimension) and are recorded, truncated, up to
    `max_unmapped` entries, so the map can be extended from what's actually
    seen in practice.
    """

    def __init__(
        self,
        reason_map: dict[str, str] | None = None,
        *,
        max_text_length: int = 100,
        max_unmapped: int = 50,
    ) -> None:
        self._map = (
            dict(reason_map) if reason_map is not None else dict(DEFAULT_REASON_MAP)
        )
        self._max_text_length = max_text_length
        self._max_unmapped = max_unmapped
        self._unmapped_seen: list[str] = []

    def resolve(self, event: ParsedMessageEvent) -> str:
        raw = event.reject_reason_code or event.reject_reason_text
        if raw is None:
            # FR-PRS-024's own wording: "...else unspecified" — lowercase,
            # matching aggregator.default_resolve_reject_reason's fallback so
            # the two resolvers agree on the label for "nothing populated".
            return "unspecified"
        canonical = self._map.get(raw)
        if canonical is not None:
            return canonical
        self._record_unmapped(raw)
        return "Other"

    def _record_unmapped(self, raw: str) -> None:
        truncated = raw[: self._max_text_length]
        if truncated in self._unmapped_seen:
            return
        if len(self._unmapped_seen) >= self._max_unmapped:
            return
        self._unmapped_seen.append(truncated)

    @property
    def unmapped_seen(self) -> tuple[str, ...]:
        return tuple(self._unmapped_seen)


def top_reject_reasons(
    aggregator: MetricsAggregator,
    window: str,
    *,
    n: int = 10,
    metric: str = "rejects_total",
) -> list[tuple[str, Decimal]]:
    """Top-N normalised reject reasons by `metric` in `window`, N configurable."""
    grouped = aggregator.snapshot(window, group_by=("reject_reason",))
    rows = [
        (label[0], row.counters[metric])
        for label, row in grouped.items()
        if metric in row.counters
    ]
    rows.sort(key=lambda row: row[1], reverse=True)
    return rows[:n]
