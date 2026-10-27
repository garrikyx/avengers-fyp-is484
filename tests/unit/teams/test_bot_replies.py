"""The Teams bot through its message boundary: Teams activity in, card out.

The backend is stubbed at the HTTP level; assertions are on the reply card and on
what the bot sent to the backend.
"""

from __future__ import annotations

import re

import httpx
from telemetry_shared.models.metrics_query import DataCompleteness, QueryGroup
from telemetry_shared.models.nl_query import NlCitation

from tests.unit.teams.fixtures import (
    answer,
    clarification,
    converse,
    group,
    json_ok,
    message,
    text_blocks,
    texts,
)

_UNESCAPED = re.compile(r"(?<!\\)[\[\]()<>`*_~#|&]")


def test_answer_card_has_headline_breakdown_range_and_show_query_toggle() -> None:
    response = answer(
        groups=[group("OrderExceedsLimit", orders_rejected=35)],
    )
    exchange = converse(message("why are orders rejecting?"), json_ok(response))

    card = exchange.card
    assert card["version"] == "1.4"
    assert card["type"] == "AdaptiveCard"
    body_text = " ".join(texts(card))
    assert "62 rejected orders" in body_text
    assert "OrderExceedsLimit" in body_text
    assert "orders\\_rejected 35" in body_text
    assert "Range: 2026-10-21 22:00 to 2026-10-21 22:30 UTC+8" in body_text

    [toggle] = card["actions"]
    assert toggle["type"] == "Action.ToggleVisibility"
    assert toggle["title"] == "Show query"
    [target] = toggle["targetElements"]
    hidden = next(b for b in text_blocks(card) if b.get("id") == target)
    assert hidden["isVisible"] is False
    assert "rejection_summary" in hidden["text"].replace("\\", "")


def test_headline_leads_the_card() -> None:
    exchange = converse(message("q"), json_ok(answer()))
    assert texts(exchange.card)[0].startswith("Magic recorded 62")


def test_breakdown_is_capped_at_ten_rows_with_a_note() -> None:
    groups = [group(f"Reason{i}", orders_rejected=i) for i in range(15)]
    exchange = converse(message("q"), json_ok(answer(groups=groups)))

    body_text = " ".join(texts(exchange.card))
    assert "Reason9" in body_text
    assert "Reason10" not in body_text
    assert "More rows exist than are shown." in body_text


def test_truncated_result_gets_the_more_rows_note() -> None:
    exchange = converse(
        message("q"),
        json_ok(answer(groups=[group("A", orders_rejected=1)], truncated=True)),
    )
    assert "More rows exist than are shown." in " ".join(texts(exchange.card))


def test_null_indicator_reads_not_enough_data_never_zero() -> None:
    null_rate = QueryGroup(
        dimensions={"rejectReason": "All"},
        counters={"orders_submitted": 0},
        indicators={"rejectRate": None},
    )
    exchange = converse(message("q"), json_ok(answer(groups=[null_rate])))

    body_text = " ".join(texts(exchange.card))
    assert "rejectRate not enough data" in body_text
    assert "0%" not in body_text


def test_totals_are_the_breakdown_when_there_are_no_groups() -> None:
    exchange = converse(
        message("q"),
        json_ok(answer(totals={"orders_rejected": 62, "rejectRate": 0.05})),
    )
    body_text = " ".join(texts(exchange.card))
    assert "orders\\_rejected" in body_text
    assert "5.0%" in body_text


def test_alert_badge_counts_alert_citations() -> None:
    response = answer(
        citations=[
            NlCitation(type="metrics_query", query_id="q-1"),
            NlCitation(type="alert", alert_id="a-1"),
            NlCitation(type="alert", alert_id="a-2"),
        ]
    )
    exchange = converse(message("any alerts?"), json_ok(response))

    badges = [
        c
        for c in exchange.card["body"]
        if c.get("type") == "Container" and c.get("style") == "attention"
    ]
    assert len(badges) == 1
    assert "2 active alerts" in texts(badges[0])[0]


def test_no_alert_badge_without_alert_citations() -> None:
    exchange = converse(message("q"), json_ok(answer()))
    assert not [c for c in exchange.card["body"] if c.get("style") == "attention"]


def test_partial_data_is_stated_plainly() -> None:
    completeness = DataCompleteness(
        agents_expected=3, agents_reporting=2, confidence="partial"
    )
    exchange = converse(message("q"), json_ok(answer(completeness=completeness)))
    assert "1 of 3 agents not reporting, so these numbers are incomplete." in " ".join(
        texts(exchange.card)
    )


