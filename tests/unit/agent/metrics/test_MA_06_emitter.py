"""Aggregator -> wire snapshot bridge: `MetricsAggregator.take_completed_buckets`
and `SnapshotEmitter` (spec 004 §3, FR-MET-024..031, FR-LOG-021)."""

from __future__ import annotations

import asyncio
import sys
import threading
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fixtures import EXPECTED_TOTALS, FakeClock, hand_labelled_events
from telemetry_agent.metrics.aggregator import (
    OTHER_LABEL,
    AggregatorConfig,
    MetricsAggregator,
)
from telemetry_agent.metrics.correlation import LATENCY_DIMENSIONS, LatencyCorrelator
from telemetry_agent.metrics.counters import COUNTER_DIMENSIONS, derive_counters
from telemetry_agent.metrics.emitter import WIRE_DIMENSION, SnapshotEmitter
from telemetry_shared.models.ingestion import WIRE_DIMENSION_KEYS
from telemetry_shared.models.parsed_message import (
    ExecutionReportEvent,
    NewOrderEvent,
    ParsedMessageEvent,
)
from telemetry_shared.models.snapshot import Snapshot

_T0 = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
_AGENT = "magic-agent-sg-01"
_BUCKET = 10
_ALL_DIMENSIONS = {**COUNTER_DIMENSIONS, **LATENCY_DIMENSIONS}


def _aggregator(clock: FakeClock, **config: object) -> MetricsAggregator:
    return MetricsAggregator(
        config=AggregatorConfig(
            bucket_seconds=_BUCKET,
            metric_dimensions=dict(_ALL_DIMENSIONS),
            **config,  # type: ignore[arg-type]
        ),
        clock=clock,
    )


def _emitter(aggregator: MetricsAggregator, **kwargs: object) -> SnapshotEmitter:
    # No configured instances unless a test asks: the data-shape tests below
    # then see only the snapshots their own events produce.
    kwargs.setdefault("instance_ids", ())
    return SnapshotEmitter(
        aggregator,
        agent_id=_AGENT,
        application="Magic",
        **kwargs,  # type: ignore[arg-type]
    )


def _order(
    at: datetime, *, instance: str = "magic-prod-01", symbol: str = "AAPL"
) -> NewOrderEvent:
    return NewOrderEvent(
        event_time_utc=at,
        instance_id=instance,
        session_id="MAGIC->EXCH1",
        cl_ord_id_hash=f"ORD-{at.timestamp()}-{instance}-{symbol}",
        symbol=symbol,
        side="Buy",
        ord_type="Limit",
        order_qty=Decimal(100),
    )


def _ingest(aggregator: MetricsAggregator, event: ParsedMessageEvent) -> None:
    aggregator.ingest_counters(event, derive_counters(event))


def _counter_total(snapshots: list[Snapshot], metric: str) -> Decimal:
    return sum(
        (
            series.counters.get(metric, Decimal(0))
            for snapshot in snapshots
            for series in snapshot.series
        ),
        Decimal(0),
    )


# --- MetricsAggregator.take_completed_buckets ------------------------------


def test_open_bucket_is_held_until_it_closes() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    _ingest(aggregator, _order(_T0))

    clock.advance(_BUCKET - 0.001)
    assert aggregator.take_completed_buckets() == []
    clock.advance(0.001)  # exactly at the boundary: closed
    (raw,) = aggregator.take_completed_buckets()
    assert raw.start_utc == _T0
    assert raw.bucket_seconds == _BUCKET


def test_a_taken_bucket_is_not_taken_again_unless_written_to() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    _ingest(aggregator, _order(_T0))
    clock.advance(_BUCKET)

    assert len(aggregator.take_completed_buckets()) == 1
    assert aggregator.take_completed_buckets() == []

    # FR-MET-003: a late event for a bucket still in memory lands in its own
    # bucket, which is returned again — in full, not just the late part.
    _ingest(aggregator, _order(_T0 + timedelta(seconds=1), symbol="MSFT"))
    (raw,) = aggregator.take_completed_buckets()
    assert sum(raw.counters["orders_submitted"].values()) == Decimal(2)


