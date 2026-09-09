"""Visual parser demo rendering for stdout (used by cli.py)."""

from __future__ import annotations

import sys
from dataclasses import asdict
from re import Pattern

from telemetry_agent.metrics.demo_sink import DemoMetricsSink
from telemetry_agent.parser.applog.signatures import SignatureMatcher, extract_log_level
from telemetry_agent.parser.fix.classify import classify_line
from telemetry_agent.parser.fix.frame import DelimiterMode, FrameOptions, Framer
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import (
    Confidence,
    LineClassification,
    ParseResult,
)
from telemetry_agent.parser.registry import Registry, registered_names

_FIX_BEGIN = (b"8=FIX", b"8=FIXT")
_FIELD_DELIMITERS = (b"\x01", b"|", b";", b"^A")
_CLASSIFY_WINDOW = 256

_TAG_NAMES: dict[str, str] = {
    "8": "BeginString",
    "9": "BodyLength",
    "10": "CheckSum",
    "11": "ClOrdID",
    "17": "ExecID",
    "34": "MsgSeqNum",
    "35": "MsgType",
    "37": "OrderID",
    "39": "OrdStatus",
    "40": "OrdType",
    "41": "OrigClOrdID",
    "49": "SenderCompID",
    "52": "SendingTime",
    "54": "Side",
    "55": "Symbol",
    "56": "TargetCompID",
    "58": "Text",
    "60": "TransactTime",
    "103": "OrdRejReason",
    "150": "ExecType",
    "38": "OrderQty",
}

_MSG_TYPE_NAMES: dict[str, str] = {
    "0": "Heartbeat",
    "1": "Test Request",
    "2": "Resend Request",
    "3": "Reject",
    "4": "Sequence Reset",
    "5": "Logout",
    "8": "Execution Report",
    "9": "Order Cancel Reject",
    "A": "Logon",
    "D": "New Order Single",
    "F": "Order Cancel Request",
    "G": "Order Cancel/Replace Request",
}


class _Style:
    __slots__ = ("reset", "bold", "dim", "cyan", "green", "yellow", "red", "blue", "magenta")

    def __init__(
        self,
        *,
        reset: str = "",
        bold: str = "",
        dim: str = "",
        cyan: str = "",
        green: str = "",
        yellow: str = "",
        red: str = "",
        blue: str = "",
        magenta: str = "",
    ) -> None:
        self.reset = reset
        self.bold = bold
        self.dim = dim
        self.cyan = cyan
        self.green = green
        self.yellow = yellow
        self.red = red
        self.blue = blue
        self.magenta = magenta


def _use_color(stream: object) -> bool:
    return hasattr(stream, "isatty") and stream.isatty()  # type: ignore[union-attr]


def _style_for(stream: object) -> _Style:
    if not _use_color(stream):
        return _Style()
    return _Style(
        reset="\033[0m",
        bold="\033[1m",
        dim="\033[2m",
        cyan="\033[36m",
        green="\033[32m",
        yellow="\033[33m",
        red="\033[31m",
        blue="\033[34m",
        magenta="\033[35m",
    )


def _visible_bytes(data: bytes, *, style: _Style) -> str:
    out: list[str] = []
    i = 0
    while i < len(data):
        if data[i : i + 1] == b"\x01":
            out.append(f"{style.magenta}[SOH]{style.reset}")
            i += 1
            continue
        if data[i : i + 3] == b"^A":
            out.append(f"{style.magenta}[^A→SOH]{style.reset}")
            i += 3
            continue
        ch = data[i : i + 1]
        if 32 <= ch[0] <= 126:
            out.append(ch.decode("ascii"))
        else:
            out.append(f"{style.dim}\\x{ch[0]:02x}{style.reset}")
        i += 1
    return "".join(out)


def _hr(width: int, char: str = "─") -> str:
    return char * width


def _box_title(title: str, *, width: int, style: _Style) -> str:
    inner = f" {title} "
    pad = max(0, width - len(inner) - 2)
    left = pad // 2
    right = pad - left
    return (
        f"{style.cyan}{style.bold}"
        f"{'═' * (left + 1)}{inner}{'═' * (right + 1)}"
        f"{style.reset}"
    )


