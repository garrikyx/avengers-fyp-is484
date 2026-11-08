"""UBS-129 / FR-HLT-016: the heartbeat's `resourceUsage` is the agent's own
RSS and CPU from the Host Monitor's sampler, never the always-zero default.
"""

from datetime import UTC, datetime

from telemetry_agent.health.config import HeartbeatConfig
from telemetry_agent.health.host_monitor import (
    HostConfig,
    HostMonitor,
    PsutilSampler,
)
from telemetry_agent.health.reporter import HealthReporter
from telemetry_agent.health.wire import to_ingestion_heartbeat
from telemetry_shared.models.health import ResourceUsage

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


def _reporter() -> HealthReporter:
    config = HeartbeatConfig(
        agent_id="magic-agent-sg-01",
        instance_ids=("magic-prod-01",),
        agent_version="0.1.0+test",
        interval_seconds=10.0,
    )
    return HealthReporter({}, heartbeat=config, clock=lambda: T0)


def test_fr_hlt_016_no_provider_means_resource_usage_is_unmeasured() -> None:
    assert _reporter().build_heartbeat().resource_usage is None


def test_fr_hlt_016_heartbeat_carries_the_providers_rss_and_cpu() -> None:
    reporter = _reporter()
    usage = ResourceUsage(rss_mb=84.0, cpu_percent=1.8)
    reporter.set_resource_usage_provider(lambda: usage)

    heartbeat = reporter.build_heartbeat()

    assert heartbeat.resource_usage == usage
    wire = to_ingestion_heartbeat(heartbeat)
    assert (wire.resource_usage.rss_mb, wire.resource_usage.cpu_percent) == (84.0, 1.8)


def test_fr_hlt_016_a_provider_with_nothing_yet_stays_unmeasured() -> None:
    reporter = _reporter()
    reporter.set_resource_usage_provider(lambda: None)
    assert reporter.build_heartbeat().resource_usage is None


def test_fr_hlt_016_real_sampler_reports_non_zero_rss_through_the_heartbeat() -> None:
    """OS-agnostic smoke test of the production sampler (psutil)."""
    monitor = HostMonitor(HostConfig(disk_paths=(".",), memory=True), PsutilSampler())
    monitor.sample_once()
    reporter = _reporter()
    reporter.set_resource_usage_provider(monitor.resource_usage)

    wire = to_ingestion_heartbeat(reporter.build_heartbeat())

    assert wire.resource_usage.rss_mb > 0
    assert wire.resource_usage.cpu_percent >= 0
    assert monitor.counters.snapshot().get("host_sample_errors", 0) == 0
    gauges = monitor.gauges()
    assert 0.0 <= gauges["host_disk_used_ratio"] <= 1.0
    assert 0.0 < gauges["host_memory_used_ratio"] <= 1.0
