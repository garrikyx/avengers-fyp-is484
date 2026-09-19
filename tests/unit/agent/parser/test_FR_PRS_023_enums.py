"""FR-PRS-023 enum mapping tests."""

from __future__ import annotations

from telemetry_agent.parser.fix.enums import (
    normalize_exec_type,
    normalize_msg_type,
    normalize_ord_rej_reason,
)


def test_FR_PRS_023_known_msg_type() -> None:
    value, unknown = normalize_msg_type("8")
    assert value == "ExecutionReport"
    assert unknown is None


def test_FR_PRS_023_unknown_enum_sanitized() -> None:
    value, unknown = normalize_exec_type("Z")
    assert value == "unknown_Z"
    assert unknown == "unknown_Z"


def test_FR_PRS_023_ord_rej_reason_mapping() -> None:
    value, unknown = normalize_ord_rej_reason("3")
    assert value == "OrderExceedsLimit"
    assert unknown is None