def print_demo_header(corpus_dirs: list[str], *, stream: object = sys.stdout) -> None:
    style = _style_for(stream)
    print(
        _box_title("Telemetry Agent — Parser Interactive Demo", width=72, style=style),
        file=stream,
    )
    print(file=stream)
    print(
        "Pipeline: Registry → Classification → Framing → Enrichment → Metrics\n",
        file=stream,
    )
    print(f"Corpora: {', '.join(corpus_dirs)}", file=stream)
    print(_hr(72), file=stream)
    print(file=stream)


def print_demo_summary(
    summary: dict[str, int],
    metrics: DemoMetricsSink,
    *,
    stream: object = sys.stdout,
) -> None:
    style = _style_for(stream)
    print(_box_title("Corpus Summary", width=72, style=style), file=stream)
    print(file=stream)
    print(f"  Total lines parsed:  {summary['lines']}", file=stream)
    print(f"  FIX classified:      {summary['fix']}", file=stream)
    print(f"  App log classified:  {summary['app_log']}", file=stream)
    print(f"  Unsupported:         {summary['unsupported']}", file=stream)
    print(f"  Successfully framed: {summary['framed']}", file=stream)
    print(f"  Frame errors:        {summary['errors']}", file=stream)
    print(file=stream)
    print(metrics.format_block(), file=stream)
    print(file=stream)


def _explain_classification(
    line: bytes,
    *,
    app_log_patterns: list[Pattern[bytes]] | None,
) -> tuple[LineClassification, list[str]]:
    steps: list[str] = []
    window = line[:_CLASSIFY_WINDOW]

    fix_start = -1
    fix_token = b""
    for token in _FIX_BEGIN:
        idx = window.find(token)
        if idx >= 0 and (fix_start < 0 or idx < fix_start):
            fix_start = idx
            fix_token = token

    if fix_start < 0:
        steps.append("✗ No BeginString token (8=FIX or 8=FIXT) in first 256 bytes")
        if app_log_patterns:
            steps.append("→ checking configured app_log patterns (FR-PRS-011)")
            cls = classify_line(line, app_log_patterns=app_log_patterns)
            if cls == LineClassification.APP_LOG:
                steps.append("✓ Matched app_log pattern")
                return LineClassification.APP_LOG, steps
        steps.append("→ classified as unsupported")
        return LineClassification.UNSUPPORTED, steps

    steps.append(f'✓ Found BeginString "{fix_token.decode("ascii")}" at byte offset {fix_start}')

    msg_type_idx = window.find(b"35=", fix_start)
    if msg_type_idx < 0:
        steps.append("✗ No MsgType tag (35=) after BeginString")
        return LineClassification.UNSUPPORTED, steps

    between = window[fix_start:msg_type_idx]
    found_delim = [d for d in _FIELD_DELIMITERS if d in between]
    if not found_delim:
        steps.append("✗ No field delimiter between BeginString and MsgType")
        return LineClassification.UNSUPPORTED, steps

    delim_labels = []
    for d in found_delim:
        if d == b"\x01":
            delim_labels.append("SOH (0x01)")
        elif d == b"|":
            delim_labels.append("|")
        elif d == b";":
            delim_labels.append(";")
        else:
            delim_labels.append("^A")
    steps.append(
        f"✓ Delimiter(s) between BeginString and MsgType: {', '.join(delim_labels)}"
    )
    steps.append(f"✓ MsgType tag (35=) at byte offset {msg_type_idx}")
    steps.append("→ classified as FIX (Confidence.HIGH)")
    return LineClassification.FIX, steps


def _delimiter_label(mode: DelimiterMode) -> str:
    labels = {
        DelimiterMode.SOH: "SOH (0x01)",
        DelimiterMode.PIPE: "pipe (|)",
        DelimiterMode.SEMICOLON: "semicolon (;)",
        DelimiterMode.CARET: "caret (^A → SOH)",
        DelimiterMode.AUTO: "auto",
    }
    return labels.get(mode, mode.value)


def _format_field_row(tag: str, value: str, *, style: _Style) -> str:
    name = _TAG_NAMES.get(tag, "")
    name_col = f"{style.dim}{name:<16}{style.reset}" if name else f"{'':16}"
    extra = ""
    if tag == "35":
        label = _MSG_TYPE_NAMES.get(value, "")
        if label:
            extra = f"  {style.yellow}({label}){style.reset}"
    if tag == "58":
        extra = f"  {style.dim}(stripped from egress — FR-PRS-022){style.reset}"
    highlight = style.bold if tag in {"8", "35", "10"} else ""
    return f"  {highlight}{tag:>3}{style.reset}  {name_col}  {value}{extra}"


