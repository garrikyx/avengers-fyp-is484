"""Intent catalogue HTTP payload (spec 007 §6.2)."""

from __future__ import annotations

from telemetry_shared.models.nl_query import IntentCatalogueEntry, NlIntentsResponse

from telemetry_backend.nl.catalogue import INTENT_DEFINITIONS, SUPPORTED_INTENTS


def build_intents_response() -> NlIntentsResponse:
    entries: list[IntentCatalogueEntry] = []
    for intent in SUPPORTED_INTENTS:
        definition = INTENT_DEFINITIONS[intent]
        entries.append(
            IntentCatalogueEntry(
                intent=intent,
                description=definition.description,
                example_questions=list(definition.example_questions),
                required_slots=list(definition.required_slots),
                optional_slots=list(definition.optional_slots),
            )
        )
    return NlIntentsResponse(intents=entries)


def catalogue_summary_for_prompt() -> str:
    """One short line per intent: small local models answer faster on short prompts,
    and the compiler fills metric and groupBy defaults from the catalogue."""
    lines: list[str] = []
    for intent in SUPPORTED_INTENTS:
        definition = INTENT_DEFINITIONS[intent]
        lines.append(
            f"- {intent}: {definition.description} "
            f'e.g. "{definition.example_questions[0]}"'
        )
    return "\n".join(lines)
