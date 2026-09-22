"""FR-CBK-011 dry-run mode tests."""

from __future__ import annotations

import asyncio
import logging

from telemetry_agent.callbacks.sink import DryRunCallbackSink


def test_FR_CBK_011_dry_run_returns_synthetic_success() -> None:
    sink = DryRunCallbackSink()
    result = asyncio.run(
        sink.send(body=b"{}", headers={"X-Telemetry-Delivery-Id": "d1"})
    )
    assert result.status_code == 200


def test_FR_CBK_011_dry_run_never_opens_a_socket() -> None:
    """DryRunCallbackSink never imports/constructs an httpx client at all —
    completing instantly with a synthetic result is the guarantee that no
    real connection was attempted."""
    sink = DryRunCallbackSink()
    result = asyncio.run(
        sink.send(body=b'{"alertId":"a1"}', headers={"X-Telemetry-Delivery-Id": "d1"})
    )
    assert result.latency_ms == 0.0
    assert result.response_snippet == "dry-run"


def test_FR_CBK_011_dry_run_logs_delivery_id_and_body() -> None:
    logger = logging.getLogger("test-dry-run")
    sink = DryRunCallbackSink(logger=logger)

    records: list[str] = []
    handler = logging.Handler()
    handler.emit = lambda record: records.append(record.getMessage())  # type: ignore[method-assign]
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    asyncio.run(
        sink.send(
            body=b'{"alertId":"a1"}',
            headers={"X-Telemetry-Delivery-Id": "delivery-42"},
        )
    )

    assert any("delivery-42" in message for message in records)
    assert any('"alertId":"a1"' in message for message in records)
