"""Demo metrics sink for parser CLI (mirrors spec 004 counter names)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from telemetry_agent.parser.protocol import LineClassification, ParseResult


@dataclass(slots=True)
class DemoMetricsSink:
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    signature_labels: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record_parse_result(self, result: ParseResult) -> None:
        if result.classification == LineClassification.UNSUPPORTED:
            self.counters["unsupported_lines"] += 1
            return

        if result.classification == LineClassification.APP_LOG:
            self.counters["log_lines_read"] += 1
            return

        self.counters["log_lines_read"] += 1

        if result.internal_error:
            self.counters["internal_errors"] += 1

        if result.error is not None:
            key = f"parse_errors:{result.error.reason}"
            self.counters[key] += 1
            return

        if not result.framed:
            return

        tel = result.telemetry
        if tel is None:
            return

        if tel.unclassified_reject_text:
            self.counters["unclassified_reject_text"] += 1

        for _ in tel.unknown_enums:
            self.counters["unknown_enum_values"] += 1

        if tel.bad_timestamp:
            self.counters["parse_errors:bad_timestamp"] += 1

        if tel.clock_skew:
            self.counters["clock_skew_events"] += 1

        if tel.unknown_msg_type:
            self.counters["parse_errors:unknown_msg_type"] += 1

        if tel.seq_gap is not None:
            if tel.seq_gap.is_regression:
                self.counters["seq_regressions"] += 1
            else:
                self.counters["seq_gaps"] += 1
                self.counters["seq_gap_messages"] += tel.seq_gap.gap_size

        msg = tel.normalized_msg_type
        if msg:
            self.counters["fix_messages_total"] += 1
            self.counters[f"fix_messages_by_type:{msg}"] += 1

        if msg == "Reject":
            self.counters["session_rejects"] += 1
        elif msg == "ExecutionReport" and (
            tel.normalized_exec_type == "Rejected"
            or tel.normalized_ord_status == "Rejected"
        ):
            self.counters["orders_rejected"] += 1
        elif msg == "NewOrderSingle":
            self.counters["orders_submitted"] += 1
        elif msg == "Logon":
            self.counters["logons"] += 1
        elif msg == "Logout":
            self.counters["logouts"] += 1

    def record_app_signature(self, label: str) -> None:
        self.signature_labels[label] += 1
        self.counters["app.error_signature"] += 1

    def format_block(self) -> str:
        lines = ["METRICS:"]
        for key in sorted(self.counters):
            lines.append(f"  {key}: {self.counters[key]}")
        for label in sorted(self.signature_labels):
            count = self.signature_labels[label]
            lines.append(f"  app.error_signature{{{label}}}: {count}")
        return "\n".join(lines)
