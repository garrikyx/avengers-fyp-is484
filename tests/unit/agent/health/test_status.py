"""FR-HLT-002/003: status rollup and reasons, using the signals UBS-58 has.

Builds `HealthSignals` directly so no files are needed; the file-backed path
is covered by test_reporter.py and the UBS-30 integration test.
"""

from datetime import UTC, datetime

from telemetry_agent.health.config import HealthThresholds
from telemetry_agent.health.reporter import HealthReporter, HealthSignals
from telemetry_shared.models.health import FileReadHealth

NOW = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


def _file(lag_ms: float | None) -> FileReadHealth:
    return FileReadHealth(path="/var/log/magic/fix.log", offset=10, read_lag_ms=lag_ms)


def test_no_signals_is_healthy_with_no_reasons() -> None:
    reporter = HealthReporter({})
    status, reasons = reporter.derive_status(HealthSignals(sampled_at=NOW))
    assert (status, reasons) == ("healthy", [])


def test_unread_file_is_not_a_reason() -> None:
    """FR-HLT-004: a file with no reads yet is a gap, not a zero and not a fault."""
    reporter = HealthReporter({})
    signals = HealthSignals(sampled_at=NOW, files={"Fix.log": _file(None)})
    assert reporter.derive_status(signals) == ("healthy", [])


def test_read_lag_over_threshold_is_degraded_with_named_reason() -> None:
    reporter = HealthReporter(
        {}, thresholds=HealthThresholds(read_lag_degraded_ms=5000)
    )
    signals = HealthSignals(sampled_at=NOW, files={"Fix.log": _file(6200)})
    status, reasons = reporter.derive_status(signals)
    assert status == "degraded"
    assert reasons == ["Fix.log: read lag 6200ms exceeds 5000ms threshold"]


def test_read_lag_at_threshold_is_still_healthy() -> None:
    reporter = HealthReporter(
        {}, thresholds=HealthThresholds(read_lag_degraded_ms=5000)
    )
    signals = HealthSignals(sampled_at=NOW, files={"Fix.log": _file(5000)})
    assert reporter.derive_status(signals) == ("healthy", [])


def test_every_lagging_file_gets_its_own_reason() -> None:
    reporter = HealthReporter(
        {}, thresholds=HealthThresholds(read_lag_degraded_ms=1000)
    )
    signals = HealthSignals(
        sampled_at=NOW,
        files={"Fix.log": _file(1500), "App.log": _file(200), "Gw.log": _file(9000)},
    )
    status, reasons = reporter.derive_status(signals)
    assert status == "degraded"
    assert [r.split(":")[0] for r in reasons] == ["Fix.log", "Gw.log"]


def test_legacy_degraded_threshold_kwarg_still_wins() -> None:
    reporter = HealthReporter(
        {},
        degraded_threshold_ms=100,
        thresholds=HealthThresholds(read_lag_degraded_ms=9e9),
    )
    assert reporter.degraded_threshold_ms == 100
    assert reporter.thresholds.parse_error_rate_unhealthy == 0.25  # rest kept
