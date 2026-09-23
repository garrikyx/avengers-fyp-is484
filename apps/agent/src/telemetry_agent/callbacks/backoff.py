"""FR-CBK-004: exponential backoff with jitter for callback retries.

Moved to `telemetry_agent.common.backoff` (UBS-104) once the Backend
Publisher needed the identical retry math -- re-exported here so existing
imports keep working unchanged.
"""

from __future__ import annotations

from telemetry_agent.common.backoff import RetryPolicy

__all__ = ["RetryPolicy"]
