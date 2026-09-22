"""FR-CBK-001/011: the swappable Callback transport boundary (spec 005 §3).

Magic's real auth/transport isn't confirmed yet (`Q-2` in
docs/plan/open-questions.md), so HTTPS is the Day-1 default behind this
`Protocol`, not a hardcoded assumption. `CallbackDispatcher` only ever calls
`sink.send(...)` and reads back a `CallbackResult` — it never knows HTTPS is
involved, so a future transport (e.g. a message queue) is a new class with
a matching `send()` method, not a rewrite of the dispatcher.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

import httpx

_RESPONSE_SNIPPET_LIMIT = 200


@dataclass(frozen=True, slots=True)
class CallbackResult:
    """Outcome of one delivery attempt (`FR-CBK-009`).

    `status_code` is `None` on a transport error (the request never reached
    Magic, so there's no HTTP status to report).
    """

    status_code: int | None
    latency_ms: float
    error_class: str | None = None
    response_snippet: str = ""
    retry_after_seconds: float | None = None


class CallbackSink(Protocol):
    """The transport boundary. `HttpsCallbackSink` is the Day-1 default;
    `DryRunCallbackSink` stands in while there's no real Magic endpoint.
    """

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> CallbackResult: ...


class HttpsCallbackSink:
    """`FR-CBK-001`: HTTPS POST to the configured Magic endpoint. Rejects
    plain HTTP at construction unless `allow_insecure_callback=True`
    (local development only).
    """

    def __init__(
        self,
        endpoint: str,
        *,
        connect_timeout_seconds: float = 3.0,
        total_timeout_seconds: float = 10.0,
        allow_insecure_callback: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not endpoint.startswith("https://") and not allow_insecure_callback:
            msg = f"callback endpoint must be https:// (got {endpoint!r})"
            raise ValueError(msg)
        self._endpoint = endpoint
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                total_timeout_seconds, connect=connect_timeout_seconds
            ),
            transport=transport,
        )

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> CallbackResult:
        start = time.monotonic()
        try:
            response = await self._client.post(
                self._endpoint, content=body, headers=headers
            )
        except httpx.TimeoutException as exc:
            return CallbackResult(
                status_code=None,
                latency_ms=(time.monotonic() - start) * 1000,
                error_class="timeout",
                response_snippet=str(exc)[:_RESPONSE_SNIPPET_LIMIT],
            )
        except httpx.TransportError as exc:
            return CallbackResult(
                status_code=None,
                latency_ms=(time.monotonic() - start) * 1000,
                error_class="connect_error",
                response_snippet=str(exc)[:_RESPONSE_SNIPPET_LIMIT],
            )

        latency_ms = (time.monotonic() - start) * 1000
        retry_after_seconds = None
        retry_after_header = response.headers.get("Retry-After")
        if retry_after_header is not None:
            try:
                retry_after_seconds = float(retry_after_header)
            except ValueError:
                retry_after_seconds = None
        return CallbackResult(
            status_code=response.status_code,
            latency_ms=latency_ms,
            response_snippet=response.text[:_RESPONSE_SNIPPET_LIMIT],
            retry_after_seconds=retry_after_seconds,
        )

    async def aclose(self) -> None:
        await self._client.aclose()


class DryRunCallbackSink:
    """`FR-CBK-011`: log the intended delivery, never open a socket. Use
    this while there's no real Magic endpoint yet.
    """

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> CallbackResult:
        delivery_id = headers.get("X-Telemetry-Delivery-Id", "unknown")
        self._logger.info(
            "dry-run callback: delivery_id=%s bytes=%d body=%s",
            delivery_id,
            len(body),
            body.decode("utf-8", errors="replace"),
        )
        return CallbackResult(
            status_code=200, latency_ms=0.0, response_snippet="dry-run"
        )
