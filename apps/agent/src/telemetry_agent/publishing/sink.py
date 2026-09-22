"""UBS-103: the swappable Publisher transport boundary (spec 002 §6).

Mirrors `callbacks/sink.py`'s `Protocol`-behind-a-boundary shape: the
Publisher only ever calls `sink.send(...)` and reads back a
`PublishResult` — a future transport swap (ADR 0003's reversal
conditions, e.g. gRPC) is a new class with a matching `send()`, not a
rewrite of the orchestrator. Bearer-token auth here, not
`callbacks/sink.py`'s HMAC signing — the backend contract is simpler
(spec 007 §1: `Authorization: Bearer <agent token>`).
"""

from __future__ import annotations

import gzip
import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

import httpx

_RESPONSE_SNIPPET_LIMIT = 200


@dataclass(frozen=True, slots=True)
class PublishResult:
    """Outcome of one publish attempt. `status_code` is `None` on a
    transport error (the request never reached the backend)."""

    status_code: int | None
    latency_ms: float
    error_class: str | None = None
    response_snippet: str = ""
    retry_after_seconds: float | None = None


class PublishSink(Protocol):
    """The transport boundary. `HttpsPublishSink` is the Day-1 default
    (ADR 0003); `DryRunPublishSink` stands in while there's no endpoint
    to send to yet.
    """

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> PublishResult: ...


def _maybe_gzip(body: bytes, threshold: int) -> tuple[bytes, bool]:
    """`FR-PUB-002`: gzip above `compress_threshold`. `mtime=0` makes the
    compressed bytes deterministic, which is useful for tests.
    """
    if len(body) <= threshold:
        return body, False
    return gzip.compress(body, mtime=0), True


def _parse_retry_after(headers: httpx.Headers) -> float | None:
    header = headers.get("Retry-After")
    if header is None:
        return None
    try:
        return float(header)
    except ValueError:
        return None


class HttpsPublishSink:
    """`FR-PUB-001`/`002`: HTTPS POST with a bearer token, gzip above
    `compress_threshold`. Rejects plain HTTP at construction unless
    `allow_insecure_endpoint=True` (local development only).
    """

    def __init__(
        self,
        endpoint: str,
        token: str,
        *,
        compress_threshold: int = 4096,
        connect_timeout_seconds: float = 3.0,
        total_timeout_seconds: float = 10.0,
        allow_insecure_endpoint: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not endpoint.startswith("https://") and not allow_insecure_endpoint:
            msg = f"publish endpoint must be https:// (got {endpoint!r})"
            raise ValueError(msg)
        self._endpoint = endpoint
        self._token = token
        self._compress_threshold = compress_threshold
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                total_timeout_seconds, connect=connect_timeout_seconds
            ),
            transport=transport,
        )

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> PublishResult:
        wire_body, gzipped = _maybe_gzip(body, self._compress_threshold)
        request_headers = dict(headers)
        request_headers["Authorization"] = f"Bearer {self._token}"
        if gzipped:
            request_headers["Content-Encoding"] = "gzip"

        start = time.monotonic()
        try:
            response = await self._client.post(
                self._endpoint, content=wire_body, headers=request_headers
            )
        except httpx.TimeoutException as exc:
            return PublishResult(
                status_code=None,
                latency_ms=(time.monotonic() - start) * 1000,
                error_class="timeout",
                response_snippet=str(exc)[:_RESPONSE_SNIPPET_LIMIT],
            )
        except httpx.TransportError as exc:
            return PublishResult(
                status_code=None,
                latency_ms=(time.monotonic() - start) * 1000,
                error_class="connect_error",
                response_snippet=str(exc)[:_RESPONSE_SNIPPET_LIMIT],
            )

        latency_ms = (time.monotonic() - start) * 1000
        return PublishResult(
            status_code=response.status_code,
            latency_ms=latency_ms,
            response_snippet=response.text[:_RESPONSE_SNIPPET_LIMIT],
            retry_after_seconds=_parse_retry_after(response.headers),
        )

    async def aclose(self) -> None:
        await self._client.aclose()


class DryRunPublishSink:
    """Log the intended publish, never open a socket. Use this while
    there's no real backend endpoint configured yet.
    """

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    async def send(
        self, *, body: bytes, headers: Mapping[str, str]
    ) -> PublishResult:
        self._logger.info("dry-run publish: bytes=%d", len(body))
        return PublishResult(
            status_code=202, latency_ms=0.0, response_snippet="dry-run"
        )
