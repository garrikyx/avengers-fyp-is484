"""UBS-116: MetricsIngestor turns parsed Application.log lines into
app-log counters in the same snapshot the Rule Engine reads."""

from datetime import UTC, datetime

from telemetry_agent.parser.applog.parser import AppLogParser
from telemetry_agent.parser.protocol import SourceMeta
from telemetry_agent.pipeline.ingest import MetricsIngestor

T0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
INSTANCE = "magic-prod-01"
_MAGIC_PATTERN = r"^\d{2}:\d{2}:\d{2}\.\d+ <\d+> \[[NWEIF]+\]"
_SIGNATURES = [
    ("out_of_memory", r"OutOfMemoryError|std::bad_alloc"),
    ("%_connection_disconnected", r"(\w+) connection disconnected"),
]

LINES = [
    b"10:00:00.000001 <1> [I] VS_1: started",
    b"10:00:00.000002 <1> [W] VS_1: GR connection disconnected",
    b"10:00:00.000003 <2> [F] VS_2: GR connection disconnected",
    b"10:00:00.000004 <2> [E] VS_2: java.lang.OutOfMemoryError",
    b"10:00:00.000005 <3> [E] OMS: order book rebuild failed",
    b"matches the app-log pattern only by being unparsable",  # no telemetry
]


def _meta() -> SourceMeta:
    return SourceMeta(
        instance_id=INSTANCE, path="Application.log", log_type="app", read_at=T0
    )


def _ingested() -> MetricsIngestor:
    ingestor = MetricsIngestor.build_default(
        clock=lambda: T0.timestamp(), monotonic=lambda: 100.0
    )
    parser = AppLogParser(
        app_log_patterns=[_MAGIC_PATTERN], error_signatures=_SIGNATURES
    )
    for line in LINES:
        ingestor.ingest(parser.parse(line, _meta()), _meta())
    return ingestor


def test_app_log_counts_appear_in_the_snapshot() -> None:
    ingestor = _ingested()

    counters = ingestor.aggregator.snapshot("1m")[()].counters
    assert counters["log_lines_read"] == 6
    assert counters["app_log_lines"] == 5
    assert counters["app_log_errors"] == 3  # E, F, E
    assert counters["app_error_signatures"] == 3
    assert ingestor.stats()["ingest_errors"] == 0


def test_app_log_counts_group_by_signature_level_and_component() -> None:
    aggregator = _ingested().aggregator

    def grouped(dim: str, metric: str) -> dict[str, int]:
        rows = aggregator.snapshot("1m", group_by=(dim,))
        return {label[0]: row.counters[metric] for label, row in rows.items()}

    assert grouped("error_signature", "app_error_signatures") == {
        "gr_connection_disconnected": 2,
        "out_of_memory": 1,
    }
    assert grouped("level", "app_log_lines") == {"I": 1, "W": 1, "F": 1, "E": 2}
    assert grouped("component", "app_log_errors") == {"VS_2": 2, "OMS": 1}


def test_fix_metrics_do_not_appear_for_app_log_lines() -> None:
    counters = _ingested().aggregator.snapshot("1m")[()].counters

    assert "messages_total" not in counters
