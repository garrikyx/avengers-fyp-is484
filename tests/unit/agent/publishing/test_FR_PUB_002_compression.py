from __future__ import annotations

import asyncio
import gzip

import httpx
import pytest
from telemetry_agent.publishing.sink import HttpsPublishSink, _maybe_gzip


def test_body_under_threshold_is_not_compressed() -> None:
    body = b"x" * 100
    wire_body, gzipped = _maybe_gzip(body, threshold=4096)

    assert gzipped is False
    assert wire_body == body


def test_body_over_threshold_is_gzipped_and_round_trips() -> None:
    body = b"x" * 5000
    wire_body, gzipped = _maybe_gzip(body, threshold=4096)

    assert gzipped is True
    assert wire_body != body
    assert gzip.decompress(wire_body) == body


def test_sink_sets_content_encoding_header_when_gzipped() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["content"] = request.content
        return httpx.Response(202, json={"status": "accepted"})

    sink = HttpsPublishSink(
        "https://backend.example/telemetry/batch",
        "token-123",
        compress_threshold=10,
        transport=httpx.MockTransport(handler),
    )

    body = b"y" * 1000
    result = asyncio.run(
        sink.send(body=body, headers={"Content-Type": "application/json"})
    )

    assert result.status_code == 202
    assert captured["headers"]["content-encoding"] == "gzip"  # type: ignore[index]
    assert captured["headers"]["authorization"] == "Bearer token-123"  # type: ignore[index]
    assert gzip.decompress(captured["content"]) == body  # type: ignore[arg-type]


def test_sink_does_not_gzip_small_bodies() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        return httpx.Response(202, json={"status": "accepted"})

    sink = HttpsPublishSink(
        "https://backend.example/telemetry/batch",
        "token-123",
        compress_threshold=4096,
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(sink.send(body=b"tiny", headers={}))

    assert "content-encoding" not in captured["headers"]  # type: ignore[operator]


def test_rejects_plain_http_by_default() -> None:
    with pytest.raises(ValueError):
        HttpsPublishSink("http://backend.example/telemetry/batch", "token")


def test_allows_plain_http_when_explicitly_opted_in() -> None:
    HttpsPublishSink(
        "http://backend.example/telemetry/batch",
        "token",
        allow_insecure_endpoint=True,
    )
