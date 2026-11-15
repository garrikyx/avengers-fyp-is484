"""FR-PIP-006 / FR-LOG-004: identity and source order survive rotation/restart."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.logs.offset_tracker import OffsetTracker
from telemetry_agent.parser.protocol import LineClassification, ParseResult
from telemetry_agent.pipeline.committer import PipelineCommitter
from telemetry_agent.pipeline.deduper import ProcessedLineDeduper
from telemetry_agent.pipeline.event_queue import EventQueue
from telemetry_agent.pipeline.monitor_adapter import source_meta_from_read_line
from telemetry_agent.pipeline.types import ParsedEvent


def test_out_of_order_workers_cannot_checkpoint_over_an_unfinished_line(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Fix.log"
    path.write_text("first\nsecond\n")
    monitor = LogMonitor(
        path,
        offset_tracker=OffsetTracker(tmp_path / "offsets.json"),
        commit_on_read=False,
    )
    try:
        lines = list(monitor.poll_lines())
        metas = [source_meta_from_read_line(line, path=str(path)) for line in lines]
        queue = EventQueue()
        committer = PipelineCommitter(
            queue, ProcessedLineDeduper(), {str(path): monitor}
        )
        for meta in metas:
            committer.expect(meta)
        for i, expected in ((1, 0), (0, path.stat().st_size)):
            queue.put(
                ParsedEvent(
                    meta=metas[i],
                    result=ParseResult(classification=LineClassification.UNSUPPORTED),
                    line=b"synthetic",
                )
            )
            committer.process_available()
            assert monitor.get_status().committed_offset == expected
    finally:
        monitor.close()


def test_ingest_failure_does_not_acknowledge_or_dedupe_the_line(tmp_path: Path) -> None:
    path = tmp_path / "Fix.log"
    path.write_text("first\n")
    monitor = LogMonitor(
        path,
        offset_tracker=OffsetTracker(tmp_path / "offsets.json"),
        commit_on_read=False,
    )
    try:
        [line] = list(monitor.poll_lines())
        meta = source_meta_from_read_line(line, path=str(path))
        queue = EventQueue()
        deduper = ProcessedLineDeduper()

        def fail(event: ParsedEvent) -> None:
            raise RuntimeError("synthetic ingestion failure")

        committer = PipelineCommitter(
            queue, deduper, {str(path): monitor}, on_event=fail
        )
        queue.put(
            ParsedEvent(
                meta=meta,
                result=ParseResult(classification=LineClassification.UNSUPPORTED),
                line=b"synthetic",
            )
        )
        with pytest.raises(RuntimeError, match="synthetic"):
            committer.process_available()
        assert monitor.get_status().committed_offset == 0
        assert not deduper.is_duplicate(meta)
    finally:
        monitor.close()


def test_rotation_ack_uses_original_inode_and_lag_cannot_be_negative(
    tmp_path: Path,
) -> None:
    path = tmp_path / "Fix.log"
    path.write_text("old\n")
    tracker = OffsetTracker(tmp_path / "offsets.json")
    monitor = LogMonitor(path, offset_tracker=tracker, commit_on_read=False)
    try:
        [old] = list(monitor.poll_lines())
        path.rename(tmp_path / "Fix.log.1")
        path.write_text("new\n")
        [new] = list(monitor.poll_lines())
        monitor.ack_line(old.end_offset, dev=old.dev, ino=old.inode)
        assert tracker.get_offset(old.dev, old.inode) == old.end_offset
        assert tracker.get_offset(new.dev, new.inode) == 0
        # NFR-REL-007: a captured heartbeat time can precede the concurrent read.
        assert (
            monitor.get_status(now=datetime.now(UTC) - timedelta(seconds=1)).read_lag_ms
            == 0
        )
    finally:
        monitor.close()
