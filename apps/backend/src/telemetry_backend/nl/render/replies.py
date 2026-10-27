"""Templated conversational replies when no metrics answer applies (FR-NLQ-030).

Plain text: each surface escapes for its own destination (FR-NLQ-022).
"""

from __future__ import annotations

from telemetry_shared.models.nl_query import IntentId

from telemetry_backend.nl.catalogue import INTENT_DEFINITIONS

# One example per common intent, in the order users usually need them.
_SUGGESTION_INTENTS: tuple[IntentId, ...] = (
    "order_flow_summary",
    "rejection_summary",
    "latency_summary",
    "alert_status",
)


def suggested_questions() -> list[str]:
    return [
        INTENT_DEFINITIONS[intent].example_questions[0]
        for intent in _SUGGESTION_INTENTS
    ]


def greeting_message(application: str) -> str:
    return (
        f"Hi! I can answer questions about {application}'s telemetry: order flow, "
        "rejected orders, latency, FIX sessions, open alerts and agent health."
    )


def thanks_message(application: str) -> str:
    return f"You're welcome. Ask me anything else about {application}'s telemetry."


def help_message(application: str) -> str:
    return (
        f"I answer read-only questions about {application}'s telemetry. Ask about "
        "order flow, rejected orders, latency, FIX sessions, open alerts, agent "
        "health or parse errors, for a window such as the last 30 minutes or today."
    )


def out_of_scope_message(application: str) -> str:
    return (
        f"I can only answer questions about {application}'s telemetry. "
        "Try one of these questions."
    )


def llm_unavailable_message() -> str:
    return (
        "I'm having trouble understanding that right now. "
        "Try one of these questions, or rephrase yours."
    )


WEAK_RULE_MATCH_CAVEAT = (
    "Interpreted by keyword matching because the language model was unavailable; "
    "rephrase the question if this is not what you meant."
)
