from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import LineClassification, SourceMeta, ParseResult
from telemetry_agent.parser.registry import Registry, registered_names


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FIX parser over a log corpus.")
    parser.add_argument(
        "--corpus",
        type=Path,
        help="Directory of synthetic FIX log files to parse.",
    )
    args = parser.parse_args()

    if args.corpus is None:
        _run_stdin()
        return

    corpus_dir = args.corpus.resolve()
    if not corpus_dir.is_dir():
        msg = f"corpus path is not a directory: {corpus_dir}"
        raise SystemExit(msg)

    registry = Registry()
    chain = ["fix"]
    unknown = registry.validate_chain(chain)
    if unknown:
        msg = f"unknown parsers in chain: {unknown}; registered={sorted(registered_names())}"
        raise SystemExit(msg)

    fix_parser = FixParser()
    summary = {
        "lines": 0,
        "fix": 0,
        "app_log": 0,
        "unsupported": 0,
        "framed": 0,
        "frame_errors": 0,
    }

    for path in sorted(corpus_dir.iterdir()):
        if not path.is_file():
            continue
        lines = path.read_bytes().splitlines()
        for line in lines:
            if not line.strip():
                continue
            result = _parse_line(fix_parser, line)
            summary["lines"] += 1
            _update_summary(summary, result)
            print(_format_line_result(path.name, result))

    print(
        "SUMMARY: "
        f"{summary['lines']} lines | "
        f"fix={summary['fix']} app_log={summary['app_log']} "
        f"unsupported={summary['unsupported']} framed={summary['framed']} "
        f"errors={summary['frame_errors']}"
    )


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
        path="corpus",
        log_type="fix",
        read_at=datetime.now(tz=UTC),
    )
    return fix_parser.parse(line, meta)


def _format_line_result(filename: str, result: ParseResult) -> str:
    parts = [f"{filename}:", f"classification={result.classification.value}"]
    if result.framed:
        parts.append("framed=true")
        parts.append(f"msgType={result.msg_type}")
        if result.joined_lines > 1:
            parts.append(f"(joined {result.joined_lines} lines)")
    elif result.error is not None:
        parts.append(f"error={result.error.reason}")
    return " ".join(parts)


def _update_summary(summary: dict[str, int], result: ParseResult) -> None:
    if result.classification == LineClassification.FIX:
        summary["fix"] += 1
    elif result.classification == LineClassification.APP_LOG:
        summary["app_log"] += 1
    else:
        summary["unsupported"] += 1
    if result.framed:
        summary["framed"] += 1
    if result.error is not None:
        summary["frame_errors"] += 1


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
