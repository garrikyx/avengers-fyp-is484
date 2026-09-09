from __future__ import annotations

import re

_MSG_TYPE: dict[str, str] = {
    "0": "Heartbeat",
    "1": "TestRequest",
    "2": "ResendRequest",
    "3": "Reject",
    "4": "SequenceReset",
    "5": "Logout",
    "A": "Logon",
    "D": "NewOrderSingle",
    "F": "OrderCancelRequest",
    "G": "OrderCancelReplaceRequest",
    "8": "ExecutionReport",
    "9": "OrderCancelReject",
    "AB": "NewOrderMultileg",
    "AC": "MultilegOrderCancelReplace",
}

_EXEC_TYPE: dict[str, str] = {
    "0": "New",
    "3": "DoneForDay",
    "4": "Canceled",
    "5": "Replaced",
    "6": "PendingCancel",
    "7": "Stopped",
    "8": "Rejected",
    "9": "Suspended",
    "A": "PendingNew",
    "C": "Expired",
    "E": "PendingReplace",
    "F": "Trade",
    "G": "TradeCorrect",
    "H": "TradeCancel",
}

_ORD_STATUS: dict[str, str] = {
    "0": "New",
    "1": "PartiallyFilled",
    "2": "Filled",
    "3": "DoneForDay",
    "4": "Canceled",
    "5": "Replaced",
    "6": "PendingCancel",
    "7": "Stopped",
    "8": "Rejected",
    "9": "Suspended",
    "A": "PendingNew",
    "C": "Expired",
    "E": "PendingReplace",
}

_ORD_REJ_REASON: dict[str, str] = {
    "0": "BrokerOption",
    "1": "UnknownSymbol",
    "2": "ExchangeClosed",
    "3": "OrderExceedsLimit",
    "4": "TooLateToEnter",
    "5": "UnknownOrder",
    "6": "DuplicateOrder",
    "7": "DuplicateOfVerballyCommunicated",
    "8": "StaleOrder",
    "9": "TradeAlongRequired",
    "10": "InvalidInvestorId",
    "11": "UnsupportedOrderCharacteristic",
    "12": "SurveillanceOption",
    "13": "IncorrectQuantity",
    "14": "IncorrectAllocatedQuantity",
    "15": "UnknownAccount",
    "99": "Other",
}

_SESSION_REJECT_REASON: dict[str, str] = {
    "0": "InvalidTagNumber",
    "1": "RequiredTagMissing",
    "2": "TagNotDefinedForMessageType",
    "3": "UndefinedTag",
    "4": "TagSpecifiedWithoutValue",
    "5": "ValueIsIncorrect",
    "6": "IncorrectDataFormat",
    "9": "CompIdProblem",
    "10": "SendingTimeAccuracyProblem",
    "11": "InvalidMsgType",
    "99": "Other",
}

_SIDE: dict[str, str] = {
    "1": "Buy",
    "2": "Sell",
}

_ORD_TYPE: dict[str, str] = {
    "1": "Market",
    "2": "Limit",
}

_RAW_SANITIZE = re.compile(r"[^A-Za-z0-9]")
_MAX_RAW_LEN = 8


def normalize_enum(raw: str | None, mapping: dict[str, str]) -> tuple[str | None, str | None]:
    """Map a raw FIX enum value to a stable name.

    Returns (normalized, unknown_token). unknown_token is set when the value
    is not in the mapping and is counted in parser.unknown_enum_values.
    """
    if raw is None or raw == "":
        return None, None
    if raw in mapping:
        return mapping[raw], None
    sanitized = _RAW_SANITIZE.sub("", raw)[:_MAX_RAW_LEN]
    if not sanitized:
        sanitized = "empty"
    return f"unknown_{sanitized}", f"unknown_{sanitized}"


def normalize_msg_type(raw: str | None) -> tuple[str | None, str | None]:
    return normalize_enum(raw, _MSG_TYPE)


def normalize_exec_type(raw: str | None) -> tuple[str | None, str | None]:
    return normalize_enum(raw, _EXEC_TYPE)


def normalize_ord_status(raw: str | None) -> tuple[str | None, str | None]:
    return normalize_enum(raw, _ORD_STATUS)


def normalize_ord_rej_reason(raw: str | None) -> tuple[str | None, str | None]:
    return normalize_enum(raw, _ORD_REJ_REASON)


def normalize_session_reject_reason(raw: str | None) -> tuple[str | None, str | None]:
    return normalize_enum(raw, _SESSION_REJECT_REASON)


def normalize_side(raw: str | None) -> tuple[str | None, str | None]:
    return normalize_enum(raw, _SIDE)


def normalize_ord_type(raw: str | None) -> tuple[str | None, str | None]:
    return normalize_enum(raw, _ORD_TYPE)
