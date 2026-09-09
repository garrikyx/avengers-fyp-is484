from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from telemetry_agent.metrics.demo_sink import DemoMetricsSink
from telemetry_agent.parser.applog.signatures import (
    SignatureMatcher,
    compile_signature_rules,
    extract_log_level,
)
from telemetry_agent.parser.config import DemoConfig, load_demo_config
from telemetry_agent.parser.corpus import prepare_corpus_line
from telemetry_agent.parser.display import (
    print_demo_header,
    print_demo_summary,
    render_demo_line,
)
from telemetry_agent.parser.fix.identifiers import load_hash_key
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import LineClassification, ParseResult, SourceMeta
from telemetry_agent.parser.registry import Registry, registered_names

def _corpus_files(corpus_path: Path) -> list[Path]:
    if corpus_path.is_file():
        return [corpus_path]
    return sorted(
        p
        for p in corpus_path.iterdir()
        if p.is_file() and p.suffix not in {".yaml", ".yml"}
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run parser over log corpora with visual demo output.",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        action="append",
        help="Directory of log files to parse (repeatable).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="YAML config for applog patterns, reject patterns, and error signatures.",
    )
    parser.add_argument(
        "--line",
        type=int,
        help="Demo only this line number within each file (1-based).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="One-line summary per log line instead of visual demo blocks.",
    )
    parser.add_argument(
        "--metrics-json",
        type=Path,
        help="Write collected demo metrics counters to JSON.",
    )
    args = parser.parse_args()

    try:
        hash_key = load_hash_key()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    config = _load_config(args.config)
    fix_parser = FixParser(
        hash_key=hash_key,
        app_log_patterns=config.app_log_patterns or None,
        reject_reason_patterns=config.reject_reason_patterns or None,
        max_reject_reason_labels=config.max_reject_reason_labels,
        max_clock_skew=config.max_clock_skew,
    )
    signature_matcher = SignatureMatcher(
        compile_signature_rules(config.error_signatures),
        max_dynamic_labels=config.max_dynamic_signature_labels,
    )
    metrics = DemoMetricsSink()
    registry = Registry()
    chain = ["fix"]
    unknown = registry.validate_chain(chain)
    if unknown:
        msg = f"unknown parsers in chain: {unknown}; registered={sorted(registered_names())}"
        raise SystemExit(msg)

    if not args.corpus:
        _run_stdin(fix_parser, signature_matcher, metrics, quiet=args.quiet)
        return

    resolved = [p.resolve() for p in args.corpus]
    for corpus_path in resolved:
        if not corpus_path.is_file() and not corpus_path.is_dir():
            msg = f"corpus path not found: {corpus_path}"
            raise SystemExit(msg)

    if not args.quiet:
        print_demo_header([str(p) for p in resolved])

    summary = {
        "lines": 0,
        "fix": 0,
        "app_log": 0,
        "unsupported": 0,
        "framed": 0,
        "errors": 0,
    }

    for corpus_path in resolved:
        for path in _corpus_files(corpus_path):
            _run_corpus_file(
                path,
                fix_parser,
                signature_matcher,
                metrics,
                summary,
                registry=registry,
                parser_chain=chain,
                line_filter=args.line,
                quiet=args.quiet,
            )

    if args.quiet:
        print(
            "SUMMARY: "
            f"{summary['lines']} lines | "
            f"fix={summary['fix']} app_log={summary['app_log']} "
            f"unsupported={summary['unsupported']} framed={summary['framed']} "
            f"errors={summary['errors']}"
        )
        print(metrics.format_block())
    else:
        print_demo_summary(summary, metrics)

    if args.metrics_json is not None:
        payload = {
            "counters": dict(metrics.counters),
            "signature_labels": dict(metrics.signature_labels),
        }
        args.metrics_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_config(path: Path | None) -> DemoConfig:
    if path is None:
        return DemoConfig(
            app_log_patterns=[],
            reject_reason_patterns=[],
            error_signatures=[],
        )
    return load_demo_config(path.resolve())


def _run_corpus_file(
    path: Path,
    fix_parser: FixParser,
    signature_matcher: SignatureMatcher,
    metrics: DemoMetricsSink,
    summary: dict[str, int],
    *,
    registry: Registry,
    parser_chain: list[str],
    line_filter: int | None,
    quiet: bool,
) -> None:
    raw_lines = path.read_bytes().splitlines()
    non_empty = [ln for ln in raw_lines if ln.strip()]
    for idx, raw in enumerate(non_empty, start=1):
        if line_filter is not None and idx != line_filter:
            continue

        line, source_label = prepare_corpus_line(raw)
        display_name = source_label or path.name

        joiner_continuation = fix_parser._joiner.has_pending
        result = _parse_line(fix_parser, line, display_name)
        _record_metrics(result, line, signature_matcher, metrics)
        _update_summary(summary, result)

        if quiet:
            print(_format_line_result(display_name, result, line, signature_matcher))
        else:
            render_demo_line(
                filename=display_name,
                line_no=idx,
                total_lines=len(non_empty),
                line=line,
                result=result,
                joiner_continuation=joiner_continuation,
                registry=registry,
                parser_chain=parser_chain,
                fix_parser=fix_parser,
                signature_matcher=signature_matcher,
            )


