"""FR-HLT-010, FR-QRY-005: `/healthz` is a liveness probe with no
dependency checks; `/readyz` reports `warming` (503) until `warmupWindow`
has elapsed since this replica started, then `ready` (200).
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.main import app
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.snapshot import SeriesEntry, Snapshot

DIMS = {"session": "MAGIC->EXCH1", "symbol": "ABC"}


def _snapshot(*, bucket_start_utc: datetime) -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id="agent-a",
        application="Magic",
        instance_id="magic-prod-01",
        bucket_start_utc=bucket_start_utc,
        bucket_seconds=10,
        series=[
            SeriesEntry(dimensions=DIMS, counters={"orders_submitted": Decimal(1)})
        ],
    )


def test_healthz_is_always_ok_regardless_of_readiness() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_is_ready_returns_false_before_warmup_window_elapses_even_with_data() -> None:
    config = StreamProcessorConfig(warmup_window_seconds=120)
    started_at = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    processor = StreamProcessor(config, started_at=started_at)
    processor.process_snapshot(_snapshot(bucket_start_utc=started_at), now=started_at)

    just_before_warmup_ends = started_at + timedelta(seconds=119)
    assert processor.is_ready(now=just_before_warmup_ends) is False


def test_is_ready_returns_true_once_warmup_window_has_elapsed_and_data_exists() -> None:
    config = StreamProcessorConfig(warmup_window_seconds=120)
    started_at = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    processor = StreamProcessor(config, started_at=started_at)
    processor.process_snapshot(_snapshot(bucket_start_utc=started_at), now=started_at)

    at_warmup_boundary = started_at + timedelta(seconds=120)
    assert processor.is_ready(now=at_warmup_boundary) is True


def test_is_ready_stays_false_past_warmup_window_if_no_data_ever_arrived() -> None:
    """FR-QRY-005: elapsed time alone must not flip `/readyz` to `ready` —
    if ingestion never delivers anything, an empty store must keep reading
    as `warming`, not be misread as a caught-up, genuinely idle instance.
    """
    config = StreamProcessorConfig(warmup_window_seconds=120)
    started_at = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    processor = StreamProcessor(config, started_at=started_at)

    long_after_warmup_window = started_at + timedelta(hours=1)
    assert processor.is_ready(now=long_after_warmup_window) is False


def test_is_ready_stays_true_once_data_has_arrived_even_if_it_later_ages_out() -> None:
    """`has_data` is sticky: a legitimately quiet period after real data was
    already seen once must not flap the instance back to `warming`.
    """
    config = StreamProcessorConfig(
        warmup_window_seconds=120,
        retention_window_seconds=600,
        max_bucket_age_seconds=600,
    )
    started_at = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
    processor = StreamProcessor(config, started_at=started_at)
    processor.process_snapshot(_snapshot(bucket_start_utc=started_at), now=started_at)

    long_after_retention_has_evicted_everything = started_at + timedelta(hours=2)
    processor.store.tick(long_after_retention_has_evicted_everything)
    assert all(
        bucket.start is None
        for ring in processor.store._rings.values()
        for bucket in ring
    ), "test setup: the merged bucket should actually have aged out by now"
    assert processor.is_ready(now=long_after_retention_has_evicted_everything) is True


def test_readyz_route_reports_warming_with_503_immediately_after_startup() -> None:
    """`main.py`'s module-level `StreamProcessor` singleton starts its
    warmup clock at import time; a request made shortly after — as every
    test run necessarily is, well under the 2-minute default
    `warmupWindow` — must see `warming`/503, never a false `ready`
    (`FR-QRY-005`: an empty just-restarted store must not be misread as
    caught-up-and-idle).
    """
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json() == {"status": "warming"}
