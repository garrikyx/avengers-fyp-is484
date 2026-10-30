"""`latency_summary` answers read the ack-latency percentiles off
`LatencySummary` (`p50`, `p95`) and say so when there are too few samples."""

from __future__ import annotations

from telemetry_backend.nl.render import formatters as fmt
from telemetry_shared.models.metrics import LatencySummary


def _summary(*, p50: float | None, p95: float | None, count: int) -> LatencySummary:
    return LatencySummary(p50=p50, p95=p95, p99=None, avg=None, count=count)


def test_latency_phrase_reports_the_percentiles_and_sample_count() -> None:
    latency = {"ack_latency_ms": _summary(p50=120.4, p95=480.6, count=60)}

    assert fmt.latency_phrase(latency) == (
        "Ack latency p50 120 ms, p95 481 ms over 60 samples."
    )


def test_latency_phrase_says_so_when_there_are_no_samples() -> None:
    latency = {"ack_latency_ms": _summary(p50=None, p95=None, count=0)}

    assert "not available" in fmt.latency_phrase(latency)


def test_latency_phrase_says_so_when_percentiles_are_withheld() -> None:
    """The aggregator nulls percentiles below its minimum sample size even
    when some samples exist."""
    latency = {"ack_latency_ms": _summary(p50=None, p95=None, count=7)}

    assert "not available" in fmt.latency_phrase(latency)


def test_latency_phrase_without_an_ack_latency_metric() -> None:
    assert "not available" in fmt.latency_phrase({})
