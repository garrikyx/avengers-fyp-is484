from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from telemetry_agent.parser.demo import run_corpus_demo
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import SourceMeta, ParseResult


def main() -> None:
    parser = argparse.ArgumentParser(description="Telemetry FIX parser CLI.")
    parser.add_argument(
        "--corpus",
        type=Path,
        help="Directory of synthetic FIX log files — runs the visual parser demo.",
    )
    args = parser.parse_args()

    if args.corpus is None:
        _run_stdin()
        return

    corpus_dir = args.corpus.resolve()
    if not corpus_dir.is_dir():
        msg = f"corpus path is not a directory: {corpus_dir}"
        raise SystemExit(msg)

    run_corpus_demo(corpus_dir)


def _run_stdin() -> None:
    fix_parser = FixParser()
    for raw in sys.stdin.buffer:
        line = raw.rstrip(b"\n\r")
        if not line:
            continue
        result = _parse_line(fix_parser, line)
        print(json.dumps(_safe_result_dict(result)))


def _parse_line(fix_parser: FixParser, line: bytes) -> ParseResult:
    meta = SourceMeta(
        instance_id="demo",
        path="stdin",
        log_type="fix",
        read_at=datetime.now(tz=UTC),
    )
    return fix_parser.parse(line, meta)


def _safe_result_dict(result: ParseResult) -> dict[str, object]:
    """Emit metadata only — no raw FIX field values beyond msgType."""
    payload: dict[str, object] = {
        "classification": result.classification.value,
        "framed": result.framed,
    }
    if result.msg_type:
        payload["msgType"] = result.msg_type
    if result.delimiter:
        payload["delimiter"] = result.delimiter
    if result.warnings:
        payload["warnings"] = result.warnings
    if result.error is not None:
        payload["error"] = result.error.reason
    if result.joined_lines > 1:
        payload["joined_lines"] = result.joined_lines
    return payload


if __name__ == "__main__":
    main()
