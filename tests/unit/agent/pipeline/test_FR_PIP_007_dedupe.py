from datetime import UTC, datetime

from telemetry_agent.metrics.demo_sink import DemoMetricsSink
from telemetry_agent.parser.protocol import LineClassification, ParseResult, SourceMeta
from telemetry_agent.pipeline.committer import PipelineCommitter
from telemetry_agent.pipeline.deduper import ProcessedLineDeduper
from telemetry_agent.pipeline.event_queue import EventQueue
from telemetry_agent.pipeline.types import ParsedEvent


def _meta(byte_offset: int = 0) -> SourceMeta:
    return SourceMeta(
        instance_id="demo",
        path="/tmp/Fix.log",
        log_type="fix",
        read_at=datetime.now(tz=UTC),
        dev=1,
        inode=42,
        byte_offset=byte_offset,
        byte_length=12,
    )


def test_duplicate_line_position_does_not_double_count() -> None:
    sink = DemoMetricsSink()
    deduper = ProcessedLineDeduper(capacity=100)
    event_queue = EventQueue(capacity=8)
    committer = PipelineCommitter(
        event_queue=event_queue,
        deduper=deduper,
        monitors_by_path={},
        sink=sink,
    )
    result = ParseResult(classification=LineClassification.FIX, framed=True)
    event = ParsedEvent(meta=_meta(), result=result, line=b"8=FIX")

    event_queue.put(event)
    committer.process_available()
    first_count = sink.counters.get("log_lines_read", 0)

    event_queue.put(event)
    committer.process_available()
    second_count = sink.counters.get("log_lines_read", 0)

    assert first_count == 1
    assert second_count == 1
    assert committer.skipped_duplicates == 1
