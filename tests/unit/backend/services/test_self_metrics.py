"""UBS-96: SelfMetrics / WarmupTracker without HTTP."""

from datetime import UTC, datetime, timedelta

import pytest
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.self_metrics import SelfMetrics, WarmupTracker

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


def at(seconds: float) -> datetime:
    return T0 + timedelta(seconds=seconds)


def test_warmup_states() -> None:
    w = WarmupTracker(window_seconds=120, clock=lambda: T0)
    assert w.status(at(500)).state == "warming"
    assert w.status(at(500)).since_first_ingest_seconds is None
    w.mark_ingest(at(10))
    w.mark_ingest(at(20))  # later marks don't move the start
    assert w.status(at(129)).state == "warming"
    assert w.status(at(130)).state == "ready"
    assert w.status(at(130)).since_first_ingest_seconds == 120.0


def test_zero_window_is_ready_at_first_ingest() -> None:
    w = WarmupTracker(window_seconds=0)
    w.mark_ingest(T0)
    assert w.status(T0).state == "ready"


def test_negative_window_rejected() -> None:
    with pytest.raises(ValueError):
        WarmupTracker(window_seconds=-1)


def test_two_instances_do_not_share_a_registry() -> None:
    """Private CollectorRegistry: no duplicate-metric errors, no cross-talk."""
    reg = AgentRegistry(clock=lambda: T0)
    a, b = SelfMetrics(reg), SelfMetrics(reg)
    a.ingest_batches.inc()
    assert b"ingest_batches_total 1.0" in a.exposition()[0]
    assert b"ingest_batches_total 0.0" in b.exposition()[0]


def test_producer_hooks_are_plain_counters_and_gauges() -> None:
    m = SelfMetrics(AgentRegistry(clock=lambda: T0))
    m.ingest_batches.inc()
    m.ingest_validation_failures.inc(3)
    m.dedupe_hits.inc()
    m.dropped_payloads.inc(2)
    m.ingest_queue_depth.set(7)
    m.store_buckets.set(360)
    m.store_memory_bytes.set(1024)
    m.query_latency.labels(route="/telemetry/query/metrics").observe(0.2)
    body = m.exposition()[0].decode()
    assert "ingest_validation_failures_total 3.0" in body
    assert "dropped_payloads_total 2.0" in body
    assert "ingest_queue_depth 7.0" in body
    assert "store_buckets 360.0" in body
    assert (
        'query_latency_seconds_bucket{le="0.25",route="/telemetry/query/metrics"} 1.0'
        in body
    )


def test_warmup_gauge_follows_tracker() -> None:
    reg = AgentRegistry(clock=lambda: T0)
    m = SelfMetrics(reg, clock=lambda: T0)
    w = WarmupTracker(0, clock=lambda: T0)
    assert b"warming_up 1.0" in m.exposition(w)[0]
    w.mark_ingest()
    assert b"warming_up 0.0" in m.exposition(w)[0]
