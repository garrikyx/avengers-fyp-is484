"""FR-CBK-001/002/003 callback payload shape tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from callback_fixtures import make_alert_event
from telemetry_agent.callbacks.payload import from_alert_event

_MAX_CALLBACK_BYTES = 16384  # FR-CBK-002 default


def test_FR_CBK_001_payload_carries_ac_required_fields() -> None:
    """UBS-32 AC: alert type, severity, timestamp, affected metric/dimension,
    unique alert ID."""
    alert = make_alert_event()
    payload = from_alert_event(alert, now=datetime.now(UTC))

    assert payload.alert_id == alert.alert_id
    assert payload.rule_name == alert.rule_name  # "alert type"
    assert payload.severity == alert.severity
    assert payload.timestamp_utc is not None
    assert payload.metric_context == alert.metric_context


def test_FR_CBK_002_serialized_payload_matches_spec_shape() -> None:
    alert = make_alert_event(metric_context={"orders_acked": 1188})
    payload = from_alert_event(alert, now=datetime.now(UTC), runbook_url="https://x/y")
    body = payload.model_dump_json(by_alias=True)
    decoded = json.loads(body)

    for key in (
        "schemaVersion",
        "alertId",
        "status",
        "severity",
        "application",
        "instanceId",
        "agentId",
        "ruleName",
        "summary",
        "matchedCondition",
        "observedValue",
        "threshold",
        "firstObservedUtc",
        "timestampUtc",
        "notificationCount",
        "metricContext",
        "runbookUrl",
    ):
        assert key in decoded, f"missing {key}"
    assert decoded["schemaVersion"] == 1
    assert decoded["runbookUrl"] == "https://x/y"


def test_FR_CBK_002_payload_under_max_bytes_for_typical_alert() -> None:
    context: dict[str, float | int | str] = {
        "orders_acked": 1188,
        "orders_rejected": 81,
    }
    alert = make_alert_event(metric_context=context)
    payload = from_alert_event(alert, now=datetime.now(UTC))
    body = payload.model_dump_json(by_alias=True).encode("utf-8")
    assert len(body) < _MAX_CALLBACK_BYTES


def test_FR_CBK_003_summary_stopgap_references_rule_and_condition() -> None:
    """Known gap: AlertEvent has no summary field; from_alert_event
    synthesizes one from rule_name + matched_condition rather than
    inventing unrelated copy."""
    alert = make_alert_event(rule_name="HighRejectRate")
    payload = from_alert_event(alert, now=datetime.now(UTC))
    assert "HighRejectRate" in payload.summary
    assert alert.matched_condition in payload.summary


def test_FR_CBK_003_runbook_url_defaults_to_none() -> None:
    alert = make_alert_event()
    payload = from_alert_event(alert, now=datetime.now(UTC))
    assert payload.runbook_url is None
