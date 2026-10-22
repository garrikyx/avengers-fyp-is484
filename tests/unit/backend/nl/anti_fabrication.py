"""FR-TST-008: numeric tokens in rendered answers must exist in structured data."""

from __future__ import annotations

import re

from telemetry_shared.models.metrics_query import MetricsQueryResponse

_NUMERIC_TOKEN = re.compile(r"\b\d+(?:\.\d+)?%?\b")


_ISO_DATETIME = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"
)


def numeric_tokens_in_text(text: str) -> list[str]:
    scrubbed = _ISO_DATETIME.sub(" ", text)
    return _NUMERIC_TOKEN.findall(scrubbed)


def _numbers_from_data(data: MetricsQueryResponse) -> set[str]:
    found: set[str] = set()
    for key, value in data.totals.items():
        if value is None:
            continue
        if isinstance(value, float):
            found.add(f"{value:.1%}".replace(".0%", "%"))
            if value <= 1:
                found.add(str(round(value * 100, 1)))
            found.add(f"{value:g}")
        else:
            found.add(str(int(value)))
    for group in data.groups:
        for value in group.counters.values():
            if value is not None:
                found.add(str(int(value)))
        for summary in data.latency.values():
            for field in (
                summary.p50_ms,
                summary.p95_ms,
                summary.p99_ms,
                summary.count,
            ):
                if field is not None:
                    found.add(str(int(field)))
    completeness = data.data_completeness
    found.update(
        {
            str(completeness.agents_expected),
            str(completeness.agents_reporting),
        }
    )
    effective = data.effective_time_range
    for dt in (effective.from_utc, effective.to_utc, data.evaluated_at_utc):
        found.add(str(dt.year))
        found.add(f"{dt.day:02d}")
        found.add(f"{dt.hour:02d}")
        found.add(f"{dt.minute:02d}")
    return found


def assert_answer_numbers_in_data(answer: str, data: MetricsQueryResponse) -> None:
    allowed = _numbers_from_data(data)
    for token in numeric_tokens_in_text(answer):
        bare = token.rstrip("%")
        if token.endswith("%"):
            if not any(t.rstrip("%") == bare or t == token for t in allowed):
                if bare not in allowed and token not in allowed:
                    raise AssertionError(
                        f"Fabricated percentage {token!r} not found in data payload"
                    )
        elif bare not in allowed and token not in allowed:
            raise AssertionError(
                f"Fabricated number {token!r} not found in data payload"
            )
