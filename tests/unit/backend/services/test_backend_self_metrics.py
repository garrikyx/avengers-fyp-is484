"""UBS-96: SelfMetrics without HTTP."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.services.agent_registry import AgentRegistry
from telemetry_backend.services.ingestion import AcceptedIngestion, IngestionService
from telemetry_backend.services.self_metrics import SelfMetrics
from telemetry_backend.services.stream_processor import StreamProcessor
from telemetry_shared.models.ingestion import Heartbeat, ResourceUsage
from telemetry_shared.models.snapshot import SeriesEntry, Snapshot

T0 = datetime(2026, 9, 20, 4, 0, 0, tzinfo=UTC)


def heartbeat(agent_id: str) -> Heartbeat:
    return Heartbeat(
        schema_version=1,
        agent_id=agent_id,
        instance_ids=["i"],
        sent_at_utc=T0,
        agent_version="0",
        uptime_seconds=1,
        status="healthy",
        files=[],
        parse_error_count_last5_min=0,
        callback_failures_last5_min=0,
        publish_queue_depth=0,
        publish_buffer_bytes=0,
        dropped_events_last5_min=0,
        active_alert_count=0,
        resource_usage=ResourceUsage(rss_mb=1, cpu_percent=0, active_tasks=1),
    )


def snapshot(at: datetime) -> Snapshot:
    return Snapshot(
        schema_version=1,
        agent_id="agent-a",
        application="Magic",
        instance_id="magic-prod-01",
        bucket_start_utc=at,
        bucket_seconds=10,
        series=[SeriesEntry(dimensions={"session": "S", "symbol": "ABC"}, counters={})],
    )


def body(metrics: SelfMetrics) -> str:
    return metrics.exposition()[0].decode()


def test_two_instances_do_not_share_a_registry() -> None:
    """Private CollectorRegistry: no duplicate-metric errors, no cross-talk."""
    reg = AgentRegistry(clock=lambda: T0)
    a, b = SelfMetrics(reg), SelfMetrics(reg)
    a.ingest_batches.inc()
    assert "ingest_batches_total 1.0" in body(a)
    assert "ingest_batches_total 0.0" in body(b)


def test_every_series_is_present_before_ingestion_is_bound() -> None:
    """A missing series looks like a broken exporter; 0 looks like idle."""
    text = body(SelfMetrics(AgentRegistry(clock=lambda: T0), clock=lambda: T0))
    for line in (
        "telemetry_backend_ingest_batches_total 0.0",
        "telemetry_backend_heartbeats_received_total 0.0",
        "telemetry_backend_ingest_dedupe_hits_total 0.0",
        "telemetry_backend_ingest_validation_failures_total 0.0",
        "telemetry_backend_ingest_queue_full_total 0.0",
        "telemetry_backend_ingest_queue_depth 0.0",
        'telemetry_backend_dropped_payloads_total{reason="bucket_too_old"} 0.0',
        "telemetry_backend_store_memory_bytes 0.0",
        "telemetry_backend_agents_known 0.0",
        "telemetry_backend_warming_up 1.0",
    ):
        assert line in text, line


def test_ingestion_and_store_numbers_are_read_at_scrape_time() -> None:
    config = StreamProcessorConfig(warmup_window_seconds=0)
    processor = StreamProcessor(config, started_at=T0)
    service = IngestionService(queue_size=1, stream_processor=processor)
    metrics = SelfMetrics(
        AgentRegistry(clock=lambda: T0),
        clock=lambda: T0 + timedelta(seconds=5),
        ingestion=lambda: service,
    )
    service.record_rejection()
    service.record_rejection()
    assert service.enqueue(AcceptedIngestion())
    assert not service.enqueue(AcceptedIngestion())  # queue_size=1 -> full

    text = body(metrics)
    assert "telemetry_backend_ingest_validation_failures_total 2.0" in text
    assert "telemetry_backend_ingest_queue_full_total 1.0" in text
    assert "telemetry_backend_ingest_queue_depth 1.0" in text
    assert "telemetry_backend_warming_up 1.0" in text  # no data yet

    processor.process_snapshot(snapshot(T0), now=T0)
    old = T0 - timedelta(hours=2)
    processor.process_snapshot(snapshot(old), now=T0)  # too old -> dropped

    text = body(metrics)
    assert "telemetry_backend_warming_up 0.0" in text
    dropped = 'telemetry_backend_dropped_payloads_total{reason="bucket_too_old"}'
    assert f"{dropped} 1.0" in text
    memory = next(
        line
        for line in text.splitlines()
        if line.startswith("telemetry_backend_store_memory_bytes ")
    )
    assert float(memory.split()[1]) > 0


def test_query_latency_histogram_is_labelled_by_route() -> None:
    m = SelfMetrics(AgentRegistry(clock=lambda: T0))
    m.query_latency.labels(route="/telemetry/health/agents").observe(0.2)
    assert (
        'query_latency_seconds_bucket{le="0.25",route="/telemetry/health/agents"} 1.0'
        in body(m)
    )


def test_concurrent_scrapes_never_produce_a_torn_exposition() -> None:
    """Every scrape must show one age line per registered agent, even while
    other scrapes are rebuilding the per-agent gauges."""
    reg = AgentRegistry(clock=lambda: T0)
    for i in range(20):
        reg.record_heartbeat(heartbeat(f"agent-{i:02d}"))
    m = SelfMetrics(reg, clock=lambda: T0)

    def scrape(_: int) -> int:
        return sum(
            1
            for line in body(m).splitlines()
            if line.startswith("telemetry_backend_agent_heartbeat_age_seconds{")
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        counts = list(pool.map(scrape, range(200)))
    assert set(counts) == {20}