def test_buckets_come_back_oldest_first_across_a_ring_wraparound() -> None:
    # capacity = 60s / 10s = 6 slots: bucket 5 sits in the last slot, bucket 6
    # wraps to slot 0 — slot order would put the newer bucket first.
    base = _T0.timestamp() + 5 * _BUCKET
    clock = FakeClock(base)
    aggregator = _aggregator(clock, windows={"1m": 60})
    _ingest(aggregator, _order(datetime.fromtimestamp(base, tz=UTC)))
    _ingest(aggregator, _order(datetime.fromtimestamp(base + _BUCKET, tz=UTC)))
    clock.advance(2 * _BUCKET)

    starts = [raw.start_utc.timestamp() for raw in aggregator.take_completed_buckets()]
    assert starts == [base, base + _BUCKET]


def test_event_older_than_retention_is_dropped_and_publishes_nothing() -> None:
    # FR-MET-002: outside the retained ring, an event has no bucket to land
    # in — it must not dirty (and so re-publish) whatever reuses that slot.
    clock = FakeClock(_T0.timestamp() + 3600)
    aggregator = _aggregator(clock)
    _ingest(aggregator, _order(_T0))

    assert aggregator.take_completed_buckets() == []


def test_every_write_path_marks_its_bucket_for_publishing() -> None:
    clock = FakeClock(_T0.timestamp())
    for write in (
        lambda agg: agg.ingest_agent_counters(
            dims={"instance_id": "magic-prod-01"},
            counters={"callback_failures": Decimal(1)},
            at=_T0,
        ),
        lambda agg: agg.observe_latency(
            metric="ack_latency_ms", dims_event=_order(_T0), value_ms=Decimal(5), at=_T0
        ),
    ):
        aggregator = _aggregator(FakeClock(clock()))
        write(aggregator)
        assert aggregator.take_completed_buckets(now=clock() + _BUCKET) != []


def test_taken_bucket_is_a_copy_detached_from_the_ring() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    correlator = LatencyCorrelator(aggregator, clock=clock)

    def ingest_all() -> None:
        for event in hand_labelled_events():
            _ingest(aggregator, event)
            correlator.ingest(event)

    ingest_all()
    clock.advance(_BUCKET)
    (raw,) = aggregator.take_completed_buckets()
    counters_before = {m: dict(s) for m, s in raw.counters.items()}
    hist_counts_before = {
        m: {label: h.count for label, h in s.items()} for m, s in raw.histograms.items()
    }

    ingest_all()  # same bucket, written again

    assert {m: dict(s) for m, s in raw.counters.items()} == counters_before
    assert {
        m: {label: h.count for label, h in s.items()} for m, s in raw.histograms.items()
    } == hist_counts_before


def test_reading_while_a_worker_thread_writes_never_raises() -> None:
    # The pipeline's parser workers are threads; the publisher reads from
    # the event loop. Without the aggregator's lock, iterating a bucket's
    # dicts mid-insert raises "dictionary changed size during iteration".
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    stop = threading.Event()
    errors: list[BaseException] = []

    def write() -> None:
        i = 0
        while not stop.is_set():
            _ingest(aggregator, _order(_T0, symbol=f"S{i % 500}"))
            i += 1

    # Force frequent thread switches so an unlocked read reliably lands
    # mid-write instead of depending on scheduler luck.
    previous_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    writer = threading.Thread(target=write)
    writer.start()
    try:
        for _ in range(300):
            aggregator.take_completed_buckets(now=clock() + _BUCKET)
            aggregator.snapshot("1m", group_by=("symbol",))
    except BaseException as exc:  # pragma: no cover - the failure path
        errors.append(exc)
    finally:
        stop.set()
        writer.join()
        sys.setswitchinterval(previous_interval)
    assert errors == []


# --- SnapshotEmitter: shape (FR-MET-024..030, FR-ING-007) -------------------


def test_each_snapshot_carries_its_own_bucket_deltas_only() -> None:
    # The double-counting failure mode a windowed bridge has: publishing a
    # summed window every tick would send bucket A's events again with B.
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    emitter = _emitter(aggregator)

    for _ in range(3):
        _ingest(aggregator, _order(_T0))
    clock.advance(_BUCKET)
    first = emitter.collect()

    for _ in range(5):
        _ingest(aggregator, _order(_T0 + timedelta(seconds=_BUCKET)))
    clock.advance(_BUCKET)
    second = emitter.collect()

    assert [s.bucket_start_utc for s in first] == [_T0]
    assert [s.bucket_start_utc for s in second] == [_T0 + timedelta(seconds=_BUCKET)]
    assert _counter_total(first, "orders_submitted") == Decimal(3)
    assert _counter_total(second, "orders_submitted") == Decimal(5)