def _run_stdin(
    fix_parser: FixParser,
    signature_matcher: SignatureMatcher,
    metrics: DemoMetricsSink,
    *,
    quiet: bool,
) -> None:
    for raw in sys.stdin.buffer:
        line, _ = prepare_corpus_line(raw.rstrip(b"\n\r"))
        if not line:
            continue
        result = _parse_line(fix_parser, line, "stdin")
        _record_metrics(result, line, signature_matcher, metrics)
        if quiet:
            print(json.dumps(_safe_result_dict(result, line, signature_matcher)))
        else:
            render_demo_line(
                filename="stdin",
                line_no=1,
                total_lines=1,
                line=line,
                result=result,
                joiner_continuation=False,
                registry=Registry(),
                parser_chain=["fix"],
                fix_parser=fix_parser,
                signature_matcher=signature_matcher,
            )
    print(metrics.format_block())


def _parse_line(fix_parser: FixParser, line: bytes, source: str) -> ParseResult:
    meta = SourceMeta(
        instance_id="demo",
        path=source,
        log_type="fix",
        read_at=datetime.now(tz=UTC),
    )
    return fix_parser.parse(line, meta)


def _record_metrics(
    result: ParseResult,
    line: bytes,
    signature_matcher: SignatureMatcher,
    metrics: DemoMetricsSink,
) -> None:
    metrics.record_parse_result(result)
    if result.classification == LineClassification.APP_LOG:
        label = signature_matcher.match(line)
        if label is not None:
            metrics.record_app_signature(label)


def _format_line_result(
    filename: str,
    result: ParseResult,
    line: bytes,
    signature_matcher: SignatureMatcher,
) -> str:
    parts = [f"{filename}:", f"classification={result.classification.value}"]
    if result.classification == LineClassification.APP_LOG:
        level = extract_log_level(line)
        if level is not None:
            parts.append(f"level={level}")
        label = signature_matcher.match(line)
        if label is not None:
            parts.append(f"signature={label}")
    elif result.framed:
        parts.append("framed=true")
        parts.append(f"msgType={result.msg_type}")
        tel = result.telemetry
        if tel is not None:
            if tel.normalized_msg_type:
                parts.append(f"normalizedMsgType={tel.normalized_msg_type}")
            if tel.effective_reject_reason:
                parts.append(f"rejectReason={tel.effective_reject_reason}")
            if tel.reject_reason_label:
                parts.append(f"rejectLabel={tel.reject_reason_label}")
            if tel.seq_gap is not None:
                gap = tel.seq_gap
                kind = "regression" if gap.is_regression else "gap"
                parts.append(f"seq_{kind}={gap.gap_size or gap.actual}")
            if tel.clock_skew:
                parts.append("clockSkew=true")
        fields = _fields_dict(result)
        if fields:
            rendered = ",".join(f"{k}={v}" for k, v in fields.items())
            parts.append(f"fields={{{rendered}}}")
        if result.joined_lines > 1:
            parts.append(f"(joined {result.joined_lines} lines)")
    elif result.error is not None:
        parts.append(f"error={result.error.reason}")
    return " ".join(parts)


def _fields_dict(result: ParseResult) -> dict[str, str]:
    if result.fields is None:
        return {}
    return {k: v for k, v in asdict(result.fields).items() if v is not None}


def _update_summary(summary: dict[str, int], result: ParseResult) -> None:
    summary["lines"] += 1
    if result.classification == LineClassification.FIX:
        summary["fix"] += 1
    elif result.classification == LineClassification.APP_LOG:
        summary["app_log"] += 1
    else:
        summary["unsupported"] += 1
    if result.framed:
        summary["framed"] += 1
    if result.error is not None:
        summary["errors"] += 1


def _safe_result_dict(
    result: ParseResult,
    line: bytes,
    signature_matcher: SignatureMatcher,
) -> dict[str, object]:
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
    fields = _fields_dict(result)
    if fields:
        payload["fields"] = fields
    if result.telemetry is not None:
        tel = result.telemetry
        payload["telemetry"] = {
            "normalizedMsgType": tel.normalized_msg_type,
            "effectiveRejectReason": tel.effective_reject_reason,
            "rejectReasonLabel": tel.reject_reason_label,
            "unknownEnums": list(tel.unknown_enums),
            "clockSkew": tel.clock_skew,
            "badTimestamp": tel.bad_timestamp,
        }
    if result.classification == LineClassification.APP_LOG:
        label = signature_matcher.match(line)
        if label is not None:
            payload["signature"] = label
    return payload


if __name__ == "__main__":
    main()
