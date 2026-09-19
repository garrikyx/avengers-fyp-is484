"""Allowlisted field extraction (FR-PRS-020, NFR-SEC-002, NFR-PERF-004).

The tag table below is the compile-time enforcement point for "no sensitive data
leaves the host" (spec 003-fix-parsing.md §4). It MUST stay a source-level constant,
never configuration — extending it requires an ADR, not a config change.

Explicitly excluded, and MUST NOT be added here: 44 (Price), 31 (LastPx), 6 (AvgPx),
1 (Account), 448/447/452 (party IDs), 448-group contents, 21, 528/529, 581, and any
tag not listed.
"""

from __future__ import annotations

from dataclasses import dataclass

from telemetry_agent.parser.fix.identifiers import hash_identifier

# FIX tag -> FixFields attribute name.
_ALLOWLIST: dict[str, str] = {
    "8": "fix_version",
    "35": "msg_type",
    "34": "seq_num",
    "49": "sender_comp_id",
    "56": "target_comp_id",
    "52": "sending_time",
    "60": "transact_time",
    "150": "exec_type",
    "39": "ord_status",
    "55": "symbol",
    "54": "side",
    "40": "ord_type",
    "38": "order_qty",
    "32": "last_qty",
    "14": "cum_qty",
    "151": "leaves_qty",
    "103": "ord_rej_reason",
    "58": "text",
    "45": "ref_seq_num",
    "372": "ref_msg_type",
    "373": "session_reject_reason",
}

# Correlation-ID tags: hashed (FR-PRS-021), never copied as plaintext.
_HASHED_TAGS: dict[str, str] = {
    "11": "cl_ord_id_hash",
    "41": "orig_cl_ord_id_hash",
    "37": "order_id_hash",
    "17": "exec_id_hash",
}


@dataclass(frozen=True, slots=True)
class FixFields:
    """Fixed-shape allowlisted field set. No attribute here may hold a raw,
    non-allowlisted tag value — this is the whole point of the type."""

    fix_version: str | None = None
    msg_type: str | None = None
    seq_num: str | None = None
    sender_comp_id: str | None = None
    target_comp_id: str | None = None
    sending_time: str | None = None
    transact_time: str | None = None
    cl_ord_id_hash: str | None = None
    orig_cl_ord_id_hash: str | None = None
    order_id_hash: str | None = None
    exec_id_hash: str | None = None
    exec_type: str | None = None
    ord_status: str | None = None
    symbol: str | None = None
    side: str | None = None
    ord_type: str | None = None
    order_qty: str | None = None
    last_qty: str | None = None
    cum_qty: str | None = None
    leaves_qty: str | None = None
    ord_rej_reason: str | None = None
    text: str | None = None
    ref_seq_num: str | None = None
    ref_msg_type: str | None = None
    session_reject_reason: str | None = None


def extract_allowlisted_fields(
    fields: dict[str, str],
    *,
    hash_key: bytes | None,
) -> FixFields:
    """
    FR-PRS-020: extract only the tags in the compile-time allowlist above.

    Correlation IDs (11/41/37/17) are HMAC-hashed when `hash_key` is available
    (FR-PRS-021); when it isn't, those attributes are simply omitted rather than
    falling back to plaintext.
    """
    cl_ord_id = fields.get("11")
    orig_cl_ord_id = fields.get("41")
    order_id = fields.get("37")
    exec_id = fields.get("17")

    return FixFields(
        fix_version=fields.get("8"),
        msg_type=fields.get("35"),
        seq_num=fields.get("34"),
        sender_comp_id=fields.get("49"),
        target_comp_id=fields.get("56"),
        sending_time=fields.get("52"),
        transact_time=fields.get("60"),
        cl_ord_id_hash=_hash_or_none(cl_ord_id, hash_key),
        orig_cl_ord_id_hash=_hash_or_none(orig_cl_ord_id, hash_key),
        order_id_hash=_hash_or_none(order_id, hash_key),
        exec_id_hash=_hash_or_none(exec_id, hash_key),
        exec_type=fields.get("150"),
        ord_status=fields.get("39"),
        symbol=fields.get("55"),
        side=fields.get("54"),
        ord_type=fields.get("40"),
        order_qty=fields.get("38"),
        last_qty=fields.get("32"),
        cum_qty=fields.get("14"),
        leaves_qty=fields.get("151"),
        ord_rej_reason=fields.get("103"),
        text=fields.get("58"),
        ref_seq_num=fields.get("45"),
        ref_msg_type=fields.get("372"),
        session_reject_reason=fields.get("373"),
    )


def _hash_or_none(raw: str | None, hash_key: bytes | None) -> str | None:
    if raw is None or hash_key is None:
        return None
    return hash_identifier(raw, hash_key)
