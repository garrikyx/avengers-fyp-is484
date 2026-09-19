from __future__ import annotations

from dataclasses import dataclass, field

from telemetry_agent.parser.fix.telemetry import SeqGapEvent


@dataclass(slots=True)
class SeqTracker:
    """Per-session MsgSeqNum tracking."""

    _last_seq: dict[str, int] = field(default_factory=dict)

    def session_key(
        self,
        sender: str | None,
        target: str | None,
        *,
        direction: str = "out",
    ) -> str:
        return f"{sender or '?'}->{target or '?'}:{direction}"

    def observe(
        self,
        *,
        msg_type: str | None,
        seq_num: str | None,
        sender: str | None,
        target: str | None,
        direction: str = "out",
    ) -> SeqGapEvent | None:
        key = self.session_key(sender, target, direction=direction)

        if msg_type in ("Logon", "A"):
            if seq_num is not None and seq_num.isdigit():
                self._last_seq[key] = int(seq_num)
            else:
                self._last_seq.pop(key, None)
            return None

        if msg_type in ("SequenceReset", "4"):
            if seq_num is not None and seq_num.isdigit():
                self._last_seq[key] = int(seq_num)
            return None

        if seq_num is None or not seq_num.isdigit():
            return None

        current = int(seq_num)
        last = self._last_seq.get(key)
        self._last_seq[key] = current

        if last is None:
            return None

        expected = last + 1
        if current == expected:
            return None
        if current < expected:
            return SeqGapEvent(
                session_key=key,
                expected=expected,
                actual=current,
                gap_size=0,
                is_regression=True,
            )
        gap_size = current - expected
        return SeqGapEvent(
            session_key=key,
            expected=expected,
            actual=current,
            gap_size=gap_size,
            is_regression=False,
        )