def test_complete_data_makes_no_completeness_claim() -> None:
    exchange = converse(message("q"), json_ok(answer()))
    assert "incomplete" not in " ".join(texts(exchange.card))


def test_backend_caveats_are_shown() -> None:
    exchange = converse(
        message("q"),
        json_ok(
            answer(caveats=["Showing the last 6 hours; earlier data is not retained."])
        ),
    )
    assert "earlier data is not retained" in " ".join(texts(exchange.card))


def test_clarification_card_lists_supported_intents() -> None:
    exchange = converse(message("gibberish"), json_ok(clarification()))

    body_text = " ".join(texts(exchange.card))
    assert "I could not interpret that question." in body_text
    assert "timeRange: unsupported" in body_text
    assert "rejection summary" in body_text
    assert "alert status" in body_text
    assert "actions" not in exchange.card


def test_hostile_text_is_escaped_in_every_rendered_field() -> None:
    evil = "[click](http://evil) <at>everyone</at> *bold* `x`"
    response = answer(
        text=f"Headline {evil}",
        groups=[group(evil, orders_rejected=1)],
        caveats=[evil],
        filters={"application": evil},
    )
    exchange = converse(message("q"), json_ok(response))

    for text in texts(exchange.card):
        assert not _UNESCAPED.search(text), text
    assert "\\[click\\]\\(http://evil\\)" in texts(exchange.card)[0]


def test_FR_NLQ_030_reply_offers_suggested_questions_as_buttons() -> None:
    response = clarification().model_copy(
        update={
            "message": "Hi! I can answer questions about Magic's telemetry.",
            "reason": "greeting",
            "details": [],
            "suggested_questions": ["How is Magic doing today?", "Any alerts open?"],
        }
    )
    exchange = converse(message("hi"), json_ok(response))

    body_text = " ".join(texts(exchange.card))
    assert "I can answer questions about: " not in body_text
    buttons = exchange.card["actions"]
    assert [b["title"] for b in buttons] == [
        "How is Magic doing today?",
        "Any alerts open?",
    ]
    assert buttons[0]["type"] == "Action.Submit"
    assert buttons[0]["data"]["msteams"] == {
        "type": "imBack",
        "value": "How is Magic doing today?",
    }


def test_hostile_clarification_text_is_escaped() -> None:
    evil = "<at>everyone</at> [x](http://evil)"
    response = clarification().model_copy(update={"message": evil, "details": [evil]})
    exchange = converse(message("q"), json_ok(response))
    for text in texts(exchange.card):
        assert not _UNESCAPED.search(text), text


def test_bot_mention_is_stripped_before_the_question_is_sent() -> None:
    exchange = converse(
        message("why are orders rejecting?", mention=True), json_ok(answer())
    )
    assert exchange.requests == [
        {
            "question": "why are orders rejecting?",
            "context": {
                "defaultApplication": "Magic",
                "userTimezone": "Asia/Singapore",
                "audience": "technical",
            },
        }
    ]


def test_one_message_makes_one_backend_call() -> None:
    exchange = converse(message("q"), json_ok(answer()))
    assert len(exchange.requests) == 1


def test_empty_message_is_ignored_without_calling_the_backend() -> None:
    exchange = converse(message("   ", mention=False), json_ok(answer()))
    assert exchange.reply is None
    assert exchange.requests == []


def test_message_with_only_the_mention_is_ignored() -> None:
    exchange = converse(message("", mention=True), json_ok(answer()))
    assert exchange.reply is None
    assert exchange.requests == []


def test_user_timezone_comes_from_the_activity() -> None:
    exchange = converse(
        message("since 9am", local_timezone="America/Los_Angeles"), json_ok(answer())
    )
    assert exchange.requests[0]["context"]["userTimezone"] == "America/Los_Angeles"


def test_user_timezone_falls_back_to_client_info_entity() -> None:
    exchange = converse(
        message("q", client_info_timezone="Asia/Tokyo"), json_ok(answer())
    )
    assert exchange.requests[0]["context"]["userTimezone"] == "Asia/Tokyo"


def test_unknown_timezone_falls_back_to_the_default() -> None:
    exchange = converse(
        message("q", local_timezone="Mars/Olympus_Mons"), json_ok(answer())
    )
    assert exchange.requests[0]["context"]["userTimezone"] == "Asia/Singapore"


def test_application_is_fixed_from_config_not_from_the_message() -> None:
    exchange = converse(message("show me application Other rejects"), json_ok(answer()))
    assert exchange.requests[0]["context"]["defaultApplication"] == "Magic"


