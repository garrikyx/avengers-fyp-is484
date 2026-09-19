from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

SOH = b"\x01"


class DelimiterMode(str, Enum):
    AUTO = "auto"
    SOH = "soh"
    PIPE = "pipe"
    CARET = "caret"
    SEMICOLON = "semicolon"


@dataclass(slots=True)
class FrameOptions:
    """Per file-set framing configuration."""

    delimiter: DelimiterMode = DelimiterMode.AUTO
    validate_checksum: bool = False
    max_join_lines: int = 4
    auto_lock_after: int = 100


@dataclass(slots=True)
class FramedMessage:
    """A FIX message extracted from log bytes."""

    raw: bytes
    fields: dict[str, str]
    delimiter: DelimiterMode
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FrameResult:
    ok: bool
    message: FramedMessage | None = None
    error_reason: str = ""
    warnings: list[str] = field(default_factory=list)
    joined_lines: int = 1


class Framer:
    """Frames FIX messages with optional auto delimiter lock."""

    def __init__(self, options: FrameOptions | None = None) -> None:
        self._options = options or FrameOptions()
        self._locked: DelimiterMode | None = None
        if self._options.delimiter != DelimiterMode.AUTO:
            self._locked = self._options.delimiter
        self._auto_successes = 0

    @property
    def locked_delimiter(self) -> DelimiterMode | None:
        return self._locked

    def frame(self, data: bytes) -> FrameResult:
        """Extract one FIX message from log line bytes."""
        start = _find_begin_string(data)
        if start < 0:
            return FrameResult(ok=False, error_reason="no_begin_string")

        body = data[start:]
        delim = self._choose_delimiter(body)
        if delim is None:
            return FrameResult(ok=False, error_reason="malformed_field")

        sliced = _slice_to_checksum(body, delim)
        if sliced is None:
            return FrameResult(ok=False, error_reason="incomplete_message")

        fields, warnings = _split_fields(sliced, delim)
        if "8" not in fields:
            return FrameResult(ok=False, error_reason="no_begin_string")
        if not fields.get("35"):
            return FrameResult(ok=False, error_reason="no_msg_type")

        body_len_warn = _check_body_length(fields, sliced, delim)
        if body_len_warn:
            warnings.append(body_len_warn)

        if self._options.validate_checksum:
            checksum_warn = _check_checksum(fields, sliced, delim)
            if checksum_warn:
                warnings.append(checksum_warn)
                return FrameResult(
                    ok=False,
                    error_reason="checksum_mismatch",
                    warnings=warnings,
                )

        if self._options.delimiter == DelimiterMode.AUTO and self._locked is None:
            self._auto_successes += 1
            if self._auto_successes >= self._options.auto_lock_after:
                self._locked = delim

        return FrameResult(
            ok=True,
            message=FramedMessage(
                raw=sliced,
                fields=fields,
                delimiter=delim,
                warnings=warnings,
            ),
            warnings=warnings,
        )

    def _choose_delimiter(self, body: bytes) -> DelimiterMode | None:
        if self._locked is not None:
            return self._locked
        return _sniff_delimiter(body)


class LineJoiner:
    """Joins split FIX messages across log lines."""

    def __init__(self, framer: Framer, max_join_lines: int = 4) -> None:
        self._framer = framer
        self._max_join_lines = max_join_lines
        self._pending: list[bytes] = []

    @property
    def has_pending(self) -> bool:
        return bool(self._pending)

    def feed(self, line: bytes) -> FrameResult | None:
        """
        Feed one log line. Returns FrameResult when a complete message is ready,
        or None while waiting for continuation lines.
        """
        if self._pending:
            self._pending.append(line)
        elif _find_begin_string(line) >= 0:
            self._pending = [line]
        else:
            return None

        joined = b"".join(self._pending)
        if _has_checksum_field(joined, self._framer.locked_delimiter):
            joined_count = len(self._pending)
            if joined_count > self._max_join_lines:
                self._pending.clear()
                return FrameResult(ok=False, error_reason="incomplete_message")
            result = self._framer.frame(joined)
            result.joined_lines = joined_count
            self._pending.clear()
            return result

        if len(self._pending) >= self._max_join_lines:
            self._pending.clear()
            return FrameResult(ok=False, error_reason="incomplete_message")

        return None


def frame_message(data: bytes, options: FrameOptions | None = None) -> FrameResult:
    """Frame a single complete log line."""
    return Framer(options).frame(data)


