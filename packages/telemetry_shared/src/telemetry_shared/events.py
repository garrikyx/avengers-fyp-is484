"""Event field allowlists shared by producers and backend validation (FR-MET-022).

Operational metadata is derived by the agent; it never contains log text.
New FIX tags still require the ADR-0004 review.
"""

FIX_EVENT_FIELD_KEYS = frozenset(
    {
        "fixVersion",
        "msgType",
        "seqNum",
        "senderCompId",
        "targetCompId",
        "sendingTime",
        "transactTime",
        "clOrdIdHash",
        "origClOrdIdHash",
        "orderIdHash",
        "execIdHash",
        "execType",
        "ordStatus",
        "symbol",
        "side",
        "ordType",
        "orderQty",
        "lastQty",
        "cumQty",
        "leavesQty",
        "ordRejReason",
        "rejectReasonText",
        "refSeqNum",
        "refMsgType",
        "sessionRejectReason",
    }
)

OPERATIONAL_EVENT_FIELDS: dict[str, frozenset[str]] = {
    "fix.seq_gap": frozenset({"expectedSeqNum", "gapSize", "isRegression"}),
    "fix.session_state": frozenset({"state", "silentSeconds"}),
    "fix.execution": frozenset({"sampleEvery"}),
    "parse.error": frozenset({"count", "bucketSeconds"}),
    "app.error": frozenset({"count", "bucketSeconds"}),
    "alert.fired": frozenset({"alertId", "ruleName", "status"}),
    "alert.resolved": frozenset({"alertId", "ruleName", "status"}),
    "log.rotated": frozenset({"sourceIndex"}),
    "log.truncated": frozenset({"sourceIndex"}),
    "log.stalled": frozenset({"sourceIndex"}),
    "agent.state_reset": frozenset({"reason"}),
    "callback.failed": frozenset({"alertId", "reason", "attempts", "httpStatus"}),
}


def allowed_event_fields(event_type: str) -> frozenset[str]:
    fix_fields = FIX_EVENT_FIELD_KEYS if event_type.startswith("fix.") else frozenset()
    return fix_fields | OPERATIONAL_EVENT_FIELDS.get(event_type, frozenset())
