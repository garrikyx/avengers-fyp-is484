"""Integration: block mode prevents drops under backpressure."""

import threading
import time
from datetime import UTC, datetime

from telemetry_agent.parser.protocol import (
    Confidence,
    LineClassification,
    ParseResult,
    SourceMeta,
)
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.supervisor import PipelineBridge


class SlowParser:
    """Artificial CPU-bound parser for backpressure tests."""

    def __init__(self, delay_s: float = 0.05) -> None:
        self._delay_s = delay_s

    def name(self) -> str:
        return "slow"

    def classify(self, line: bytes) -> Confidence:
        if line.startswith(b"SLOW|"):
            return Confidence.HIGH
        return Confidence.NONE

    def parse(self, line: bytes, meta: SourceMeta) -> ParseResult:
        time.sleep(self._delay_s)
        return ParseResult(classification=LineClassification.FIX, framed=True)


def _meta(i: int) -> SourceMeta:
    return SourceMeta(
        instance_id="demo",
        path="/tmp/Fix.log",
        log_type="fix",
        read_at=datetime.now(tz=UTC),
        file_set=f"line-{i}",
        dev=1,
        inode=100,
        byte_offset=i * 10,
        byte_length=10,
    )


def test_block_mode_never_drops_under_backpressure() -> None:
    registry = Registry(parsers={"slow": SlowParser(delay_s=0.05)})
    bridge = PipelineBridge(
        config=PipelineConfig(
            line_queue_size=4,
            event_queue_size=64,
            parse_workers=1,
            overflow_policy="block",
        ),
        registry=registry,
    )
    bridge.start()

    done = threading.Event()
    enqueued = 0

    def flood() -> None:
        nonlocal enqueued
        for i in range(8):
            while not bridge.enqueue_line(
                f"SLOW|{i}\n".encode(),
                _meta(i),
                parser_chain=["slow"],
                timeout=2.0,
            ):
                time.sleep(0.01)
            enqueued += 1
        done.set()

    thread = threading.Thread(target=flood)
    thread.start()
    done.wait(timeout=10.0)
    thread.join(timeout=1.0)

    assert enqueued == 8
    stats = bridge.stats()
    assert stats.lines_dropped == 0

    deadline = time.monotonic() + 8.0
    total_events = 0
    while time.monotonic() < deadline:
        total_events += len(bridge.drain_events())
        if total_events >= 8 and bridge.line_queue.depth == 0:
            break
        time.sleep(0.05)

    bridge.stop()
    assert total_events == 8
