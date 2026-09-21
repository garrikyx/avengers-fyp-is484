import time
from datetime import UTC, datetime

from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import LineClassification, SourceMeta
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.config import PipelineConfig
from telemetry_agent.pipeline.supervisor import PipelineBridge


def _meta(path: str = "/tmp/Fix.log") -> SourceMeta:
    return SourceMeta(
        instance_id="demo",
        path=path,
        log_type="fix",
        read_at=datetime.now(tz=UTC),
    )


def test_parser_workers_drain_line_queue(monkeypatch) -> None:
    monkeypatch.setenv("MAGIC_TELEMETRY_ID_HASH_KEY", "test-key")
    registry = Registry(parsers={"fix": FixParser(hash_key=b"test-key")})

    bridge = PipelineBridge(
        config=PipelineConfig(
            line_queue_size=32,
            event_queue_size=32,
            parse_workers=1,
        ),
        registry=registry,
    )
    bridge.start()
    try:
        fix_line = (
            b"2024-01-01 10:00:00.000 "
            b"8=FIX.4.2|9=000|35=D|49=SESS|56=CL|34=1|52=20240101-10:00:00|"
            b"11=ORD-1|55=IBM|54=1|38=100|40=2|10=000|\n"
        )
        assert bridge.enqueue_line(fix_line, _meta(), parser_chain=["fix"])

        deadline = time.monotonic() + 2.0
        events = []
        while time.monotonic() < deadline and not events:
            events = bridge.drain_events()
            if not events:
                time.sleep(0.01)

        assert len(events) == 1
        assert events[0].result.classification == LineClassification.FIX
        assert events[0].result.framed is True
    finally:
        bridge.stop()


def test_unmatched_chain_emits_unsupported() -> None:
    registry = Registry(parsers={})
    bridge = PipelineBridge(
        config=PipelineConfig(parse_workers=1, line_queue_size=4, event_queue_size=4),
        registry=registry,
    )
    bridge.start()
    try:
        assert bridge.enqueue_line(b"not fix\n", _meta(), parser_chain=["fix"])
        deadline = time.monotonic() + 1.0
        events = []
        while time.monotonic() < deadline and not events:
            events = bridge.drain_events()
            if not events:
                time.sleep(0.01)
        assert len(events) == 1
        assert events[0].result.classification == LineClassification.UNSUPPORTED
    finally:
        bridge.stop()
