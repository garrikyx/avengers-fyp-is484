"""Adaptive Card builders (spec 008 §5, §6).

Pure functions: backend response in, card JSON out. The bot never recomputes
numbers (FR-NLQ-009); it renders what the backend returned. Every dynamic string
goes through `escape_card_text` (FR-NLQ-022).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, tzinfo
from typing import Any
from zoneinfo import ZoneInfo

from telemetry_shared.models.metrics_query import QueryGroup
from telemetry_shared.models.nl_query import NlClarificationResponse, NlQueryResponse

from teams_agent.backend_client import ErrorKind
from teams_agent.escape import escape_card_text

SCHEMA_VERSION = "1.4"
MAX_BREAKDOWN_ROWS = 10
NO_DATA = "not enough data"
DEFAULT_DISPLAY_TZ = ZoneInfo("Asia/Singapore")
UNSPECIFIED = "unspecified"  # the backend's placeholder for a missing dimension
_QUERY_BLOCK_ID = "interpretedQuery"

_ERROR_MESSAGES: dict[ErrorKind, str] = {
    "disabled": "Natural-language queries are currently disabled.",
    "bad_request": "I couldn't process that question. Try rephrasing it.",
    "timeout": "The telemetry service took too long to answer. Please try again.",
    "unavailable": (
        "I couldn't reach the telemetry service. Please try again shortly."
    ),
}


def _card(
    body: list[dict[str, Any]], actions: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    card: dict[str, Any] = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": SCHEMA_VERSION,
        "body": body,
    }
    if actions:
        card["actions"] = actions
    return card


def _text(text: str, *, escape: bool = True, **props: Any) -> dict[str, Any]:
    return {
        "type": "TextBlock",
        "text": escape_card_text(text) if escape else text,
        "wrap": True,
        **props,
    }


def _format_value(name: str, value: int | float | None) -> str:
    if value is None:
        return NO_DATA
    if isinstance(value, float):
        if name.lower().endswith("rate"):
            return f"{value:.1%}"
        return f"{value:,.2f}"
    return f"{value:,}"


def _group_row(group: QueryGroup) -> tuple[str, str]:
    known = [v for v in group.dimensions.values() if v != UNSPECIFIED]
    label = ", ".join(known) or "All"
    parts = [
        f"{name} {_format_value(name, value)}" for name, value in group.counters.items()
    ]
    parts += [
        f"{name} {_format_value(name, value)}"
        for name, value in group.indicators.items()
    ]
    return label, " · ".join(parts)


def _breakdown_rows(response: NlQueryResponse) -> tuple[list[tuple[str, str]], bool]:
    data = response.data
    if data.groups:
        rows = [_group_row(group) for group in data.groups]
    else:
        rows = [
            (name, _format_value(name, value)) for name, value in data.totals.items()
        ]
    overflow = len(rows) > MAX_BREAKDOWN_ROWS
    return rows[:MAX_BREAKDOWN_ROWS], overflow or data.truncated


def _breakdown(response: NlQueryResponse) -> list[dict[str, Any]]:
    rows, more = _breakdown_rows(response)
    if not rows:
        return []
    items: list[dict[str, Any]] = [
        {
            "type": "ColumnSet",
            "separator": index == 0,
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [_text(label, weight="Bolder")],
                },
                {"type": "Column", "width": "stretch", "items": [_text(value)]},
            ],
        }
        for index, (label, value) in enumerate(rows)
    ]
    if more:
        items.append(
            _text("More rows exist than are shown.", isSubtle=True, size="Small")
        )
    return items


def _alert_badge(response: NlQueryResponse) -> list[dict[str, Any]]:
    count = sum(1 for citation in response.citations if citation.type == "alert")
    if count == 0:
        return []
    noun = "alert" if count == 1 else "alerts"
    return [
        {
            "type": "Container",
            "style": "attention",
            "items": [_text(f"{count} active {noun}", weight="Bolder")],
        }
    ]


def _notes(response: NlQueryResponse) -> list[str]:
    data = response.data
    completeness = data.data_completeness
    notes = list(response.caveats)
    if completeness.confidence != "complete":
        missing = completeness.agents_expected - completeness.agents_reporting
        if missing > 0:
            notes.append(
                f"{missing} of {completeness.agents_expected} agents "
                "not reporting, so these numbers are incomplete."
            )
        else:
            notes.append(
                f"Data is {completeness.confidence}: these numbers may be incomplete."
            )
    if data.timed_out or data.partial:
        notes.append("The query returned partial results.")
    return notes


def _utc_offset_label(moment: datetime) -> str:
    offset = moment.utcoffset() or timedelta(0)
    minutes = int(offset.total_seconds() // 60)
    sign = "+" if minutes >= 0 else "-"
    hours, rest = divmod(abs(minutes), 60)
    return f"UTC{sign}{hours}" + (f":{rest:02d}" if rest else "")


def _range_line(response: NlQueryResponse, tz: tzinfo) -> str:
    window = response.data.effective_time_range
    start = window.from_utc.astimezone(tz)
    end = window.to_utc.astimezone(tz)
    fmt = "%Y-%m-%d %H:%M"
    label = _utc_offset_label(end)
    return f"Range: {start.strftime(fmt)} to {end.strftime(fmt)} {label}"


def build_answer_card(
    response: NlQueryResponse, tz: tzinfo = DEFAULT_DISPLAY_TZ
) -> dict[str, Any]:
    """`tz` is only for display; the backend's times stay UTC."""
    body: list[dict[str, Any]] = [_text(response.answer, size="Large", weight="Bolder")]
    body += _breakdown(response)
    body += _alert_badge(response)
    notes = _notes(response)
    if notes:
        body.append(
            {
                "type": "Container",
                "separator": True,
                "items": [_text(f"• {note}", size="Small") for note in notes],
            }
        )
    body.append(_text(_range_line(response, tz), isSubtle=True, size="Small"))
    query_json = json.dumps(
        response.interpreted_query.model_dump(mode="json", by_alias=True), indent=2
    )
    body.append(
        _text(
            query_json,
            id=_QUERY_BLOCK_ID,
            isVisible=False,
            fontType="Monospace",
            size="Small",
        )
    )
    actions = [
        {
            "type": "Action.ToggleVisibility",
            "title": "Show query",
            "targetElements": [_QUERY_BLOCK_ID],
        }
    ]
    return _card(body, actions)


def build_clarification_card(response: NlClarificationResponse) -> dict[str, Any]:
    body: list[dict[str, Any]] = [_text(response.message, weight="Bolder")]
    body += [_text(f"• {detail}", size="Small") for detail in response.details]
    if response.supported_intents:
        intents = ", ".join(
            intent.replace("_", " ") for intent in response.supported_intents
        )
        body.append(_text(f"I can answer questions about: {intents}.", isSubtle=True))
    return _card(body)


def build_error_card(kind: ErrorKind) -> dict[str, Any]:
    return _card([_text(_ERROR_MESSAGES[kind])])
