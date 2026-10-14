"""FR-QRY-005: `/readyz` probes the same StreamProcessor that ingestion
feeds. With two instances (one for the probe, one inside
`IngestionService`), the probe's store never received data and `/readyz`
stayed `warming` forever.
"""

import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from telemetry_backend.config import StreamProcessorConfig
from telemetry_backend.main import create_app
from telemetry_backend.services.ingestion import IngestionService
from telemetry_backend.services.stream_processor import StreamProcessor

AGENT = "magic-agent-sg-01"


def _batch_with_snapshot(now: datetime) -> dict[str, object]:
    bucket = now.replace(second=(now.second // 10) * 10, microsecond=0)
    return {
        "schemaVersion": 1,
        "batchId": str(uuid4()),
        "batchSeq": 1,
        "agentId": AGENT,
        "application": "Magic",
        "sentAtUtc": now.isoformat(),
        "snapshots": [
            {
                "schemaVersion": 1,
                "agentId": AGENT,
                "application": "Magic",
                "instanceId": "magic-prod-01",
                "bucketStartUtc": bucket.isoformat(),
                "bucketSeconds": 10,
                "series": [
                    {
                        "dimensions": {"session": "MAGIC->EXCH1", "symbol": "ABC"},
                        "counters": {"orders_submitted": "1"},
                    }
                ],
            }
        ],
        "events": [],
        "alerts": [],
    }


def _wait_for_status(client: TestClient, expected: int) -> int:
    # Ingestion merges on a background task, so give it a moment.
    deadline = time.monotonic() + 5
    code = client.get("/readyz").status_code
    while code != expected and time.monotonic() < deadline:
        time.sleep(0.05)
        code = client.get("/readyz").status_code
    return code


def test_readyz_turns_ready_once_ingested_data_reaches_the_shared_store() -> None:
    # Warmup window already elapsed, so data arriving is the only gate left.
    processor = StreamProcessor(
        StreamProcessorConfig(warmup_window_seconds=120),
        started_at=datetime.now(UTC) - timedelta(hours=1),
    )
    with TestClient(create_app(processor=processor)) as client:
        assert client.get("/readyz").status_code == 503

        response = client.post(
            "/telemetry/batch", json=_batch_with_snapshot(datetime.now(UTC))
        )
        assert response.status_code == 202

        assert _wait_for_status(client, 200) == 200
        assert client.get("/readyz").json() == {"status": "ready"}


def test_create_app_probes_the_supplied_services_own_processor() -> None:
    service = IngestionService()
    app = create_app(service)
    assert app.state.processor is service.stream_processor


def test_create_app_rejects_a_processor_the_service_does_not_feed() -> None:
    with pytest.raises(ValueError, match="stream_processor"):
        create_app(IngestionService(), StreamProcessor(StreamProcessorConfig()))
