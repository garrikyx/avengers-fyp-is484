"""UBS-103: HTTP response -> publish action classification (spec 007 §2.1's
response table). More outcomes than `callbacks/retry.py`'s 3-way
classifier because the publish contract distinguishes 401/403 (halt) from
413 (split) from 429 (honour Retry-After) from a generic backoff case.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from telemetry_agent.publishing.sink import PublishResult


class PublishAction(StrEnum):
    COMMIT = "commit"  # 202 - drop from buffer
    DROP_REJECTED = "drop_rejected"  # 400 / other 4xx - drop, count, log once
    HALT = "halt"  # 401/403 - stop publishing, alert BackendUnreachable
    SPLIT = "split"  # 413 - halve maxBatchItems
    RETRY_AFTER = "retry_after"  # 429 - honour Retry-After
    BACKOFF = "backoff"  # 408/5xx/transport error - keep buffered, retry later


@dataclass(frozen=True, slots=True)
class PublishOutcome:
    action: PublishAction
    status_code: int | None
    retry_after_seconds: float | None = None
    error_class: str | None = None


def classify_publish_response(result: PublishResult) -> PublishOutcome:
    if result.status_code is None:
        # Transport error: never reached the backend.
        return PublishOutcome(
            PublishAction.BACKOFF, None, error_class=result.error_class
        )

    status = result.status_code
    if 200 <= status < 300:
        return PublishOutcome(PublishAction.COMMIT, status)
    if status == 400:
        return PublishOutcome(PublishAction.DROP_REJECTED, status)
    if status in (401, 403):
        return PublishOutcome(PublishAction.HALT, status)
    if status == 408:
        return PublishOutcome(PublishAction.BACKOFF, status)
    if status == 413:
        return PublishOutcome(PublishAction.SPLIT, status)
    if status == 429:
        return PublishOutcome(
            PublishAction.RETRY_AFTER,
            status,
            retry_after_seconds=result.retry_after_seconds,
        )
    if 400 <= status < 500:
        return PublishOutcome(PublishAction.DROP_REJECTED, status)
    # 5xx and anything else unexpected (1xx/3xx): back off and retry.
    return PublishOutcome(PublishAction.BACKOFF, status)
