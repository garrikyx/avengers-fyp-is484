"""LLM slot-filling fallback (FR-NLQ-007)."""

from telemetry_backend.nl.llm.mock import MockLlmSlotFiller
from telemetry_backend.nl.llm.protocol import (
    LlmSlotFiller,
    LlmSlotFillError,
    LlmSlotResult,
)

__all__ = [
    "LlmSlotFiller",
    "LlmSlotFillError",
    "LlmSlotResult",
    "MockLlmSlotFiller",
]
