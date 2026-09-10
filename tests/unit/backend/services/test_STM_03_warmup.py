"""FR-STM-006: an agent's post-restart cold-start state is preserved through
the Stream Processor rather than discarded on merge, so a query layer can
still tell a range was fed by a warming-up agent.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.metric_store import MetricStore
from telemetry_shared.models.snapshot import SeriesEntry, Snapshot

DIMS = {"session": "MAGIC->EXCH1", "symbol": "ABC"}


def _snapshot(
    *,
    agent_id: str,
    instance_id: str,
    bucket_start_utc: datetime,
    restarted: bool,
    counters: dict[str, int] | None = None,
) -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id=agent_id,
        application="Magic",
        instance_id=instance_id,
        bucket_start_utc=bucket_start_utc,
        bucket_seconds=10,
        restarted=restarted,
        series=[
            SeriesEntry(
                dimensions=DIMS,
                counters={k: Decimal(v) for k, v in (counters or {}).items()},
            )
        ],
    )


def test_restarted_bucket_marks_the_instance_warming_up_for_the_warmup_window() -> None:
    config = StreamProcessorConfig(warmup_window_seconds=120)
    store = MetricStore(config)
    bucket_start = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)

    store.merge(
        _snapshot(
            agent_id="agent-a",
            instance_id="magic-prod-01",
            bucket_start_utc=bucket_start,
            restarted=True,
            counters={"orders_submitted": 3},
        ),
        canonical_start=bucket_start,
        now=bucket_start,
    )

    assert store.is_warming_up("magic-prod-01", at=bucket_start) is True
    assert (
        store.is_warming_up(
            "magic-prod-01", at=bucket_start + timedelta(seconds=119)
        )
        is True
    )
    assert (
        store.is_warming_up(
            "magic-prod-01", at=bucket_start + timedelta(seconds=121)
        )
        is False
    )


def test_data_from_a_restarted_bucket_is_still_merged_not_dropped() -> None:
    """warmingUp flags incomplete data for the caller to exclude; it does
    not mean the Stream Processor throws the bucket away.
    """
    store = MetricStore(StreamProcessorConfig())
    bucket_start = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)

    store.merge(
        _snapshot(
            agent_id="agent-a",
            instance_id="magic-prod-01",
            bucket_start_utc=bucket_start,
            restarted=True,
            counters={"orders_submitted": 3},
        ),
        canonical_start=bucket_start,
        now=bucket_start,
    )

    groups = store.read(
        "magic-prod-01",
        from_utc=bucket_start,
        to_utc=bucket_start + timedelta(seconds=10),
    )
    assert groups[0].counters["orders_submitted"] == 3


def test_restarted_bucket_count_reflects_only_buckets_a_restart_touched() -> None:
    store = MetricStore(StreamProcessorConfig())
    bucket_start = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    next_bucket = bucket_start + timedelta(seconds=10)

    store.merge(
        _snapshot(
            agent_id="agent-a",
            instance_id="magic-prod-01",
            bucket_start_utc=bucket_start,
            restarted=True,
        ),
        canonical_start=bucket_start,
        now=bucket_start,
    )
    store.merge(
        _snapshot(
            agent_id="agent-a",
            instance_id="magic-prod-01",
            bucket_start_utc=next_bucket,
            restarted=False,
        ),
        canonical_start=next_bucket,
        now=next_bucket,
    )

    count = store.restarted_bucket_count(
        "magic-prod-01", from_utc=bucket_start, to_utc=next_bucket
    )
    assert count == 1


def test_an_unrelated_instance_is_not_marked_warming_up() -> None:
    store = MetricStore(StreamProcessorConfig())
    bucket_start = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)

    store.merge(
        _snapshot(
            agent_id="agent-a",
            instance_id="magic-prod-01",
            bucket_start_utc=bucket_start,
            restarted=True,
        ),
        canonical_start=bucket_start,
        now=bucket_start,
    )

    assert store.is_warming_up("magic-prod-02", at=bucket_start) is False


def test_an_out_of_order_earlier_restart_does_not_shrink_the_warmup_window() -> None:
    config = StreamProcessorConfig(warmup_window_seconds=120)
    store = MetricStore(config)
    early = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    later = early + timedelta(seconds=60)

    # The later restart is processed first (e.g. it arrived first)...
    store.merge(
        _snapshot(
            agent_id="agent-a",
            instance_id="magic-prod-01",
            bucket_start_utc=later,
            restarted=True,
        ),
        canonical_start=later,
        now=later,
    )
    # ...then an earlier restart arrives out of order.
    store.merge(
        _snapshot(
            agent_id="agent-a",
            instance_id="magic-prod-01",
            bucket_start_utc=early,
            restarted=True,
        ),
        canonical_start=early,
        now=later,
    )

    # later's warm-up window (later + 120s) must win, not be shrunk back to
    # early's (early + 120s = later + 60s).
    still_warming_probe = later + timedelta(seconds=100)
    assert store.is_warming_up("magic-prod-01", at=still_warming_probe) is True