def _render_framing(line: bytes, *, style: _Style) -> list[str]:
    lines: list[str] = []
    framer = Framer(FrameOptions())
    result = framer.frame(line)

    prefix_len = 0
    for token in _FIX_BEGIN:
        idx = line.find(token)
        if idx >= 0:
            prefix_len = idx
            break

    lines.append("3a. Locate message boundaries (FR-PRS-013)")
    if prefix_len > 0:
        prefix = line[:prefix_len]
        lines.append(
            f"    Log prefix stripped ({prefix_len} bytes): "
            f"{_visible_bytes(prefix, style=style)}"
        )
    else:
        lines.append("    No log prefix — message starts at beginning of line")

    if not result.ok:
        lines.append(f"    {style.red}✗ Framing failed: {result.error_reason}{style.reset}")
        return lines

    message = result.message
    if message is None:
        lines.append(f"    {style.red}✗ Framing failed: internal_error{style.reset}")
        return lines

    lines.append("")
    lines.append("3b. Delimiter detection (FR-PRS-012)")
    lines.append(f"    Mode: auto → detected {_delimiter_label(message.delimiter)}")

    lines.append("")
    lines.append("3c. Slice to checksum tag 10 (FR-PRS-013)")
    lines.append(f"    Extracted {len(message.raw)} bytes ending at CheckSum field")

    lines.append("")
    lines.append("3d. Tag=value field breakdown")
    lines.append(f"    {style.dim}{'Tag':>3}  {'Name':<16}  Value{style.reset}")

    if message.delimiter == DelimiterMode.PIPE:
        delim_byte = b"|"
    elif message.delimiter == DelimiterMode.SEMICOLON:
        delim_byte = b";"
    else:
        delim_byte = b"\x01"
    split_data = (
        message.raw.replace(b"^A", b"\x01")
        if message.delimiter == DelimiterMode.CARET
        else message.raw
    )
    ordered_tags: list[str] = []
    seen: set[str] = set()
    for part in split_data.split(delim_byte):
        if b"=" not in part:
            continue
        tag_b, _, _ = part.partition(b"=")
        try:
            tag = tag_b.decode("ascii")
        except UnicodeDecodeError:
            continue
        if tag.isdigit() and tag not in seen:
            ordered_tags.append(tag)
            seen.add(tag)

    for tag in ordered_tags:
        if tag == "58":
            lines.append(_format_field_row(tag, "<redacted>", style=style))
        else:
            lines.append(_format_field_row(tag, message.fields[tag], style=style))

    if result.warnings:
        lines.append("")
        warn_text = ", ".join(result.warnings)
        lines.append(f"    {style.yellow}⚠ Warnings: {warn_text}{style.reset}")

    return lines


def _render_enrichment(result: ParseResult, *, style: _Style) -> list[str]:
    lines: list[str] = []
    tel = result.telemetry
    if tel is None:
        lines.append(f"  {style.dim}(no telemetry — framing did not complete){style.reset}")
        return lines

    if tel.normalized_msg_type:
        lines.append(f"  normalized_msg_type     {tel.normalized_msg_type}")
    if tel.normalized_exec_type:
        lines.append(f"  normalized_exec_type    {tel.normalized_exec_type}")
    if tel.normalized_ord_status:
        lines.append(f"  normalized_ord_status   {tel.normalized_ord_status}")
    if tel.reject_reason_label:
        lines.append(
            f"  reject_reason_label     {style.yellow}{tel.reject_reason_label}{style.reset}"
        )
    if tel.effective_reject_reason:
        lines.append(f"  effective_reject_reason {tel.effective_reject_reason}")
    if tel.unclassified_reject_text:
        lines.append(
            f"  {style.yellow}→ unclassified_reject_text counter incremented{style.reset}"
        )
    if tel.unknown_enums:
        lines.append(
            f"  unknown_enums           {', '.join(tel.unknown_enums)} "
            f"{style.dim}(→ unknown_enum_values){style.reset}"
        )
    if tel.event_time_utc:
        lines.append(
            f"  event_time_utc          {tel.event_time_utc.isoformat()} "
            f"({tel.time_source})"
        )
    if tel.bad_timestamp:
        lines.append(f"  {style.yellow}→ bad_timestamp; using log read time{style.reset}")
    if tel.clock_skew:
        lines.append(
            f"  {style.yellow}→ clock_skew_events incremented; using agent clock{style.reset}"
        )
    if tel.seq_gap is not None:
        gap = tel.seq_gap
        if gap.is_regression:
            lines.append(
                f"  seq_regression          session={gap.session_key} "
                f"expected>{gap.actual}"
            )
        else:
            lines.append(
                f"  seq_gap                 session={gap.session_key} "
                f"size={gap.gap_size}"
            )
    if tel.unknown_msg_type:
        lines.append(
            f"  {style.yellow}→ unknown_msg_type warning (message still processed){style.reset}"
        )
    return lines


