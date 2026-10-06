"""FR-MET-030 / FR-ING-007: one shared dimension vocabulary for agent and
backend, so the two sides cannot drift."""

from telemetry_backend.services.ingestion import ALLOWED_DIMENSION_KEYS
from telemetry_shared.models.ingestion import WIRE_DIMENSION_KEYS


def test_backend_allowlist_is_the_shared_vocabulary() -> None:
    assert ALLOWED_DIMENSION_KEYS is WIRE_DIMENSION_KEYS
