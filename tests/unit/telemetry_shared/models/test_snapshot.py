"""Wire-format Snapshot contract (spec 004 §3, FR-MET-024..028)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError
from telemetry_shared.models.snapshot import HistogramPayload, Snapshot

SPEC_004_EXAMPLE = {
    "schemaVersion": 1,
    "agentId": "magic-agent-sg-01",
    "application": "Magic",
    "instanceId": "magic-prod-01",
    "bucketStartUtc": "2026-06-12T04:00:00.000Z",
    "bucketSeconds": 10,
    "restarted": False,
    "series": [
        {
            "dimensions": {"session": "MAGIC->EXCH1", "symbol": "ABC", "side": "buy"},
            "counters": {
                "orders_submitted": 120,
                "orders_acked": 118,
                "orders_rejected": 2,
            },
            "histograms": {
                "ack_latency_ms": {
                    "count": 118,
                    "sum": 2714,
                    "min": 4,
                    "max": 96,
                    "buckets": {
                        "1": 0,
                        "5": 12,
                        "10": 60,
                        "25": 38,
                        "50": 6,
                        "100": 2,
                        "250": 0,
                        "500": 0,
                        "1000": 0,
                        "5000": 0,
                        "+Inf": 0,
                    },
                }
            },
        }
    ],
    "gauges": {"pending_orders": 340, "read_lag_ms": 120, "publish_queue_depth": 4},
}


def test_parses_the_spec_004_example_verbatim() -> None:
    snapshot = Snapshot.model_validate(SPEC_004_EXAMPLE)

    assert snapshot.agent_id == "magic-agent-sg-01"
    assert snapshot.instance_id == "magic-prod-01"
    assert snapshot.bucket_seconds == 10
    assert snapshot.restarted is False
    assert len(snapshot.series) == 1

    series = snapshot.series[0]
    assert series.dimensions == {
        "session": "MAGIC->EXCH1",
        "symbol": "ABC",
        "side": "buy",
    }
    assert series.counters["orders_submitted"] == Decimal(120)


def test_unknown_top_level_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Snapshot.model_validate({**SPEC_004_EXAMPLE, "unexpectedField": 1})


def test_unknown_dimension_shaped_extra_key_on_a_series_is_rejected() -> None:
    bad_series = {**SPEC_004_EXAMPLE["series"][0], "extra": 1}
    bad = {**SPEC_004_EXAMPLE, "series": [bad_series]}
    with pytest.raises(ValidationError):
        Snapshot.model_validate(bad)


def test_histogram_payload_requires_the_full_shape_not_a_percentile_summary() -> None:
    """FR-STM-004: there is no wire shape for 'summary percentiles only, no
    histogram' — a histogram is either the full boundary-bucketed payload or
    it is absent from `histograms{}` entirely. Enforcing this at the schema
    boundary makes the failure mode FR-STM-004 warns about structurally
    unrepresentable rather than a runtime check that could be forgotten.
    """
    with pytest.raises(ValidationError):
        HistogramPayload.model_validate({"p50": 12, "p95": 40, "p99": 90})

    with pytest.raises(ValidationError):
        HistogramPayload.model_validate({"count": 10, "sum": 100})  # missing buckets


def test_to_histogram_ignores_unrecognised_bucket_keys_defensively() -> None:
    payload = HistogramPayload.model_validate(
        {
            "count": 1,
            "sum": 5,
            "min": 5,
            "max": 5,
            "buckets": {"5": 1, "not-a-real-boundary": 999},
        }
    )
    histogram = payload.to_histogram()
    assert histogram.buckets["5"] == 1
    assert "not-a-real-boundary" not in histogram.buckets
    assert histogram.count == 1
