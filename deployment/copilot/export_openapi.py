"""Write the Copilot API plugin's OpenAPI document (UBS-135; FR-NLQ-018).

The fallback Copilot path (spec 008 §6) gets only the read operations of
the backend's generated OpenAPI document; ingestion and probes are dropped,
so the plugin cannot call a mutating endpoint.

    uv run python deployment/copilot/export_openapi.py --server-url https://...
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from telemetry_backend.main import create_app

ALLOWED: dict[str, set[str]] = {
    "/telemetry/nl/query": {"post"},
    "/telemetry/query/metrics": {"post"},
    "/telemetry/alerts": {"get"},
    "/telemetry/alerts/{alert_id}": {"get"},
    "/telemetry/health/agents": {"get"},
    "/telemetry/health/agents/{agent_id}": {"get"},
}


def plugin_openapi(server_url: str) -> dict[str, Any]:
    spec = create_app().openapi()
    spec["paths"] = {
        path: {m: op for m, op in ops.items() if m in ALLOWED[path]}
        for path, ops in spec["paths"].items()
        if path in ALLOWED
    }
    spec["servers"] = [{"url": server_url}]
    return spec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-url", required=True)
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).with_name("openapi.json")
    )
    args = parser.parse_args()
    args.out.write_text(json.dumps(plugin_openapi(args.server_url), indent=2) + "\n")


if __name__ == "__main__":
    main()
