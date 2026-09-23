from __future__ import annotations

import pytest
from telemetry_agent.publishing.outcome import PublishAction, classify_publish_response
from telemetry_agent.publishing.sink import PublishResult


@pytest.mark.parametrize(
    ("status_code", "expected_action"),
    [
        (200, PublishAction.COMMIT),
        (202, PublishAction.COMMIT),
        (299, PublishAction.COMMIT),
        (400, PublishAction.DROP_REJECTED),
        (401, PublishAction.HALT),
        (403, PublishAction.HALT),
        (404, PublishAction.DROP_REJECTED),
        (408, PublishAction.BACKOFF),
        (413, PublishAction.SPLIT),
        (429, PublishAction.RETRY_AFTER),
        (500, PublishAction.BACKOFF),
        (503, PublishAction.BACKOFF),
    ],
)
def test_status_code_classification(
    status_code: int, expected_action: PublishAction
) -> None:
    result = PublishResult(status_code=status_code, latency_ms=1.0)

    outcome = classify_publish_response(result)

    assert outcome.action is expected_action
    assert outcome.status_code == status_code


def test_transport_error_is_backoff() -> None:
    result = PublishResult(
        status_code=None, latency_ms=1.0, error_class="connect_error"
    )

    outcome = classify_publish_response(result)

    assert outcome.action is PublishAction.BACKOFF
    assert outcome.status_code is None
    assert outcome.error_class == "connect_error"


def test_429_carries_retry_after_seconds() -> None:
    result = PublishResult(status_code=429, latency_ms=1.0, retry_after_seconds=30.0)

    outcome = classify_publish_response(result)

    assert outcome.action is PublishAction.RETRY_AFTER
    assert outcome.retry_after_seconds == 30.0
