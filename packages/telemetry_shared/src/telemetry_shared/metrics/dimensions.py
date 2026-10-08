"""spec 004 §5 / FR-ING-007: the dimension-key allowlist shared by both
trust-boundary checks — the backend's own ingestion validator and (UBS-115)
the agent's wire-format converter — so the two can never silently diverge.
"""

from __future__ import annotations

# Wire-format names, so they stay in camelCase even though Python model
# attributes and the agent's internal dimension names use snake_case.
ALLOWED_DIMENSION_KEYS: frozenset[str] = frozenset(
    {
        "application",
        "instanceId",
        "session",
        "symbol",
        "side",
        "ordType",
        "msgType",
        "rejectReason",
        "sessionRejectReason",
        "reason",
        "severity",
    }
)

# Agent-internal snake_case dimension name -> wire camelCase name. Dimensions
# already identical on both sides (symbol, side, reason, severity) are
# omitted; `.get(dim, dim)` falls through unchanged for those.
DIMENSION_KEY_ALIASES: dict[str, str] = {
    "instance_id": "instanceId",
    "session_id": "session",
    "ord_type": "ordType",
    "reject_reason": "rejectReason",
    "session_reject_reason": "sessionRejectReason",
}
