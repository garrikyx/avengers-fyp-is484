"""FR-PRS-024 rejection precedence tests."""

from __future__ import annotations

from telemetry_agent.parser.fix.rejection import effective_reject_reason


def test_FR_PRS_024_ord_rej_reason_wins() -> None:
    result = effective_reject_reason(
        ord_rej_reason="OrderExceedsLimit",
        reject_reason_label="price_exceeds_limit",
    )
    assert result == "OrderExceedsLimit"


def test_FR_PRS_024_text_label_when_no_ord_rej() -> None:
    result = effective_reject_reason(
        ord_rej_reason=None,
        reject_reason_label="price_exceeds_limit",
    )
    assert result == "price_exceeds_limit"


def test_FR_PRS_024_unspecified_when_missing() -> None:
    result = effective_reject_reason(ord_rej_reason=None, reject_reason_label=None)
    assert result == "unspecified"


def test_FR_PRS_024_session_reject_for_msg_type_reject() -> None:
    result = effective_reject_reason(
        ord_rej_reason=None,
        reject_reason_label=None,
        session_reject_reason="InvalidTagNumber",
        msg_type="Reject",
    )
    assert result == "InvalidTagNumber"
