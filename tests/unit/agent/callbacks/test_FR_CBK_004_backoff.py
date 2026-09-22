"""FR-CBK-004 exponential backoff with jitter tests."""

from __future__ import annotations

from telemetry_agent.callbacks.backoff import RetryPolicy


def test_FR_CBK_004_first_attempt_is_roughly_base() -> None:
    policy = RetryPolicy(base_seconds=1.0, factor=2.0, cap_seconds=60.0, jitter=0.0)
    assert policy.delay_for_attempt(1) == 1.0


def test_FR_CBK_004_delay_doubles_per_attempt_with_factor_2() -> None:
    policy = RetryPolicy(base_seconds=1.0, factor=2.0, cap_seconds=60.0, jitter=0.0)
    assert policy.delay_for_attempt(1) == 1.0
    assert policy.delay_for_attempt(2) == 2.0
    assert policy.delay_for_attempt(3) == 4.0
    assert policy.delay_for_attempt(4) == 8.0


def test_FR_CBK_004_delay_is_capped() -> None:
    policy = RetryPolicy(base_seconds=1.0, factor=2.0, cap_seconds=5.0, jitter=0.0)
    assert policy.delay_for_attempt(10) == 5.0


def test_FR_CBK_004_jitter_stays_within_bounds() -> None:
    policy = RetryPolicy(base_seconds=1.0, factor=2.0, cap_seconds=60.0, jitter=0.2)
    for attempt in range(1, 6):
        delay = policy.delay_for_attempt(attempt)
        raw = min(1.0 * 2.0 ** (attempt - 1), 60.0)
        assert raw * 0.8 <= delay <= raw * 1.2


def test_FR_CBK_004_retry_after_overrides_when_larger() -> None:
    policy = RetryPolicy(base_seconds=1.0, factor=2.0, cap_seconds=60.0, jitter=0.0)
    assert policy.delay_for_attempt(1, retry_after=30.0) == 30.0


def test_FR_CBK_004_retry_after_ignored_when_smaller() -> None:
    policy = RetryPolicy(base_seconds=10.0, factor=2.0, cap_seconds=60.0, jitter=0.0)
    assert policy.delay_for_attempt(1, retry_after=1.0) == 10.0