def test_no_configured_instance_and_no_data_publishes_nothing() -> None:
    clock = FakeClock(_T0.timestamp())
    emitter = _emitter(_aggregator(clock))
    clock.advance(10 * _BUCKET)
    assert emitter.collect() == []


def test_snapshot_totals_match_the_hand_labelled_fixture() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    for event in hand_labelled_events():
        _ingest(aggregator, event)
    clock.advance(_BUCKET)

    snapshots = _emitter(aggregator).collect()

    for metric, expected in EXPECTED_TOTALS.items():
        assert _counter_total(snapshots, metric) == expected, metric


def test_instance_id_becomes_the_snapshot_identity_not_a_dimension() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    _ingest(aggregator, _order(_T0, instance="magic-prod-01"))
    _ingest(aggregator, _order(_T0, instance="magic-prod-01"))
    _ingest(aggregator, _order(_T0, instance="magic-prod-02"))
    clock.advance(_BUCKET)

    snapshots = _emitter(aggregator).collect()

    by_instance = {s.instance_id: s for s in snapshots}
    assert set(by_instance) == {"magic-prod-01", "magic-prod-02"}
    assert _counter_total([by_instance["magic-prod-01"]], "orders_submitted") == 2
    assert _counter_total([by_instance["magic-prod-02"]], "orders_submitted") == 1
    for snapshot in snapshots:
        assert (snapshot.agent_id, snapshot.application) == (_AGENT, "Magic")
        assert snapshot.schema_version == 1
        for series in snapshot.series:
            assert not {"instance_id", "instanceId"} & set(series.dimensions)


def test_dimensions_are_renamed_to_wire_keys_the_backend_accepts() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    for event in hand_labelled_events():
        _ingest(aggregator, event)
    clock.advance(_BUCKET)

    snapshots = _emitter(aggregator).collect()

    keys = {k for s in snapshots for series in s.series for k in series.dimensions}
    assert keys <= WIRE_DIMENSION_KEYS
    assert {"session", "symbol", "side", "ordType", "rejectReason"} <= keys


def test_every_production_dimension_has_a_wire_name() -> None:
    # A dimension added to COUNTER_DIMENSIONS / LATENCY_DIMENSIONS without a
    # wire name would 400 every batch; every metric must also carry
    # instance_id, since a snapshot is per instance.
    for metric, dims in _ALL_DIMENSIONS.items():
        assert "instance_id" in dims, metric
        assert set(dims) - {"instance_id"} <= set(WIRE_DIMENSION), metric
    assert set(WIRE_DIMENSION.values()) <= WIRE_DIMENSION_KEYS


def test_metrics_with_different_dimension_sets_stay_in_separate_series() -> None:
    # FR-MET-030: orders_submitted must not acquire a rejectReason label, and
    # a reject must not lose its own.
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    for event in hand_labelled_events():
        _ingest(aggregator, event)
    clock.advance(_BUCKET)

    (snapshot,) = _emitter(aggregator).collect()

    for series in snapshot.series:
        if "orders_submitted" in series.counters:
            assert "rejectReason" not in series.dimensions
        if "orders_rejected" in series.counters:
            assert "rejectReason" in series.dimensions


def test_agent_scoped_counters_publish_with_no_series_dimensions() -> None:
    # AGENT_DIMS is just (instance_id,): once that moves to the snapshot,
    # the series is instance-wide — `{}` — and parse_errors keeps `reason`.
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    aggregator.ingest_agent_counters(
        dims={"instance_id": "magic-prod-01"},
        counters={"log_lines_read": Decimal(40)},
        at=_T0,
    )
    aggregator.ingest_agent_counters(
        dims={"instance_id": "magic-prod-01", "reason": "bad_checksum"},
        counters={"parse_errors": Decimal(2)},
        at=_T0,
    )
    clock.advance(_BUCKET)

    (snapshot,) = _emitter(aggregator).collect()

    by_dims = {tuple(sorted(s.dimensions.items())): s for s in snapshot.series}
    assert by_dims[()].counters == {"log_lines_read": Decimal(40)}
    assert by_dims[(("reason", "bad_checksum"),)].counters == {
        "parse_errors": Decimal(2)
    }


