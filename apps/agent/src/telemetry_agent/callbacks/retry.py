"""FR-CBK-006: HTTP outcome -> retry decision classification."""

from __future__ import annotations

from enum import StrEnum

_RETRYABLE_STATUSES = {408, 429}


class RetryDecision(StrEnum):
    SUCCESS = "success"
    RETRY = "retry"
    PERMANENT_FAILURE = "permanent_failure"


def classify_http_status(status: int) -> RetryDecision:
    """`FR-CBK-006`: 2xx=success; 408/429/5xx=retry; other 4xx=permanent
    failure."""
    if 200 <= status < 300:
        return RetryDecision.SUCCESS
    if status in _RETRYABLE_STATUSES or status >= 500:
        return RetryDecision.RETRY
    return RetryDecision.PERMANENT_FAILURE
