from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern

_CAPTURE_SANITIZE = re.compile(r"[^a-z0-9]")
_MAX_CAPTURE_LEN = 16


@dataclass(frozen=True, slots=True)
class SignatureRule:
    label: str
    pattern: Pattern[bytes]


def compile_signature_rules(
    rules: list[tuple[str, str]],
) -> list[SignatureRule]:
    compiled: list[SignatureRule] = []
    for label, match in rules:
        compiled.append(
            SignatureRule(label=label, pattern=re.compile(match.encode("utf-8")))
        )
    return compiled


def _sanitize_capture(raw: str) -> str:
    cleaned = _CAPTURE_SANITIZE.sub("", raw.lower())[:_MAX_CAPTURE_LEN]
    return cleaned


def resolve_label_template(label: str, capture: str) -> str | None:
    if "%" not in label:
        return label
    sanitized = _sanitize_capture(capture)
    if not sanitized:
        return None
    return label.replace("%", sanitized)


class SignatureMatcher:
    """First-match-wins signature rules with dynamic label templates."""

    def __init__(
        self,
        rules: list[SignatureRule],
        *,
        max_dynamic_labels: int = 50,
    ) -> None:
        self._rules = rules
        self._max_dynamic = max_dynamic_labels
        self._seen_dynamic: set[str] = set()
        self._overflow_count = 0

    @property
    def overflow_count(self) -> int:
        return self._overflow_count

    def match(self, line: bytes) -> str | None:
        for rule in self._rules:
            match = rule.pattern.search(line)
            if match is None:
                continue
            if "%" in rule.label:
                if match.lastindex is None or match.lastindex < 1:
                    continue
                capture = match.group(1).decode("utf-8", errors="replace")
                resolved = resolve_label_template(rule.label, capture)
                if resolved is None:
                    continue
                return self._apply_cardinality(resolved)
            return rule.label
        return None

    def _apply_cardinality(self, label: str) -> str:
        if label in self._seen_dynamic:
            return label
        if len(self._seen_dynamic) >= self._max_dynamic:
            self._overflow_count += 1
            return "__other__"
        self._seen_dynamic.add(label)
        return label


def extract_log_level(line: bytes) -> str | None:
    """Extract [N/E/W/F/I] level from Magic-style log lines."""
    match = re.search(rb"\[([NWEIF])\]", line)
    if match is None:
        return None
    return match.group(1).decode("ascii")