def test_cardinality_fold_stays_under_the_real_instance() -> None:
    # FR-MET-029: labels past the cap fold to __other__, the fold is counted,
    # and nothing is lost — but the snapshot still belongs to the real
    # instance, never to an instance named __other__.
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock, max_label_sets=2)
    for symbol in ("AAA", "BBB", "CCC", "DDD"):
        _ingest(aggregator, _order(_T0, symbol=symbol))
    clock.advance(_BUCKET)

    (snapshot,) = _emitter(aggregator).collect()

    assert snapshot.instance_id == "magic-prod-01"
    assert aggregator.cardinality_folded > 0
    symbols = {
        s.dimensions["symbol"]
        for s in snapshot.series
        if "orders_submitted" in s.counters
    }
    assert OTHER_LABEL in symbols
    assert _counter_total([snapshot], "orders_submitted") == Decimal(4)


def test_histograms_are_carried_with_their_full_payload() -> None:
    # FR-MET-025/026: boundary buckets plus exact count/sum/min/max.
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    correlator = LatencyCorrelator(aggregator, clock=clock)
    order = _order(_T0)
    ack = ExecutionReportEvent(
        event_time_utc=_T0 + timedelta(milliseconds=42),
        instance_id="magic-prod-01",
        session_id="MAGIC->EXCH1",
        cl_ord_id_hash=order.cl_ord_id_hash,
        order_id_hash="OID-1",
        exec_id_hash="EXEC-1",
        exec_type="New",
        ord_status="New",
        symbol="AAPL",
        side="Buy",
        ord_type="Limit",
    )
    for event in (order, ack):
        _ingest(aggregator, event)
        correlator.ingest(event)
    clock.advance(_BUCKET)

    (snapshot,) = _emitter(aggregator).collect()

    (payload,) = [
        s.histograms["ack_latency_ms"]
        for s in snapshot.series
        if "ack_latency_ms" in s.histograms
    ]
    assert payload.count == 1
    assert payload.sum == payload.min == payload.max == Decimal(42)
    assert payload.buckets["50"] == 1
    assert sum(payload.buckets.values()) == 1


def test_snapshot_survives_the_wire_round_trip() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    for event in hand_labelled_events():
        _ingest(aggregator, event)
    clock.advance(_BUCKET)
    (snapshot,) = _emitter(aggregator).collect()

    wire = snapshot.model_dump_json(by_alias=True)

    assert Snapshot.model_validate_json(wire) == snapshot


# --- SnapshotEmitter: idle instances (FR-MET-024, FR-MET-028) --------------


def test_idle_instance_gets_a_series_less_snapshot_every_bucket() -> None:
    # FR-MET-024: one snapshot per completed bucket per instance. FR-MET-027
    # drops all-zero *series*, never the snapshot — and the snapshot is what
    # carries the gauges through a quiet period.
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    emitter = _emitter(aggregator, instance_ids=("magic-prod-01",))
    _ingest(aggregator, _order(_T0))
    clock.advance(_BUCKET)
    (busy,) = emitter.collect()
    assert busy.series

    idle_ages: list[float] = []
    for i in range(1, 4):
        clock.advance(_BUCKET)
        (idle,) = emitter.collect()
        assert idle.instance_id == "magic-prod-01"
        assert idle.bucket_start_utc == _T0 + timedelta(seconds=i * _BUCKET)
        assert idle.series == []
        idle_ages.append(idle.gauges["seconds_since_last_event"])
    # The staleness signal keeps rising instead of freezing at the last
    # busy bucket.
    assert idle_ages == sorted(idle_ages) and idle_ages[0] < idle_ages[-1]


def test_first_collect_does_not_backfill_before_the_process_existed() -> None:
    clock = FakeClock(_T0.timestamp() + 10 * _BUCKET)
    emitter = _emitter(_aggregator(clock), instance_ids=("magic-prod-01",))

    (first,) = emitter.collect()

    assert first.bucket_start_utc == _T0 + timedelta(seconds=9 * _BUCKET)


