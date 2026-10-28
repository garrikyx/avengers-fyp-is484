"""LLM slot-filling protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

from telemetry_shared.models.nl_query import IntentId

# The model's answer when the question is not about telemetry (FR-NLQ-030).
NO_INTENT: Literal["none"] = "none"


@dataclass(frozen=True, slots=True)
class LlmSlotResult:
    intent: IntentId | Literal["none"]
    time_range: object | None = None
    filters: dict[str, str | list[str]] | None = None
    group_by: list[str] | None = None
    metrics: list[str] | None = None
    series: bool | None = None
    step: str | None = None
    percentiles: dict[str, list[int]] | None = None
    # Untrusted conversational text; only used when intent is NO_INTENT and only
    # after `reply_guard.guard_reply` accepts it.
    reply: str | None = None


class LlmSlotFillError(Exception):
    """Structured slot fill failed or timed out."""


class LlmUnavailableError(LlmSlotFillError):
    """The model could not be reached (connection, HTTP status, transport timeout),
    as opposed to answering with something unusable."""


class LlmSlotFiller(Protocol):
    async def fill_slots(
        self,
        question: str,
        *,
        catalogue_summary: str,
        schema_json: str,
    ) -> LlmSlotResult: ...


@runtime_checkable
class ManagedLlmSlotFiller(LlmSlotFiller, Protocol):
    """A filler that owns network resources: warm it at startup, close it at exit."""

    async def warm_up(self) -> None: ...

    async def aclose(self) -> None: ...