def _render_applog(
    line: bytes,
    *,
    signature_matcher: SignatureMatcher,
    style: _Style,
) -> list[str]:
    lines: list[str] = []
    level = extract_log_level(line)
    if level is not None:
        lines.append(f"  log_level               [{level}]")
    label = signature_matcher.match(line)
    if label is not None:
        lines.append(
            f"  error_signature         {style.blue}{label}{style.reset} "
            f"{style.dim}(→ app.error_signature counter){style.reset}"
        )
    else:
        lines.append(f"  {style.dim}→ no error signature matched{style.reset}")
    return lines


def _render_metrics_for_line(
    result: ParseResult,
    line: bytes,
    *,
    signature_matcher: SignatureMatcher,
    style: _Style,
) -> list[str]:
    sink = DemoMetricsSink()
    sink.record_parse_result(result)
    if result.classification == LineClassification.APP_LOG:
        label = signature_matcher.match(line)
        if label is not None:
            sink.record_app_signature(label)
    lines: list[str] = []
    for key in sorted(sink.counters):
        if sink.counters[key]:
            lines.append(f"  {key}: {sink.counters[key]}")
    for label in sorted(sink.signature_labels):
        lines.append(f"  app.error_signature{{{label}}}: {sink.signature_labels[label]}")
    if not lines:
        lines.append(f"  {style.dim}(no counters for this line){style.reset}")
    return lines


def _render_output(result: ParseResult, *, style: _Style) -> list[str]:
    lines: list[str] = []
    cls_color = {
        LineClassification.FIX: style.green,
        LineClassification.APP_LOG: style.blue,
        LineClassification.UNSUPPORTED: style.dim,
    }.get(result.classification, "")

    lines.append(
        f"  classification  {cls_color}{result.classification.value}{style.reset}"
    )
    lines.append(
        f"  framed          {style.green if result.framed else style.dim}"
        f"{result.framed}{style.reset}"
    )

    if result.msg_type:
        label = _MSG_TYPE_NAMES.get(result.msg_type, "")
        suffix = f"  ({label})" if label else ""
        lines.append(f"  msgType (35)    {result.msg_type}{suffix}")
    if result.delimiter:
        lines.append(f"  delimiter       {result.delimiter}")
    if result.joined_lines > 1:
        lines.append(f"  joined_lines    {result.joined_lines}")
    if result.warnings:
        lines.append(f"  warnings        {', '.join(result.warnings)}")
    if result.error is not None:
        lines.append(f"  error           {style.red}{result.error.reason}{style.reset}")
        if result.error.detail:
            lines.append(f"  error_detail    {result.error.detail}")

    if result.fields is not None:
        safe = {k: v for k, v in asdict(result.fields).items() if v is not None}
        if safe:
            rendered = ", ".join(f"{k}={v}" for k, v in safe.items())
            lines.append(f"  allowlisted     {rendered}")

    return lines