def test_collecting_twice_within_a_bucket_sends_nothing_twice() -> None:
    clock = FakeClock(_T0.timestamp())
    emitter = _emitter(_aggregator(clock), instance_ids=("magic-prod-01",))
    clock.advance(_BUCKET)
    assert len(emitter.collect()) == 1
    clock.advance(_BUCKET / 2)
    assert emitter.collect() == []


def test_busy_and_idle_instances_each_get_exactly_one_snapshot() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    emitter = _emitter(aggregator, instance_ids=("busy", "idle"))
    _ingest(aggregator, _order(_T0, instance="busy"))
    clock.advance(_BUCKET)

    snapshots = emitter.collect()

    by_instance = {s.instance_id: s for s in snapshots}
    assert len(snapshots) == 2 and set(by_instance) == {"busy", "idle"}
    assert by_instance["busy"].series and by_instance["idle"].series == []
    assert by_instance["busy"].gauges and by_instance["idle"].gauges


def test_unconfigured_instance_with_data_is_still_published() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    _ingest(aggregator, _order(_T0, instance="surprise"))
    clock.advance(_BUCKET)

    snapshots = _emitter(aggregator, instance_ids=("configured",)).collect()

    assert {s.instance_id for s in snapshots} == {"surprise", "configured"}


def test_stalled_collect_fills_idle_buckets_only_within_retention() -> None:
    # A stalled loop resumes with every missed bucket — but never older
    # than the aggregator itself retains (capacity = 60s / 10s = 6).
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock, windows={"1m": 60})
    emitter = _emitter(aggregator, instance_ids=("magic-prod-01",))
    clock.advance(_BUCKET)
    emitter.collect()

    clock.advance(20 * _BUCKET)
    starts = [s.bucket_start_utc for s in emitter.collect()]

    assert len(starts) == 6
    assert starts == sorted(starts)
    assert starts[-1] == _T0 + timedelta(seconds=20 * _BUCKET)


def test_late_republish_of_an_old_bucket_carries_no_gauges_or_idle_twins() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    emitter = _emitter(aggregator, instance_ids=("magic-prod-01", "other"))
    _ingest(aggregator, _order(_T0))
    clock.advance(2 * _BUCKET)
    emitter.collect()

    _ingest(aggregator, _order(_T0 + timedelta(seconds=1), symbol="MSFT"))
    (republished,) = emitter.collect()

    assert republished.bucket_start_utc == _T0
    assert republished.gauges == {}


# --- SnapshotEmitter: restarted (FR-LOG-021) --------------------------------


def test_restarted_marks_only_the_first_snapshot_per_instance() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    emitter = _emitter(aggregator)

    _ingest(aggregator, _order(_T0))
    _ingest(aggregator, _order(_T0 + timedelta(seconds=_BUCKET)))
    clock.advance(2 * _BUCKET)
    first, second = emitter.collect()
    assert (first.restarted, second.restarted) == (True, False)

    # A late re-publish of that first bucket is not a new restart.
    _ingest(aggregator, _order(_T0 + timedelta(seconds=1), symbol="MSFT"))
    (republished,) = emitter.collect()
    assert republished.bucket_start_utc == _T0
    assert republished.restarted is False

    # An instance first seen later is still marked on its own first snapshot.
    # (An idle configured instance's first, series-less snapshot counts too.)
    _ingest(aggregator, _order(_T0 + timedelta(seconds=2 * _BUCKET), instance="b"))
    clock.advance(_BUCKET)
    (new_instance,) = emitter.collect()
    assert new_instance.restarted is True


# --- SnapshotEmitter: gauges (FR-MET-028, FR-MET-031) -----------------------


