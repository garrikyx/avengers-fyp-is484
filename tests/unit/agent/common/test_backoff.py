"""UBS-104: `RetryPolicy` at its canonical `common/` location (moved from
`callbacks/backoff.py`, which now just re-exports it -- see
`tests/unit/agent/callbacks/test_FR_CBK_004_backoff.py` for the exhaustive
delay-math coverage, unchanged and still passing through the shim). This
file just confirms the new import path is live and correct.
"""

from __future__ import annotations

from telemetry_agent.common.backoff import RetryPolicy


def test_delay_doubles_per_attempt_with_factor_2() -> None:
    policy = RetryPolicy(base_seconds=1.0, factor=2.0, cap_seconds=60.0, jitter=0.0)
    assert policy.delay_for_attempt(1) == 1.0
    assert policy.delay_for_attempt(2) == 2.0
    assert policy.delay_for_attempt(3) == 4.0


def test_delay_is_capped() -> None:
    policy = RetryPolicy(base_seconds=1.0, factor=2.0, cap_seconds=5.0, jitter=0.0)
    assert policy.delay_for_attempt(10) == 5.0


def test_callbacks_shim_is_the_same_class() -> None:
    from telemetry_agent.callbacks.backoff import RetryPolicy as ShimmedRetryPolicy

    assert ShimmedRetryPolicy is RetryPolicy
