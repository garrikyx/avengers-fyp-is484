"""UBS-85: IngestGuard dedupe (FR-ING-004) and rate limiting (FR-ING-008)."""

from datetime import UTC, datetime, timedelta

import pytest
from telemetry_backend.config import (
    BackendConfigError,
    IngestGuardConfig,
    load_backend_health_config,
)
from telemetry_backend.services.ingest_guard import (
    Accept,
    Duplicate,
    IngestGuard,
    RateLimited,
)

T0 = datetime(2026, 9, 29, 4, 0, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def guard(**kw: float) -> tuple[IngestGuard, FakeClock]:
    clock = FakeClock()
    return IngestGuard(IngestGuardConfig(**kw), clock=clock), clock  # type: ignore[arg-type]


def test_first_sight_is_accepted_and_a_committed_batch_is_a_duplicate() -> None:
    g, _ = guard()
    assert g.check("a", "b1") == Accept()
    g.commit("a", "b1")
    assert g.check("a", "b1") == Duplicate()


def test_check_without_commit_remembers_nothing() -> None:
    """A batch refused downstream (503 queue_full) must be accepted on retry."""
    g, _ = guard(max_batches_per_minute_per_agent=1)
    assert g.check("a", "b1") == Accept()
    assert g.check("a", "b1") == Accept()
    assert g.check("a", "b2") == Accept()  # no quota spent either


def test_batch_ids_are_scoped_per_agent() -> None:
    g, _ = guard()
    g.commit("a", "same-id")
    assert g.check("b", "same-id") == Accept()


def test_duplicate_is_forgotten_after_ttl() -> None:
    g, clock = guard(dedupe_ttl_seconds=1800)
    g.commit("a", "b1")
    clock.advance(1799)
    assert g.check("a", "b1") == Duplicate()
    clock.advance(1)
    assert g.check("a", "b1") == Accept()


def test_lru_evicts_the_oldest_id_past_capacity() -> None:
    g, _ = guard(dedupe_cache_size=2, max_batches_per_minute_per_agent=100)
    for batch_id in ("b1", "b2", "b3"):
        g.commit("a", batch_id)
    assert g.check("a", "b1") == Accept()
    assert g.check("a", "b2") == Duplicate()
    assert g.check("a", "b3") == Duplicate()


def test_rate_limit_refuses_past_the_limit_with_retry_after() -> None:
    g, clock = guard(max_batches_per_minute_per_agent=3)
    for i in range(3):
        g.commit("a", f"b{i}")
        clock.advance(10)  # accepted at t=0, 10, 20
    # t=30: the oldest frees up at t=60
    assert g.check("a", "new") == RateLimited(retry_after_seconds=30)
    assert g.check("other-agent", "new") == Accept()


def test_rate_window_slides() -> None:
    g, clock = guard(max_batches_per_minute_per_agent=2)
    g.commit("a", "b1")
    clock.advance(30)
    g.commit("a", "b2")
    assert isinstance(g.check("a", "b3"), RateLimited)
    clock.advance(30)  # b1 is now 60s old and drops out
    assert g.check("a", "b3") == Accept()


def test_dedupe_wins_over_rate_limit() -> None:
    """A retry of a batch we already hold costs no quota and gets 202."""
    g, _ = guard(max_batches_per_minute_per_agent=1)
    g.commit("a", "b1")
    assert g.check("a", "b1") == Duplicate()


def test_retry_after_is_at_least_one_second() -> None:
    g, clock = guard(max_batches_per_minute_per_agent=1)
    g.commit("a", "b1")
    clock.advance(59.9)
    assert g.check("a", "b2") == RateLimited(retry_after_seconds=1)


@pytest.mark.parametrize(
    "kw",
    [
        {"max_batches_per_minute_per_agent": 0},
        {"dedupe_cache_size": 0},
        {"dedupe_ttl_seconds": 0},
    ],
)
def test_invalid_config_is_refused(kw: dict[str, float]) -> None:
    with pytest.raises(BackendConfigError):
        IngestGuardConfig(**kw)  # type: ignore[arg-type]


def test_ingest_section_is_loaded_from_yaml(tmp_path) -> None:  # type: ignore[no-untyped-def]
    file = tmp_path / "backend.yaml"
    file.write_text(
        "ingest:\n"
        "  maxBodyBytes: 8388608\n"  # someone else's key: tolerated
        "  maxBatchesPerMinutePerAgent: 12\n"
        "  dedupeCacheSize: 500\n"
        "  dedupeTtl: 10m\n",
        encoding="utf-8",
    )
    ingest = load_backend_health_config(file).ingest
    assert ingest == IngestGuardConfig(
        max_batches_per_minute_per_agent=12,
        dedupe_cache_size=500,
        dedupe_ttl_seconds=600.0,
    )


def test_missing_ingest_section_uses_spec_defaults(tmp_path) -> None:  # type: ignore[no-untyped-def]
    file = tmp_path / "backend.yaml"
    file.write_text("backend:\n  listen: 0.0.0.0:9000\n", encoding="utf-8")
    assert load_backend_health_config(file).ingest == IngestGuardConfig(
        max_batches_per_minute_per_agent=30,
        dedupe_cache_size=10_000,
        dedupe_ttl_seconds=1800.0,
    )
