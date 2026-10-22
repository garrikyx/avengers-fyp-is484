"""Bound ingestion bodies before JSON parsing, including gzip expansion."""

from __future__ import annotations

import zlib

from starlette.requests import Request


class IngestionBodyError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


async def read_ingestion_body(request: Request, max_bytes: int) -> bytes:
    encoding = request.headers.get("content-encoding", "identity").strip().lower()
    if encoding not in {"identity", "gzip"}:
        raise IngestionBodyError(415, "unsupported_encoding", "Use identity or gzip.")
    decoder = zlib.decompressobj(wbits=31) if encoding == "gzip" else None
    body = bytearray()
    wire_bytes = 0
    try:
        async for chunk in request.stream():
            wire_bytes += len(chunk)
            if wire_bytes > max_bytes:
                raise IngestionBodyError(
                    413, "body_too_large", "Ingestion body exceeds limit."
                )
            decoded = (
                decoder.decompress(chunk, max_bytes + 1 - len(body))
                if decoder
                else chunk
            )
            body.extend(decoded)
            if len(body) > max_bytes:
                raise IngestionBodyError(
                    413, "body_too_large", "Decoded body exceeds limit."
                )
        if decoder is not None and (not decoder.eof or decoder.unused_data):
            raise IngestionBodyError(400, "invalid_encoding", "Invalid gzip body.")
    except zlib.error:
        raise IngestionBodyError(
            400, "invalid_encoding", "Invalid gzip body."
        ) from None
    return bytes(body)
