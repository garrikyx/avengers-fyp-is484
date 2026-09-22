from datetime import UTC, datetime

from telemetry_agent.parser.protocol import LineClassification, ParseResult, SourceMeta
from telemetry_agent.pipeline.event_queue import EventQueue
from telemetry_agent.pipeline.line_queue import LineQueue
from telemetry_agent.pipeline.types import ParsedEvent, QueuedLine


def _meta() -> SourceMeta:
    return SourceMeta(
        instance_id="demo",
        path="/tmp/Fix.log",
        log_type="fix",
        read_at=datetime.now(tz=UTC),
    )


def test_line_queue_defaults_to_2048_capacity() -> None:
    queue = LineQueue()
    assert queue.capacity == 2048


def test_event_queue_defaults_to_256_capacity() -> None:
    queue = EventQueue()
    assert queue.capacity == 256


def test_line_queue_drop_oldest_when_configured() -> None:
    queue = LineQueue(capacity=1, overflow_policy="drop_oldest")
    queue.put_nowait(
        QueuedLine(line=b"old", meta=_meta(), parser_chain=("fix",))
    )
    queue.put_nowait(
        QueuedLine(line=b"new", meta=_meta(), parser_chain=("fix",))
    )

    assert queue.lines_dropped == 1
    remaining = queue.get(timeout=0.1)
    assert remaining is not None
    assert remaining.line == b"new"


def test_event_queue_drop_oldest_when_configured() -> None:
    queue = EventQueue(capacity=1, overflow_policy="drop_oldest")
    result = ParseResult(classification=LineClassification.FIX)
    queue.put_nowait(ParsedEvent(meta=_meta(), result=result))
    queue.put_nowait(ParsedEvent(meta=_meta(), result=result))

    assert queue.events_dropped == 1
    drained = queue.drain()
    assert len(drained) == 1