def _error_card_text(handler: object) -> str:
    exchange = converse(message("q"), handler)  # type: ignore[arg-type]
    card = exchange.card
    assert "actions" not in card
    return " ".join(texts(card))


def test_disabled_nl_gets_a_clear_card() -> None:
    text = _error_card_text(lambda _r: httpx.Response(503, json={"error": {}}))
    assert "currently disabled" in text


def test_bad_request_gets_a_rephrase_card() -> None:
    assert "rephras" in _error_card_text(lambda _r: httpx.Response(422, json={}))


def test_server_error_says_the_service_is_unreachable_without_internals() -> None:
    text = _error_card_text(
        lambda _r: httpx.Response(500, text="Traceback (most recent call last)")
    )
    assert "couldn't reach the telemetry service" in text
    assert "Traceback" not in text


def test_timeout_gets_a_try_again_card() -> None:
    def boom(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    assert "took too long" in _error_card_text(boom)


def test_connection_failure_hides_the_exception_text() -> None:
    def boom(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("secret-host:1234 refused")

    text = _error_card_text(boom)
    assert "couldn't reach the telemetry service" in text
    assert "secret-host" not in text


def test_unrecognised_backend_body_is_treated_as_unavailable() -> None:
    text = _error_card_text(lambda _r: httpx.Response(200, json={"unexpected": True}))
    assert "couldn't reach the telemetry service" in text


def test_gateway_timeout_gets_the_try_again_card() -> None:
    assert "took too long" in _error_card_text(lambda _r: httpx.Response(504))


def test_unexpected_failure_still_replies_with_an_error_card() -> None:
    def boom(_request: httpx.Request) -> httpx.Response:
        raise RuntimeError("secret-internal-detail")

    exchange = converse(message("q"), boom)
    text = " ".join(texts(exchange.card))
    assert "couldn't reach the telemetry service" in text
    assert "secret-internal-detail" not in text


def test_list_markers_and_image_syntax_in_backend_text_are_neutralised() -> None:
    response = answer(
        text="1. first\n- second\n+ third ![x](http://evil/p.png)",
        caveats=["- injected bullet"],
    )
    exchange = converse(message("q"), json_ok(response))

    rendered = "\n".join(texts(exchange.card))
    assert "1\\. first" in rendered
    assert "\n\\- second" in rendered
    assert "\n\\+ third" in rendered
    assert "\\!\\[x\\]" in rendered
    assert "• - injected bullet" in rendered  # mid-line, so not a list item


def test_unspecified_dimension_values_are_not_shown_as_labels() -> None:
    mixed = QueryGroup(
        dimensions={"rejectReason": "unspecified", "instanceId": "magic-prod-01"},
        counters={"orders_rejected": 3},
    )
    nothing = QueryGroup(
        dimensions={"rejectReason": "unspecified", "instanceId": "unspecified"},
        counters={"orders_rejected": 9},
    )
    exchange = converse(message("q"), json_ok(answer(groups=[mixed, nothing])))

    body_text = " ".join(texts(exchange.card))
    assert "unspecified" not in body_text
    assert "magic-prod-01" in body_text
    assert "All" in body_text


def test_the_range_is_shown_in_the_users_timezone() -> None:
    exchange = converse(
        message("q", local_timezone="America/Los_Angeles"), json_ok(answer())
    )
    assert "Range: 2026-10-21 07:00 to 2026-10-21 07:30 UTC-7" in " ".join(
        texts(exchange.card)
    )


def test_a_half_hour_offset_is_labelled_with_its_minutes() -> None:
    exchange = converse(message("q", local_timezone="Asia/Kolkata"), json_ok(answer()))
    assert "UTC+5:30" in " ".join(texts(exchange.card))


def test_card_sections_follow_the_answer_order() -> None:
    """FR-NLQ-015: the number, then the breakdown, then an open alert, then caveats."""
    response = answer(
        groups=[group("OrderExceedsLimit", orders_rejected=35)],
        citations=[NlCitation(type="alert", alert_id="a-1")],
        caveats=["Using default time range of last 30m."],
    )
    body = converse(message("q"), json_ok(response)).card["body"]

    def position(predicate: object) -> int:
        return next(i for i, item in enumerate(body) if predicate(item))  # type: ignore[operator]

    headline = position(lambda i: i["type"] == "TextBlock" and i["size"] == "Large")
    breakdown = position(lambda i: i["type"] == "ColumnSet")
    alert = position(lambda i: i.get("style") == "attention")
    caveats = position(lambda i: "default time range" in " ".join(texts(i)))
    assert headline == 0
    assert headline < breakdown < alert < caveats
