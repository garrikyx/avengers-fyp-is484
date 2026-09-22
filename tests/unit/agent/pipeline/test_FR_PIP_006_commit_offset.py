from pathlib import Path

from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_agent.metrics.demo_sink import DemoMetricsSink
from telemetry_agent.parser.protocol import LineClassification, ParseResult, SourceMeta
from telemetry_agent.pipeline.committer import PipelineCommitter
from telemetry_agent.pipeline.deduper import ProcessedLineDeduper
from telemetry_agent.pipeline.event_queue import EventQueue
from telemetry_agent.pipeline.types import ParsedEvent


def test_committed_offset_advances_only_after_committer_ingest(tmp_path: Path) -> None:
    log_path = tmp_path / "Fix.log"
    log_path.write_text("line-1\nline-2\n")
    tracker = OffsetTracker(registry_path=tmp_path / "offsets.json")
    monitor = LogMonitor(log_path, offset_tracker=tracker, commit_on_read=False)

    read_lines = list(monitor.poll_lines())
    status_after_read = monitor.get_status()
    assert status_after_read.offset == len("line-1\nline-2\n")
    assert status_after_read.committed_offset == 0

    event_queue = EventQueue(capacity=8)
    committer = PipelineCommitter(
        event_queue=event_queue,
        deduper=ProcessedLineDeduper(capacity=100),
        monitors_by_path={str(log_path.resolve()): monitor},
        sink=DemoMetricsSink(),
    )

    first = read_lines[0]
    meta = SourceMeta(
        instance_id="demo",
        path=str(log_path.resolve()),
        log_type="fix",
        read_at=status_after_read.last_read_at,  # type: ignore[arg-type]
        dev=first.dev,
        inode=first.inode,
        byte_offset=first.byte_offset,
        byte_length=first.byte_length,
    )
    event_queue.put(
        ParsedEvent(
            meta=meta,
            result=ParseResult(classification=LineClassification.UNSUPPORTED),
            line=b"line-1",
        )
    )
    committer.process_available()

    partial = monitor.get_status()
    assert partial.committed_offset == first.end_offset
    assert partial.offset == len("line-1\nline-2\n")

    monitor.close()
    tracker2 = OffsetTracker(registry_path=tmp_path / "offsets.json")
    monitor2 = LogMonitor(log_path, offset_tracker=tracker2)
    restarted = monitor2.get_status()
    assert restarted.committed_offset == first.end_offset
    monitor2.close()
