from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class DemoConfig:
    app_log_patterns: list[str]
    reject_reason_patterns: list[tuple[str, str]]
    error_signatures: list[tuple[str, str]]
    max_reject_reason_labels: int = 50
    max_dynamic_signature_labels: int = 50
    max_clock_skew: timedelta = timedelta(minutes=5)


def load_demo_config(path: Path) -> DemoConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = f"invalid config root in {path}"
        raise ValueError(msg)

    parsing = raw.get("parsing", {})
    if not isinstance(parsing, dict):
        parsing = {}

    app_log = _string_list(raw.get("appLogPatterns", []))
    reject = _label_match_pairs(parsing.get("rejectReasonPatterns", []))
    signatures = _label_match_pairs(parsing.get("errorSignatures", []))

    max_reject = int(parsing.get("maxRejectReasonLabels", 50))
    max_sig = int(parsing.get("maxDynamicSignatureLabels", 50))
    skew = _parse_duration(str(parsing.get("maxClockSkew", "5m")))

    return DemoConfig(
        app_log_patterns=app_log,
        reject_reason_patterns=reject,
        error_signatures=signatures,
        max_reject_reason_labels=max_reject,
        max_dynamic_signature_labels=max_sig,
        max_clock_skew=skew,
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _label_match_pairs(value: Any) -> list[tuple[str, str]]:
    if not isinstance(value, list):
        return []
    pairs: list[tuple[str, str]] = []
    for item in value:
        if isinstance(item, dict) and "label" in item and "match" in item:
            pairs.append((str(item["label"]), str(item["match"])))
    return pairs


def _parse_duration(raw: str) -> timedelta:
    raw = raw.strip()
    if raw.endswith("m"):
        return timedelta(minutes=int(raw[:-1]))
    if raw.endswith("s"):
        return timedelta(seconds=int(raw[:-1]))
    if raw.endswith("h"):
        return timedelta(hours=int(raw[:-1]))
    return timedelta(minutes=int(raw))
