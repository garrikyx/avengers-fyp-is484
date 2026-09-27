"""Lightweight in-process counters for callback self-observability
(`FR-CBK-009`): delivery outcomes, failures.

Moved to `telemetry_agent.common.self_metrics` (UBS-104) once the Backend
Publisher needed the identical counter registry -- re-exported here so
existing imports keep working unchanged.
"""

from __future__ import annotations

from telemetry_agent.common.self_metrics import CounterRegistry

__all__ = ["CounterRegistry"]