def render_demo_line(
    *,
    filename: str,
    line_no: int,
    total_lines: int,
    line: bytes,
    result: ParseResult,
    joiner_continuation: bool,
    registry: Registry,
    parser_chain: list[str],
    fix_parser: FixParser,
    signature_matcher: SignatureMatcher,
    stream: object = sys.stdout,
) -> None:
    """Print one annotated demo block for a corpus line."""
    style = _style_for(stream)
    width = 72

    print(
        _box_title(
            f"Parser Demo · {filename} · line {line_no}/{total_lines}",
            width=width,
            style=style,
        ),
        file=stream,
    )
    print(file=stream)

    print(f"{style.bold}▶ INPUT{style.reset}  (raw log line as read from disk)", file=stream)
    print(f"  {_visible_bytes(line, style=style)}", file=stream)
    print(file=stream)

    print(
        f"{style.bold}▶ STEP 1 — Registry{style.reset}  (FR-PRS-030 / FR-PRS-031)",
        file=stream,
    )
    print(f"  Registered parsers: {sorted(registered_names())}", file=stream)
    print(f"  Configured chain:   {parser_chain}", file=stream)
    for name in parser_chain:
        parser = fix_parser if name == "fix" else None
        if parser is None:
            print(f"  {name}: not loaded in this demo", file=stream)
            continue
        confidence = parser.classify(line)
        if joiner_continuation and name == "fix":
            print(
                f"  {name}.classify() → Confidence.{confidence.name}  "
                f"{style.yellow}(joiner continuation){style.reset}",
                file=stream,
            )
            continue
        marker = (
            f"{style.green}✓ selected{style.reset}"
            if confidence == Confidence.HIGH
            else "— skipped"
        )
        print(f"  {name}.classify() → Confidence.{confidence.name}  {marker}", file=stream)
    print(file=stream)

    print(
        f"{style.bold}▶ STEP 2 — Classification{style.reset}  (FR-PRS-010 / FR-PRS-011)",
        file=stream,
    )
    if joiner_continuation:
        print("  Continuation line — joiner holds a partial FIX message", file=stream)
        print("  → fed directly to joiner (FR-PRS-014)", file=stream)
    else:
        print("  Order: fix → app_log → unsupported (first 256 bytes)", file=stream)
        _, cls_steps = _explain_classification(
            line,
            app_log_patterns=fix_parser._app_log_patterns,
        )
        for step in cls_steps:
            print(f"  {step}", file=stream)
    print(file=stream)

    if result.classification == LineClassification.FIX:
        print(
            f"{style.bold}▶ STEP 3 — Framing{style.reset}  (FR-PRS-012 – FR-PRS-014)",
            file=stream,
        )
        if result.joined_lines > 1:
            print(
                f"  {style.yellow}Multi-line message: {result.joined_lines} lines joined"
                f"{style.reset}",
                file=stream,
            )
            print(file=stream)
        for framing_line in _render_framing(line, style=style):
            print(framing_line, file=stream)
        print(file=stream)

        print(
            f"{style.bold}▶ STEP 4 — Enrichment{style.reset}  (UBS-45/46: FR-PRS-022–027)",
            file=stream,
        )
        for enrich_line in _render_enrichment(result, style=style):
            print(enrich_line, file=stream)
        print(file=stream)
    elif result.classification == LineClassification.APP_LOG:
        print(
            f"{style.bold}▶ STEP 3 — Framing{style.reset}  {style.dim}(skipped — app_log)"
            f"{style.reset}",
            file=stream,
        )
        print(file=stream)
        print(
            f"{style.bold}▶ STEP 4 — Applog signatures{style.reset}  (FR-RUL-001 demo)",
            file=stream,
        )
        for sig_line in _render_applog(line, signature_matcher=signature_matcher, style=style):
            print(sig_line, file=stream)
        print(file=stream)
    else:
        print(
            f"{style.bold}▶ STEP 3 — Framing{style.reset}  {style.dim}(skipped — unsupported)"
            f"{style.reset}",
            file=stream,
        )
        print(file=stream)

    print(
        f"{style.bold}▶ STEP 5 — Metrics{style.reset}  (counters for this line)",
        file=stream,
    )
    for metric_line in _render_metrics_for_line(
        result,
        line,
        signature_matcher=signature_matcher,
        style=style,
    ):
        print(metric_line, file=stream)
    print(file=stream)

    print(
        f"{style.bold}▶ OUTPUT{style.reset}  (ParseResult emitted to pipeline)",
        file=stream,
    )
    for out_line in _render_output(result, style=style):
        print(out_line, file=stream)

    print(_hr(width), file=stream)
    print(file=stream)
