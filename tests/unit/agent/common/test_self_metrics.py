"""UBS-104: `CounterRegistry` at its canonical `common/` location (moved
from `callbacks/self_metrics.py`, which now just re-exports it). No
dedicated test existed before this move -- it was only exercised
indirectly through `CallbackDispatcher.counters` assertions.
"""

from __future__ import annotations

from telemetry_agent.common.self_metrics import CounterRegistry


def test_increment_starts_at_zero_and_accumulates() -> None:
    registry = CounterRegistry()
    registry.increment("publish_delivered")
    registry.increment("publish_delivered")
    registry.increment("publish_delivered", 3)

    assert registry.snapshot() == {"publish_delivered": 5}


def test_independent_counters_do_not_interfere() -> None:
    registry = CounterRegistry()
    registry.increment("a")
    registry.increment("b", 2)

    assert registry.snapshot() == {"a": 1, "b": 2}


def test_snapshot_is_a_copy_not_a_live_view() -> None:
    registry = CounterRegistry()
    registry.increment("a")
    snapshot = registry.snapshot()
    registry.increment("a")

    assert snapshot == {"a": 1}
    assert registry.snapshot() == {"a": 2}


def test_callbacks_shim_is_the_same_class() -> None:
    from telemetry_agent.callbacks.self_metrics import (
        CounterRegistry as ShimmedCounterRegistry,
    )

    assert ShimmedCounterRegistry is CounterRegistry