def _find_begin_string(data: bytes) -> int:
    best = -1
    for token in (b"8=FIX", b"8=FIXT"):
        idx = data.find(token)
        if idx >= 0 and (best < 0 or idx < best):
            best = idx
    return best


def _sniff_delimiter(body: bytes) -> DelimiterMode | None:
    scores = {
        DelimiterMode.SOH: body.count(SOH),
        DelimiterMode.PIPE: body.count(b"|"),
        DelimiterMode.SEMICOLON: body.count(b";"),
        DelimiterMode.CARET: body.count(b"^A"),
    }
    order = (
        DelimiterMode.PIPE,
        DelimiterMode.SEMICOLON,
        DelimiterMode.SOH,
        DelimiterMode.CARET,
    )
    best = max(scores.values())
    if best == 0:
        return DelimiterMode.PIPE if b"|" in body else DelimiterMode.SOH
    for mode in order:
        if scores[mode] == best and scores[mode] > 0:
            return mode
    return DelimiterMode.SOH


def _delimiter_byte(mode: DelimiterMode) -> bytes:
    if mode == DelimiterMode.SOH or mode == DelimiterMode.CARET:
        return SOH
    if mode == DelimiterMode.PIPE:
        return b"|"
    if mode == DelimiterMode.SEMICOLON:
        return b";"
    return SOH


def _has_checksum_field(data: bytes, locked: DelimiterMode | None) -> bool:
    if locked is not None:
        delim = _delimiter_byte(locked)
        return _contains_tag(data, b"10=", delim)
    for mode in (DelimiterMode.PIPE, DelimiterMode.SEMICOLON, DelimiterMode.SOH):
        if _contains_tag(data, b"10=", _delimiter_byte(mode)):
            return True
    return b"10=" in data


def _contains_tag(data: bytes, tag: bytes, delim: bytes) -> bool:
    needle = tag + delim
    if needle in data:
        return True
    if delim == SOH:
        return data.endswith(tag) or (tag + SOH) in data
    return False


def _slice_to_checksum(body: bytes, mode: DelimiterMode) -> bytes | None:
    delim = _delimiter_byte(mode)
    idx = body.find(b"10=")
    if idx < 0:
        return None

    end = idx
    rest = body[idx + 3 :]
    if rest.startswith(delim):
        end = idx + 3
        value_end = rest.find(delim, 1)
        if value_end >= 0:
            end = idx + 3 + value_end + 1
        else:
            end = len(body)
    else:
        for i, ch in enumerate(rest):
            if len(delim) == 1 and ch == delim[0]:
                end = idx + 3 + i + 1
                break
        else:
            end = len(body)

    return body[:end]


def _split_fields(
    data: bytes,
    mode: DelimiterMode,
) -> tuple[dict[str, str], list[str]]:
    fields: dict[str, str] = {}
    warnings: list[str] = []
    delim = _delimiter_byte(mode)

    if mode == DelimiterMode.CARET and b"^A" in data:
        parts = data.replace(b"^A", SOH).split(SOH)
    else:
        parts = data.split(delim)

    for part in parts:
        if not part:
            continue
        if b"=" not in part:
            warnings.append("malformed_field")
            continue
        tag_b, _, value_b = part.partition(b"=")
        try:
            tag = tag_b.decode("ascii")
        except UnicodeDecodeError:
            warnings.append("malformed_field")
            continue
        if not tag.isdigit():
            warnings.append("malformed_field")
            continue
        fields[tag] = value_b.decode("utf-8", errors="replace")
    return fields, warnings


def _check_body_length(fields: dict[str, str], data: bytes, mode: DelimiterMode) -> str:
    """Soft warning only."""
    body_len = fields.get("9")
    if not body_len or not body_len.isdigit():
        return ""
    expected = int(body_len)
    start = data.find(b"35=")
    if start < 0:
        return ""
    end = data.find(_delimiter_byte(mode) + b"10=")
    if end < 0:
        end = data.find(b"10=")
    if end < 0:
        return ""
    actual = end - start
    if actual != expected:
        return "body_length_mismatch"
    return ""


def _check_checksum(fields: dict[str, str], data: bytes, mode: DelimiterMode) -> str:
    """When validate_checksum enabled."""
    declared = fields.get("10")
    if declared is None:
        return "checksum_mismatch"
    idx = data.find(b"10=")
    if idx < 0:
        return "checksum_mismatch"
    payload = data[:idx]
    total = sum(payload) % 256
    expected = f"{total:03d}"
    if declared.zfill(3) != expected:
        return "checksum_mismatch"
    return ""
