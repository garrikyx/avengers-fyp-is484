from __future__ import annotations


def effective_reject_reason(
    *,
    ord_rej_reason: str | None,
    reject_reason_label: str | None,
    session_reject_reason: str | None = None,
    msg_type: str | None = None,
) -> str:
    """Single precedence: ordRejReason → rejectReasonText label → unspecified.

    For session-level Reject (35=3), sessionRejectReason takes precedence over
    text label when ordRejReason is absent.
    """
    if ord_rej_reason is not None and ord_rej_reason != "":
        return ord_rej_reason
    if msg_type == "Reject" and session_reject_reason:
        return session_reject_reason
    if reject_reason_label is not None and reject_reason_label != "":
        return reject_reason_label
    return "unspecified"
