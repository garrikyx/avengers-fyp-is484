from decimal import Decimal

from telemetry_agent.metrics.histogram import Histogram


def test_record_places_values_into_the_correct_exclusive_bucket() -> None:
    hist = Histogram()
    for value in (
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
    ):
        hist.record(Decimal(value))

    assert hist.count == 20
    assert hist.sum_ms == Decimal(sum(range(1, 21)))
    assert hist.min_ms == Decimal(1)
    assert hist.max_ms == Decimal(20)
    assert hist.buckets["1"] == 1  # {1}
    assert hist.buckets["5"] == 4  # {2,3,4,5}
    assert hist.buckets["10"] == 5  # {6,7,8,9,10}
    assert hist.buckets["25"] == 10  # {11..20}
    assert hist.buckets["+Inf"] == 0


def test_record_above_the_largest_boundary_falls_into_overflow() -> None:
    hist = Histogram()
    hist.record(Decimal(9999))
    assert hist.buckets["+Inf"] == 1
    assert hist.max_ms == Decimal(9999)


def test_merge_is_bucket_wise_addition() -> None:
    a = Histogram()
    a.record(Decimal(5))
    b = Histogram()
    b.record(Decimal(15))

    a.merge(b)

    assert a.count == 2
    assert a.sum_ms == Decimal(20)
    assert a.min_ms == Decimal(5)
    assert a.max_ms == Decimal(15)
    assert a.buckets["5"] == 1
    assert a.buckets["25"] == 1


def test_percentile_below_min_sample_size_returns_none() -> None:
    hist = Histogram()
    for value in range(1, 6):  # only 5 samples
        hist.record(Decimal(value))
    assert hist.percentile(0.5, min_sample_size=20) is None


def test_percentile_interpolates_within_the_identified_bucket() -> None:
    hist = Histogram()
    for value in range(1, 21):  # 1..20, matches the hand-worked example
        hist.record(Decimal(value))

    # target_rank(p50) = 10; cumulative reaches 10 exactly at the "10" bucket
    # boundary (buckets: 1,4,5 -> cumulative 1,5,10), fraction=1.0 -> == 10.
    assert hist.percentile(0.5) == Decimal(10)

    # target_rank(p95) = 19; falls 9/10 of the way through the "25" bucket
    # (cumulative after "10" is 10, bucket "25" holds 10 samples):
    # 10 + (19-10)/10 * (25-10) == 23.5
    assert hist.percentile(0.95) == Decimal("23.5")

    # p99, the third AC-named percentile, never independently exercised
    # before — target_rank(p99) = 19.8, same "25" bucket as p95:
    # 10 + (19.8-10)/10 * (25-10) == 24.7
    assert hist.percentile(0.99) == Decimal("24.7")


def test_percentile_interpolates_within_the_overflow_bucket() -> None:
    hist = Histogram()
    for value in range(1, 21):  # 1..20
        hist.record(Decimal(value))
    hist.record(Decimal(9000))  # one sample far above every fixed boundary

    # count=21, target_rank(p99)=20.79. Every fixed boundary through "5000"
    # only reaches cumulative 20 (the 1..20 samples), so the target lands in
    # "+Inf" itself (bucket_count=1), interpolating between the "5000"
    # boundary and max_ms=9000:
    # 5000 + (20.79-20)/1 * (9000-5000) == 8160
    assert hist.percentile(0.99) == Decimal("8160")
