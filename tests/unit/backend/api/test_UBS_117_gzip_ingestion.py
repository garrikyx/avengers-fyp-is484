"""FR-PUB-002 / FR-ING-008: compressed real batches and bounded decoding."""

import gzip
import json

import pytest
from fastapi.testclient import TestClient
from telemetry_backend.config import (
    BackendHealthConfig,
    IngestGuardConfig,
    load_backend_health_config,
)
from telemetry_backend.deps import AppDeps
from telemetry_backend.main import create_app

from tests.unit.agent.publishing.publish_fixtures import make_event


def client(limit=8_388_608):
    return TestClient(
        create_app(
            deps=AppDeps(
                config=BackendHealthConfig(
                    ingest=IngestGuardConfig(max_body_bytes=limit)
                )
            )
        )
    )


def test_compressed_events_are_accepted_with_existing_contract():
    body = json.dumps(
        {"events": [make_event().model_dump(mode="json", by_alias=True)]}
    ).encode()
    with client() as api:
        response = api.post(
            "/telemetry/events",
            content=gzip.compress(body),
            headers={"Content-Type": "application/json", "Content-Encoding": "gzip"},
        )
    assert response.status_code == 202


@pytest.mark.parametrize(
    "body", [b"bad gzip PRIVATE_SENTINEL", gzip.compress(b"{}")[:-4]]
)
def test_corrupt_compressed_body_returns_safe_error(body):
    with client() as api:
        response = api.post(
            "/telemetry/batch",
            content=body,
            headers={"Content-Encoding": "gzip", "X-Request-Id": "test-id"},
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_encoding"
    assert response.headers["X-Request-Id"] == "test-id"
    assert "PRIVATE_SENTINEL" not in response.text


@pytest.mark.parametrize("compress", [False, True])
def test_wire_and_expanded_body_sizes_are_bounded(compress):
    body = b"x" * 1001
    with client(limit=1000) as api:
        response = api.post(
            "/telemetry/batch",
            content=gzip.compress(body) if compress else body,
            headers={"Content-Encoding": "gzip" if compress else "identity"},
        )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "body_too_large"


def test_body_limit_is_loaded_from_existing_ingest_config(tmp_path):
    path = tmp_path / "backend.yaml"
    path.write_text("ingest:\n  maxBodyBytes: 1234\n")
    assert load_backend_health_config(path).ingest.max_body_bytes == 1234
