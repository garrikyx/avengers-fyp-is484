"""Synthetic FIX corpus loading helpers."""

from __future__ import annotations

from pathlib import Path

DEMO_LOGS_NAME = "demo_logs.txt"
FIX_CORPUS_DIR = Path(__file__).resolve().parents[3] / "testdata" / "fix"
DEMO_LOGS_PATH = FIX_CORPUS_DIR / DEMO_LOGS_NAME


def prepare_corpus_line(raw: bytes) -> tuple[bytes, str | None]:
    """Strip trailing `` # source.txt`` annotation from merged corpus lines."""
    marker = b" # "
    idx = raw.rfind(marker)
    if idx < 0:
        return raw, None
    label = raw[idx + len(marker) :]
    if not label.endswith(b".txt") or b" " in label:
        return raw, None
    return raw[:idx].rstrip(), label.decode("ascii")


def demo_log_lines(
    *,
    source: str | None = None,
    path: Path = DEMO_LOGS_PATH,
) -> list[tuple[bytes, str | None]]:
    """Return parsed corpus lines, optionally filtered to one source file label."""
    lines: list[tuple[bytes, str | None]] = []
    for raw in path.read_bytes().splitlines():
        if not raw.strip():
            continue
        line, label = prepare_corpus_line(raw)
        if source is not None and label != source:
            continue
        lines.append((line, label))
    return lines
