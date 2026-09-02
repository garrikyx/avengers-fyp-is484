"""Visual FIX parser demo — shows input, pipeline steps, and output."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from telemetry_agent.parser.fix.classify import classify_line
from telemetry_agent.parser.fix.frame import DelimiterMode, FrameOptions, Framer
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import (
    Confidence,
    LineClassification,
    ParseResult,
    SourceMeta,
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
    "60": "TransactTime",
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


@dataclass(frozen=True, slots=True)
class _Style:
    reset: str = ""
    bold: str = ""
    dim: str = ""
    cyan: str = ""
    green: str = ""
    yellow: str = ""
    red: str = ""
    blue: str = ""
    magenta: str = ""


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
    """Render log bytes with delimiters and non-printables made visible."""
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


def _explain_classification(line: bytes) -> tuple[LineClassification, list[str]]:
    """Return classification and human-readable decision trace."""
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
        steps.append("→ skip FIX; no app_log patterns configured")
        return LineClassification.UNSUPPORTED, steps

    steps.append(f'✓ Found BeginString "{fix_token.decode("ascii")}" at byte offset {fix_start}')

    msg_type_idx = window.find(b"35=", fix_start)
    if msg_type_idx < 0:
        steps.append("✗ No MsgType tag (35=) after BeginString")
        steps.append("→ not classified as FIX")
        return LineClassification.UNSUPPORTED, steps

    between = window[fix_start:msg_type_idx]
    found_delim = [d for d in _FIELD_DELIMITERS if d in between]
    if not found_delim:
        steps.append("✗ No field delimiter between BeginString and MsgType")
        steps.append("  (requires SOH, |, ;, or ^A between 8= and 35=)")
        steps.append("→ not classified as FIX")
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
    steps.append(f"✓ Delimiter(s) between BeginString and MsgType: {', '.join(delim_labels)}")
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
    highlight = style.bold if tag in {"8", "35", "10"} else ""
    return f"  {highlight}{tag:>3}{style.reset}  {name_col}  {value}{extra}"


def _render_framing(line: bytes, *, style: _Style) -> list[str]:
    """Explain framing steps for a FIX-classified line."""
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
    lines.append(f"    Parsing begins at BeginString (offset {prefix_len})")

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
    lines.append(f"    {style.dim}{'───':>3}  {'─' * 16}  {'─' * 20}{style.reset}")

    ordered_tags: list[str] = []
    seen: set[str] = set()
    if message.delimiter == DelimiterMode.PIPE:
        delim_byte = b"|"
    elif message.delimiter == DelimiterMode.SEMICOLON:
        delim_byte = b";"
    else:
        delim_byte = b"\x01"
    split_data = message.raw.replace(b"^A", b"\x01") if message.delimiter == DelimiterMode.CARET else message.raw
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
        lines.append(_format_field_row(tag, message.fields[tag], style=style))

    if result.warnings:
        lines.append("")
        warn_text = ", ".join(result.warnings)
        lines.append(f"    {style.yellow}⚠ Warnings: {warn_text}{style.reset}")

    return lines


def _render_output(result: ParseResult, *, style: _Style) -> list[str]:
    lines: list[str] = []
    cls_color = {
        LineClassification.FIX: style.green,
        LineClassification.APP_LOG: style.blue,
        LineClassification.UNSUPPORTED: style.dim,
    }.get(result.classification, "")

    lines.append(f"  classification  {cls_color}{result.classification.value}{style.reset}")
    lines.append(f"  framed          {style.green if result.framed else style.dim}{result.framed}{style.reset}")

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

    if result.classification == LineClassification.UNSUPPORTED:
        lines.append(
            f"  {style.dim}→ line counted in parser.unsupported_lines; no further parsing{style.reset}"
        )
    elif result.classification == LineClassification.FIX and not result.framed and result.error is None:
        lines.append(
            f"  {style.yellow}→ joiner buffering — waiting for tag 10= on a continuation line{style.reset}"
        )
    elif result.framed:
        lines.append(f"  {style.green}→ ready for field extraction (UBS-43+){style.reset}")

    return lines


def render_demo_line(
    *,
    filename: str,
    line_no: int,
    total_lines: int,
    line: bytes,
    framing_bytes: bytes,
    result: ParseResult,
    joiner_continuation: bool,
    registry: Registry,
    parser_chain: list[str],
    fix_parser: FixParser,
    stream: object = sys.stdout,
) -> None:
    """Print one annotated demo block for a corpus line."""
    style = _style_for(stream)
    width = 72

    print(_box_title(f"FIX Parser Demo · {filename} · line {line_no}/{total_lines}", width=width, style=style), file=stream)
    print(file=stream)

    print(f"{style.bold}▶ INPUT{style.reset}  (raw log line as read from disk)", file=stream)
    print(f"  {_visible_bytes(line, style=style)}", file=stream)
    print(file=stream)

    print(f"{style.bold}▶ STEP 1 — Registry{style.reset}  (FR-PRS-030 / FR-PRS-031)", file=stream)
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
                f"{style.yellow}(joiner continuation — parse bypasses chain select){style.reset}",
                file=stream,
            )
            continue
        marker = f"{style.green}✓ selected{style.reset}" if confidence == Confidence.HIGH else "— skipped"
        print(f"  {name}.classify() → Confidence.{confidence.name}  {marker}", file=stream)
    print(file=stream)

    print(f"{style.bold}▶ STEP 2 — Classification{style.reset}  (FR-PRS-010)", file=stream)
    if joiner_continuation:
        print(
            "  Continuation line — joiner already holds a partial FIX message",
            file=stream,
        )
        print("  → classification skipped; line fed directly to joiner (FR-PRS-014)", file=stream)
    else:
        print(f"  Order: fix → app_log → unsupported (first 256 bytes)", file=stream)
        expected_cls, cls_steps = _explain_classification(line)
        for step in cls_steps:
            print(f"  {step}", file=stream)
        actual_cls = classify_line(line)
        if actual_cls != expected_cls:
            print(
                f"  {style.red}(internal mismatch: {actual_cls} vs {expected_cls}){style.reset}",
                file=stream,
            )
    print(file=stream)

    if result.classification == LineClassification.FIX:
        print(f"{style.bold}▶ STEP 3 — Framing{style.reset}  (FR-PRS-012 – FR-PRS-014)", file=stream)
        if result.joined_lines > 1:
            print(
                f"  {style.yellow}Multi-line message: {result.joined_lines} log lines joined "
                f"before framing{style.reset}",
                file=stream,
            )
            print(file=stream)
        if framing_bytes != line:
            print(
                f"  Combined buffer for framing ({len(framing_bytes)} bytes):",
                file=stream,
            )
            print(f"  {_visible_bytes(framing_bytes, style=style)}", file=stream)
            print(file=stream)
        for framing_line in _render_framing(framing_bytes, style=style):
            print(framing_line, file=stream)
        print(file=stream)
    else:
        print(
            f"{style.bold}▶ STEP 3 — Framing{style.reset}  {style.dim}(skipped — not FIX){style.reset}",
            file=stream,
        )
        print(file=stream)

    print(f"{style.bold}▶ OUTPUT{style.reset}  (ParseResult emitted to pipeline)", file=stream)
    for out_line in _render_output(result, style=style):
        print(out_line, file=stream)

    print(_hr(width), file=stream)
    print(file=stream)


def run_corpus_demo(corpus_dir: Path, *, stream: object = sys.stdout) -> None:
    """Walk a corpus directory and print the visual demo for each line."""
    style = _style_for(stream)

    registry = Registry()
    chain = ["fix"]
    unknown = registry.validate_chain(chain)
    if unknown:
        msg = f"unknown parsers in chain: {unknown}; registered={sorted(registered_names())}"
        raise SystemExit(msg)

    fix_parser = FixParser()

    files = sorted(p for p in corpus_dir.iterdir() if p.is_file())
    if not files:
        print(f"No files found in {corpus_dir}", file=stream)
        return

    print(_box_title("Telemetry Agent — FIX Parser Interactive Demo", width=72, style=style), file=stream)
    print(file=stream)
    print(
        "This demo walks each synthetic log line through the parser pipeline:\n"
        "  Registry → Classification → Framing → ParseResult\n",
        file=stream,
    )
    print(f"Corpus: {corpus_dir}", file=stream)
    print(f"Files:  {', '.join(p.name for p in files)}", file=stream)
    print(_hr(72), file=stream)
    print(file=stream)

    summary = {"lines": 0, "fix": 0, "app_log": 0, "unsupported": 0, "framed": 0, "errors": 0}

    for path in files:
        raw_lines = path.read_bytes().splitlines()
        non_empty = [ln for ln in raw_lines if ln.strip()]
        for idx, line in enumerate(non_empty, start=1):
            meta = SourceMeta(
                instance_id="demo",
                path=str(path.name),
                log_type="fix",
                read_at=datetime.now(tz=UTC),
            )
            joiner_continuation = fix_parser._joiner.has_pending
            framing_bytes = fix_parser.bytes_for_framing(line)
            result = fix_parser.parse(line, meta)
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

            render_demo_line(
                filename=path.name,
                line_no=idx,
                total_lines=len(non_empty),
                line=line,
                framing_bytes=framing_bytes,
                result=result,
                joiner_continuation=joiner_continuation,
                registry=registry,
                parser_chain=chain,
                fix_parser=fix_parser,
                stream=stream,
            )

    print(_box_title("Corpus Summary", width=72, style=style), file=stream)
    print(file=stream)
    print(f"  Total lines parsed:  {summary['lines']}", file=stream)
    print(f"  FIX classified:      {summary['fix']}", file=stream)
    print(f"  App log classified:  {summary['app_log']}", file=stream)
    print(f"  Unsupported:         {summary['unsupported']}", file=stream)
    print(f"  Successfully framed: {summary['framed']}", file=stream)
    print(f"  Frame errors:        {summary['errors']}", file=stream)
    print(file=stream)
