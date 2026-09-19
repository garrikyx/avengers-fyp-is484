"""FR-STM-002/003/004: counters merge by summation; ratios are recomputed
from summed numerator/denominator (never averaged per agent); histograms
merge bucket-wise (never averaged percentiles), and a metric no contributing
agent reported for a dimension-set is simply absent, never fabricated.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.metric_store import MetricStore
from telemetry_shared.metrics import Histogram
from telemetry_shared.models.snapshot import HistogramPayload, SeriesEntry, Snapshot

DIMS = {"session": "MAGIC->EXCH1", "symbol": "ABC"}
BUCKET_START = datetime(2026, 6, 12, 4, 0, 0, tzinfo=UTC)
NOW = BUCKET_START + timedelta(seconds=30)


def _histogram_payload(values: list[int]) -> HistogramPayload:
    histogram = Histogram()
    for value in values:
        histogram.record(Decimal(value))
    return HistogramPayload(
        count=histogram.count,
        sum=histogram.sum_ms,
        min=histogram.min_ms,
        max=histogram.max_ms,
        buckets=dict(histogram.buckets),
    )


def _snapshot(
    *,
    agent_id: str,
    counters: dict[str, int] | None = None,
    histograms: dict[str, HistogramPayload] | None = None,
    dimensions: dict[str, str] = DIMS,
) -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id=agent_id,
        application="Magic",
        instance_id="magic-prod-01",
        bucket_start_utc=BUCKET_START,
        bucket_seconds=10,
        series=[
            SeriesEntry(
                dimensions=dimensions,
                counters={k: Decimal(v) for k, v in (counters or {}).items()},
                histograms=histograms or {},
            )
        ],
    )


def _read_one_group(store: MetricStore):
    groups = store.read(
        "magic-prod-01",
        from_utc=BUCKET_START,
        to_utc=BUCKET_START + timedelta(seconds=10),
    )
    assert len(groups) == 1
    return groups[0]


def test_counters_merge_by_summation_across_agents() -> None:
    store = MetricStore(StreamProcessorConfig())
    store.merge(
        _snapshot(agent_id="agent-a", counters={"orders_submitted": 100}),
        canonical_start=BUCKET_START,
        now=NOW,
    )
    store.merge(
        _snapshot(agent_id="agent-b", counters={"orders_submitted": 250}),
        canonical_start=BUCKET_START,
        now=NOW,
    )

    group = _read_one_group(store)
    assert group.counters["orders_submitted"] == 350


def test_redelivery_from_the_same_agent_overwrites_not_double_adds() -> None:
    """A retried publish that misses batchId-level dedupe (a different
    ticket's concern) must not double-count once it reaches the store.
    """
    store = MetricStore(StreamProcessorConfig())
    store.merge(
        _snapshot(agent_id="agent-a", counters={"orders_submitted": 100}),
        canonical_start=BUCKET_START,
        now=NOW,
    )
    store.merge(
        _snapshot(agent_id="agent-a", counters={"orders_submitted": 100}),
        canonical_start=BUCKET_START,
        now=NOW,
    )

    group = _read_one_group(store)
    assert group.counters["orders_submitted"] == 100


def test_reject_rate_recomputed_from_sums_not_averaged_per_agent() -> None:
    """Two agents of unequal volume (FR-STM-003's required test shape):
    agent A: 10/110 rejected (~9.09%); agent B: 10/1010 rejected (~0.99%).
    Averaging the two per-agent rates gives ~5.04% — wrong. The correct
    combined rate sums numerators and denominators first: 20/1120 ~ 1.79%.
    """
    store = MetricStore(StreamProcessorConfig())
    agent_a_counters = {"orders_acked": 100, "orders_rejected": 10}
    agent_b_counters = {"orders_acked": 1000, "orders_rejected": 10}
    store.merge(
        _snapshot(agent_id="agent-a", counters=agent_a_counters),
        canonical_start=BUCKET_START,
        now=NOW,
    )
    store.merge(
        _snapshot(agent_id="agent-b", counters=agent_b_counters),
        canonical_start=BUCKET_START,
        now=NOW,
    )

    group = _read_one_group(store)
    correct_combined_rate = 20 / 1120
    naive_average_of_per_agent_rates = ((10 / 110) + (10 / 1010)) / 2

    assert group.indicators.reject_rate.value is not None
    assert abs(group.indicators.reject_rate.value - correct_combined_rate) < 1e-9
    assert group.indicators.reject_rate.denominator == 1120
    assert (
        abs(group.indicators.reject_rate.value - naive_average_of_per_agent_rates)
        > 0.03
    )


def test_histograms_merge_bucket_wise_not_by_averaging_percentiles() -> None:
    fast_agent_values = list(range(1, 26))  # small latencies, 25 samples
    slow_agent_values = list(range(400, 425))  # larger latencies, 25 samples

    fast_histogram = Histogram()
    slow_histogram = Histogram()
    for value in fast_agent_values:
        fast_histogram.record(Decimal(value))
    for value in slow_agent_values:
        slow_histogram.record(Decimal(value))

    # Reference: the same bucket-wise merge the store is supposed to do,
    # computed directly (test_histogram.py already proves Histogram.merge
    # itself is correct bucket-wise addition).
    expected = Histogram(
        count=fast_histogram.count,
        sum_ms=fast_histogram.sum_ms,
        min_ms=fast_histogram.min_ms,
        max_ms=fast_histogram.max_ms,
        buckets=dict(fast_histogram.buckets),
    )
    expected.merge(slow_histogram)
    expected_p95 = expected.percentile(0.95)

    naive_average_p95 = (
        fast_histogram.percentile(0.95) + slow_histogram.percentile(0.95)
    ) / 2

    store = MetricStore(StreamProcessorConfig())
    store.merge(
        _snapshot(
            agent_id="agent-a",
            histograms={
                "ack_latency_ms": HistogramPayload(
                    count=fast_histogram.count,
                    sum=fast_histogram.sum_ms,
                    min=fast_histogram.min_ms,
                    max=fast_histogram.max_ms,
                    buckets=dict(fast_histogram.buckets),
                )
            },
        ),
        canonical_start=BUCKET_START,
        now=NOW,
    )
    store.merge(
        _snapshot(
            agent_id="agent-b",
            histograms={
                "ack_latency_ms": HistogramPayload(
                    count=slow_histogram.count,
                    sum=slow_histogram.sum_ms,
                    min=slow_histogram.min_ms,
                    max=slow_histogram.max_ms,
                    buckets=dict(slow_histogram.buckets),
                )
            },
        ),
        canonical_start=BUCKET_START,
        now=NOW,
    )

    group = _read_one_group(store)
    summary = group.latency["ack_latency_ms"]
    assert summary.count == 50
    assert summary.p95 == float(expected_p95)
    assert summary.p95 != float(naive_average_p95)


def test_a_metric_no_contributing_agent_reported_is_absent_not_fabricated() -> None:
    store = MetricStore(StreamProcessorConfig())
    only_counters = _snapshot(agent_id="agent-a", counters={"orders_submitted": 5})
    store.merge(only_counters, canonical_start=BUCKET_START, now=NOW)

    group = _read_one_group(store)
    assert "ack_latency_ms" not in group.latency


def test_a_metric_only_some_agents_reported_still_merges_the_ones_that_did() -> None:
    store = MetricStore(StreamProcessorConfig())
    values = list(range(1, 26))
    histogram = Histogram()
    for value in values:
        histogram.record(Decimal(value))
    payload = HistogramPayload(
        count=histogram.count,
        sum=histogram.sum_ms,
        min=histogram.min_ms,
        max=histogram.max_ms,
        buckets=dict(histogram.buckets),
    )

    store.merge(
        _snapshot(agent_id="agent-a", histograms={"ack_latency_ms": payload}),
        canonical_start=BUCKET_START,
        now=NOW,
    )
    store.merge(
        _snapshot(agent_id="agent-b", counters={"orders_submitted": 3}),
        canonical_start=BUCKET_START,
        now=NOW,
    )

    group = _read_one_group(store)
    assert group.latency["ack_latency_ms"].count == 25
    assert group.counters["orders_submitted"] == 3
