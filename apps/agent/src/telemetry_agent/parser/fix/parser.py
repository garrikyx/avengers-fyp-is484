from __future__ import annotations

from datetime import timedelta
from re import Pattern

from telemetry_agent.parser.fix.classify import classify_line, compile_app_log_patterns
from telemetry_agent.parser.fix.enrich import build_fix_telemetry
from telemetry_agent.parser.fix.fields import FixFields, extract_allowlisted_fields
from telemetry_agent.parser.fix.frame import (
    FrameOptions,
    Framer,
    FrameResult,
    LineJoiner,
)
from telemetry_agent.parser.fix.normalize import RejectPattern, compile_reject_patterns
from telemetry_agent.parser.fix.seq_tracker import SeqTracker
from telemetry_agent.parser.protocol import (
    Confidence,
    LineClassification,
    ParseError,
    ParseResult,
    SourceMeta,
)
from telemetry_agent.parser.registry import register_parser

_DEFAULT_REJECT_PATTERNS: list[tuple[str, str]] = [
    ("price_exceeds_limit", r"price.*(exceeds|outside).*limit"),
    ("unknown_symbol", r"unknown (symbol|instrument)"),
    ("market_closed", r"market (is )?closed|exchange closed"),
    ("risk_limit_breach", r"risk limit|credit limit|position limit"),
    ("duplicate_order", r"duplicate (order|clordid)"),
    ("throttled", r"throttl|rate limit|too many"),
]


class FixParser:

    def __init__(
        self,
        *,
        frame_options: FrameOptions | None = None,
        app_log_patterns: list[str] | None = None,
        hash_key: bytes | None = None,
        reject_reason_patterns: list[tuple[str, str]] | None = None,
        max_reject_reason_labels: int = 50,
        max_clock_skew: timedelta = timedelta(minutes=5),
    ) -> None:
        self._frame_options = frame_options or FrameOptions()
        self._app_log_patterns: list[Pattern[bytes]] = (
            compile_app_log_patterns(app_log_patterns) if app_log_patterns else []
        )
        self._hash_key = hash_key
        self._reject_patterns: list[RejectPattern] = compile_reject_patterns(
            reject_reason_patterns or _DEFAULT_REJECT_PATTERNS
        )
        self._max_reject_labels = max_reject_reason_labels
        self._max_clock_skew = max_clock_skew
        self._seen_reject_labels: set[str] = set()
        self._framer = Framer(self._frame_options)
        self._joiner = LineJoiner(self._framer, self._frame_options.max_join_lines)
        self._seq_tracker = SeqTracker()

    def name(self) -> str:
        return "fix"

    def classify(self, line: bytes) -> Confidence:
        result = classify_line(line, app_log_patterns=self._app_log_patterns)
        if result == LineClassification.FIX:
            return Confidence.HIGH
        return Confidence.NONE

    def parse(self, line: bytes, meta: SourceMeta) -> ParseResult:
        if meta.truncated:
            return ParseResult(
                classification=LineClassification.FIX,
                framed=False,
                error=ParseError(reason="line_truncated"),
            )

        try:
            if self._joiner.has_pending:
                frame_result = self._joiner.feed(line)
                if frame_result is None:
                    return ParseResult(
                        classification=LineClassification.FIX,
                        framed=False,
                    )
                return self._frame_to_parse_result(
                    frame_result,
                    joined_lines=frame_result.joined_lines,
                    meta=meta,
                )

            classification = classify_line(
                line,
                app_log_patterns=self._app_log_patterns,
            )
            if classification != LineClassification.FIX:
                return ParseResult(classification=classification)

            frame_result = self._joiner.feed(line)
            if frame_result is None:
                return ParseResult(
                    classification=LineClassification.FIX,
                    framed=False,
                )

            return self._frame_to_parse_result(
                frame_result,
                joined_lines=frame_result.joined_lines,
                meta=meta,
            )
        except Exception as exc:
            return ParseResult(
                classification=LineClassification.FIX,
                error=ParseError(reason="internal_error", detail=type(exc).__name__),
                internal_error=True,
            )

    def _frame_to_parse_result(
        self,
        frame_result: FrameResult,
        *,
        joined_lines: int,
        meta: SourceMeta,
    ) -> ParseResult:
        if not frame_result.ok:
            return ParseResult(
                classification=LineClassification.FIX,
                framed=False,
                warnings=list(frame_result.warnings),
                error=ParseError(reason=frame_result.error_reason),
                joined_lines=joined_lines,
            )

        message = frame_result.message
        if message is None:
            return ParseResult(
                classification=LineClassification.FIX,
                framed=False,
                error=ParseError(reason="internal_error"),
                internal_error=True,
            )

        warnings = list(frame_result.warnings)
        extracted = extract_allowlisted_fields(message.fields, hash_key=self._hash_key)
        telemetry = build_fix_telemetry(
            extracted,
            meta=meta,
            reject_patterns=self._reject_patterns,
            max_reject_labels=self._max_reject_labels,
            seen_reject_labels=self._seen_reject_labels,
            seq_tracker=self._seq_tracker,
            max_clock_skew=self._max_clock_skew,
        )

        if telemetry.unknown_msg_type:
            warnings.append("unknown_msg_type")

        safe_fields = _strip_sensitive_fields(extracted)

        return ParseResult(
            classification=LineClassification.FIX,
            framed=True,
            msg_type=message.fields.get("35", ""),
            delimiter=message.delimiter.value,
            warnings=warnings,
            joined_lines=joined_lines,
            fields=safe_fields,
            telemetry=telemetry,
        )


def _strip_sensitive_fields(fields: FixFields) -> FixFields:
    """Remove raw tag 58 text from egress (FR-PRS-022)."""
    return FixFields(
        fix_version=fields.fix_version,
        msg_type=fields.msg_type,
        seq_num=fields.seq_num,
        sender_comp_id=fields.sender_comp_id,
        target_comp_id=fields.target_comp_id,
        sending_time=fields.sending_time,
        transact_time=fields.transact_time,
        cl_ord_id_hash=fields.cl_ord_id_hash,
        orig_cl_ord_id_hash=fields.orig_cl_ord_id_hash,
        order_id_hash=fields.order_id_hash,
        exec_id_hash=fields.exec_id_hash,
        exec_type=fields.exec_type,
        ord_status=fields.ord_status,
        symbol=fields.symbol,
        side=fields.side,
        ord_type=fields.ord_type,
        order_qty=fields.order_qty,
        last_qty=fields.last_qty,
        cum_qty=fields.cum_qty,
        leaves_qty=fields.leaves_qty,
        ord_rej_reason=fields.ord_rej_reason,
        text=None,
        ref_seq_num=fields.ref_seq_num,
        ref_msg_type=fields.ref_msg_type,
        session_reject_reason=fields.session_reject_reason,
    )

register_parser(FixParser())
