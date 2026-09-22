"""End-to-end demo: LogMonitor → queue → parse → output → commit."""

from __future__ import annotations

import argparse
import shutil
import tempfile
import time
from pathlib import Path

from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor
from telemetry_agent.metrics.demo_sink import DemoMetricsSink
from telemetry_agent.parser.applog.parser import AppLogParser
from telemetry_agent.parser.applog.signatures import (
    SignatureMatcher,
    compile_signature_rules,
)
from telemetry_agent.parser.config import DemoConfig, load_demo_config
from telemetry_agent.parser.display import print_demo_header, render_demo_line
from telemetry_agent.logs.log_monitor import LogMonitor
from telemetry_agent.parser.fix.identifiers import load_hash_key
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import Confidence, ParseResult, SourceMeta
from telemetry_agent.parser.registry import Registry
from telemetry_agent.pipeline.config import OverflowPolicy, PipelineConfig
from telemetry_agent.pipeline.monitor_adapter import MonitorPipelineAdapter
from telemetry_agent.pipeline.supervisor import PipelineBridge


def _load_config(path: Path | None) -> DemoConfig:
    if path is None:
        return DemoConfig(
            app_log_patterns=[],
            reject_reason_patterns=[],
            error_signatures=[],
        )
    return load_demo_config(path.resolve())


def _print_stage(message: str) -> None:
    print(message, flush=True)


def _build_bridge(
    registry: Registry,
    monitors_by_path: dict[str, LogMonitor],
    *,
    overflow_policy: OverflowPolicy = "block",
) -> PipelineBridge:
    bridge = PipelineBridge(
        config=PipelineConfig(
            line_queue_size=8,
            event_queue_size=8,
            parse_workers=1,
            overflow_policy=overflow_policy,
        ),
        registry=registry,
    )
    sink = DemoMetricsSink()
    bridge.attach_committer(monitors_by_path, sink=sink)
    return bridge


def _build_registry(
    config: DemoConfig, hash_key: bytes
) -> tuple[Registry, list[str], FixParser]:
    """Hands back the `FixParser` alongside the registry it went into.

    Callers need the concrete instance, not `registry.parser("fix")`: that
    returns `Parser | None`, and a second `FixParser(...)` would carry its own
    `SeqTracker`, so it would report a different sequence view than the one
    that actually parsed the line.
    """
    fix_parser = FixParser(hash_key=hash_key)
    parsers: dict[str, FixParser | AppLogParser] = {"fix": fix_parser}
    chain = ["fix"]
    if config.app_log_patterns:
        parsers["applog"] = AppLogParser(
            app_log_patterns=config.app_log_patterns,
            error_signatures=config.error_signatures,
            max_dynamic_signature_labels=config.max_dynamic_signature_labels,
        )
        chain = ["fix", "applog"]
    return Registry(parsers=parsers), chain, fix_parser


def run_happy_path(corpus: Path, config: DemoConfig) -> None:
    print("\n=== Scenario 1: Monitor → Queue → Parse → Output → Commit ===\n")
    hash_key = load_hash_key()
    registry, parser_chain, fix_parser = _build_registry(config, hash_key)
    signature_matcher = SignatureMatcher(
        compile_signature_rules(config.error_signatures),
        max_dynamic_labels=config.max_dynamic_signature_labels,
    )

    with tempfile.TemporaryDirectory() as tmp:
        log_dir = Path(tmp)
        fix_log = log_dir / "Fix.log"
        shutil.copy(corpus, fix_log)
        registry_path = log_dir / "offsets.json"

        monitor = MultiLogMonitor(
            [fix_log],
            registry_path=registry_path,
            commit_on_read=False,
        )
        path_map = {str(fix_log.resolve()): monitor.monitors["Fix.log"]}
        bridge = _build_bridge(registry, path_map)
        bridge.start()
        try:
            adapter = MonitorPipelineAdapter(
                monitor,
                bridge,
                parser_chain=parser_chain,
                on_stage=_print_stage,
            )
            line_no = 0
            for event in adapter.run_until(max_lines=5, idle_rounds=2):
                line_no += 1
                _print_stage(
                    f"[PARSE] classification={event.result.classification.value} "
                    f"framed={event.result.framed}"
                )
                render_demo_line(
                    filename="Fix.log",
                    line_no=line_no,
                    total_lines=5,
                    line=event.line,
                    result=event.result,
                    joiner_continuation=False,
                    registry=registry,
                    parser_chain=parser_chain,
                    fix_parser=fix_parser,
                    signature_matcher=signature_matcher,
                )
                status = monitor.monitors["Fix.log"].get_status()
                _print_stage(
                    f"[COMMIT] read_offset={status.offset} "
                    f"committed_offset={status.committed_offset}"
                )
            stats = bridge.stats()
            _print_stage(
                f"[STATS] lines_dropped={stats.lines_dropped} "
                f"events_dropped={stats.events_dropped}"
            )
            assert stats.lines_dropped == 0
            assert stats.events_dropped == 0
        finally:
            bridge.stop()
            monitor.close()


def run_slow_parser_backpressure(corpus: Path, config: DemoConfig) -> None:
    print("\n=== Scenario 2: Slow parser — blocking backpressure, zero drops ===\n")
    hash_key = load_hash_key()
    registry, parser_chain, fix_parser = _build_registry(config, hash_key)

    class SlowFixParser:
        def name(self) -> str:
            return "fix"

        def classify(self, line: bytes) -> Confidence:
            return fix_parser.classify(line)

        def parse(self, line: bytes, meta: SourceMeta) -> ParseResult:
            time.sleep(0.05)
            return fix_parser.parse(line, meta)

    slow_parsers: dict[str, SlowFixParser | AppLogParser] = {"fix": SlowFixParser()}
    applog_parser = registry.parser("applog")
    if applog_parser is not None:
        slow_parsers["applog"] = applog_parser  # type: ignore[assignment]
    slow_registry = Registry(parsers=slow_parsers)

    with tempfile.TemporaryDirectory() as tmp:
        log_dir = Path(tmp)
        fix_log = log_dir / "Fix.log"
        shutil.copy(corpus, fix_log)
        registry_path = log_dir / "offsets.json"

        monitor = MultiLogMonitor(
            [fix_log],
            registry_path=registry_path,
            commit_on_read=False,
        )
        path_map = {str(fix_log.resolve()): monitor.monitors["Fix.log"]}
        bridge = _build_bridge(slow_registry, path_map)
        bridge.start()
        try:
            adapter = MonitorPipelineAdapter(
                monitor,
                bridge,
                parser_chain=parser_chain,
                on_stage=_print_stage,
            )
            events = list(adapter.run_until(max_lines=3, idle_rounds=3))
            stats = bridge.stats()
            _print_stage(f"[STATS] processed={len(events)} drops={stats.lines_dropped}")
            assert stats.lines_dropped == 0
        finally:
            bridge.stop()
            monitor.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline demo: log monitor through parse to output.",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("apps/agent/testdata/fix/demo_logs.txt"),
        help="FIX corpus copied into a temp log file for tailing.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional YAML config (same as parser demo).",
    )
    parser.add_argument(
        "--scenario",
        choices=["all", "happy", "backpressure"],
        default="all",
    )
    args = parser.parse_args()
    config = _load_config(args.config)

    print_demo_header([str(args.corpus.resolve())])

    if args.scenario in {"all", "happy"}:
        run_happy_path(args.corpus.resolve(), config)
    if args.scenario in {"all", "backpressure"}:
        run_slow_parser_backpressure(args.corpus.resolve(), config)

    print("\n=== Pipeline demo complete ===\n")


if __name__ == "__main__":
    main()
