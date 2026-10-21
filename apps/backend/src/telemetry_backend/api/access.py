"""Read-side access checkpoint for query surfaces (UBS-135; FR-NLQ-018).

Every read route the Teams bot, Copilot API plugin and MCP server call
depends on `read_access`. It is the single place Entra ID bearer validation
(scope `Telemetry.Read`, spec 007 §1) plugs in.

POC: spec 009 §3.3 defers custom backend authentication, so the actor is
always `unauthenticated` (NFR-SEC-011) and no token is required. A
surface-supplied identity is never treated as a verified actor.
"""

from __future__ import annotations

from fastapi import Request

UNAUTHENTICATED = "unauthenticated"


def read_access(request: Request) -> str:
    """Return the verified actor for this request."""
    return UNAUTHENTICATED


def rate_limit_key(request: Request, actor: str) -> str:
    """Per-user once authenticated; per request source until then (spec 008 §6)."""
    if actor != UNAUTHENTICATED:
        return actor
    return request.client.host if request.client else "unknown"
