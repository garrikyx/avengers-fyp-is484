"""FR-CBK-006 HTTP status -> retry decision classification tests."""

from __future__ import annotations

import pytest
from telemetry_agent.callbacks.retry import RetryDecision, classify_http_status


@pytest.mark.parametrize("status", [200, 201, 202, 204, 299])
def test_FR_CBK_006_2xx_is_success(status: int) -> None:
    assert classify_http_status(status) is RetryDecision.SUCCESS


@pytest.mark.parametrize("status", [408, 429, 500, 502, 503, 504])
def test_FR_CBK_006_408_429_5xx_is_retry(status: int) -> None:
    assert classify_http_status(status) is RetryDecision.RETRY


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 422])
def test_FR_CBK_006_other_4xx_is_permanent_failure(status: int) -> None:
    assert classify_http_status(status) is RetryDecision.PERMANENT_FAILURE


@pytest.mark.parametrize("status", [100, 301, 302])
def test_FR_CBK_006_non_2xx_non_4xx_5xx_falls_back_to_permanent_failure(
    status: int,
) -> None:
    """1xx/3xx aren't expected from Magic's ack, but must classify to
    something rather than raise — permanent failure (no infinite retry on
    a genuinely unexpected response) is the safe default."""
    assert classify_http_status(status) is RetryDecision.PERMANENT_FAILURE