def test_gauges_ride_only_on_the_newest_bucket_for_every_instance_in_it() -> None:
    # Gauges are "now"; on a backfilled older bucket they would be stamped
    # with a time they were not observed at.
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    correlator = LatencyCorrelator(aggregator, clock=clock)
    for offset, instance in ((0, "a"), (_BUCKET, "a"), (_BUCKET, "b")):
        order = _order(_T0 + timedelta(seconds=offset), instance=instance)
        _ingest(aggregator, order)
        correlator.ingest(order)
    clock.advance(2 * _BUCKET)

    snapshots = _emitter(aggregator, correlator=correlator).collect()

    with_gauges = {(s.instance_id, s.bucket_start_utc) for s in snapshots if s.gauges}
    newest = _T0 + timedelta(seconds=_BUCKET)
    assert with_gauges == {("a", newest), ("b", newest)}
    assert all(s.gauges["pending_orders"] == 3 for s in snapshots if s.gauges)


def test_publish_failure_gauge_is_omitted_when_no_publisher_is_wired() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    _ingest(aggregator, _order(_T0))
    clock.advance(_BUCKET)

    (snapshot,) = _emitter(aggregator).collect()

    assert "consecutive_publish_failures" not in snapshot.gauges
    assert "seconds_since_last_event" in snapshot.gauges


def test_publish_failure_gauge_reads_the_live_provider() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    failures = [0]
    emitter = _emitter(aggregator, consecutive_publish_failures=lambda: failures[0])
    _ingest(aggregator, _order(_T0))
    clock.advance(_BUCKET)
    failures[0] = 4

    (snapshot,) = emitter.collect()

    assert snapshot.gauges["consecutive_publish_failures"] == 4


def test_idle_instance_first_snapshot_is_marked_restarted() -> None:
    clock = FakeClock(_T0.timestamp())
    emitter = _emitter(_aggregator(clock), instance_ids=("magic-prod-01",))
    clock.advance(_BUCKET)
    (first,) = emitter.collect()
    clock.advance(_BUCKET)
    (second,) = emitter.collect()
    assert (first.restarted, second.restarted) == (True, False)


def test_queue_depth_and_read_lag_gauges_read_their_live_providers() -> None:
    # spec 004 §3's gauge set: pending_orders, read_lag_ms,
    # publish_queue_depth, consecutive_publish_failures.
    clock = FakeClock(_T0.timestamp())
    depth = [0]
    lag: list[float | None] = [None]
    emitter = _emitter(
        _aggregator(clock),
        instance_ids=("magic-prod-01",),
        consecutive_publish_failures=lambda: 0,
        publish_queue_depth=lambda: depth[0],
        read_lag_ms=lambda: lag[0],
    )
    clock.advance(_BUCKET)
    (no_lag_yet,) = emitter.collect()
    # No file has read a line yet: read lag is unknown, never 0.
    assert "read_lag_ms" not in no_lag_yet.gauges
    assert no_lag_yet.gauges["publish_queue_depth"] == 0
    assert no_lag_yet.gauges["consecutive_publish_failures"] == 0

    depth[0], lag[0] = 7, 120.0
    clock.advance(_BUCKET)
    (later,) = emitter.collect()
    assert later.gauges["publish_queue_depth"] == 7
    assert later.gauges["read_lag_ms"] == 120.0


def test_unwired_gauge_sources_are_omitted_not_zero() -> None:
    clock = FakeClock(_T0.timestamp())
    emitter = _emitter(_aggregator(clock), instance_ids=("magic-prod-01",))
    clock.advance(_BUCKET)
    (snapshot,) = emitter.collect()
    assert not {
        "publish_queue_depth",
        "read_lag_ms",
        "consecutive_publish_failures",
    } & set(snapshot.gauges)


# --- SnapshotEmitter.run ----------------------------------------------------


def test_run_pushes_completed_snapshots_until_stopped() -> None:
    clock = FakeClock(_T0.timestamp())
    aggregator = _aggregator(clock)
    emitter = _emitter(aggregator)
    _ingest(aggregator, _order(_T0))
    _ingest(aggregator, _order(_T0 + timedelta(seconds=_BUCKET)))
    clock.advance(_BUCKET)  # first bucket closed, second still open
    received: list[Snapshot] = []

    async def scenario() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(
            emitter.run(received.append, stop, interval_seconds=60)
        )
        await asyncio.sleep(0)  # first tick
        stop.set()
        await task

    asyncio.run(scenario())

    # Only the closed bucket; the open one waits for a later tick.
    assert [s.bucket_start_utc for s in received] == [_T0]
