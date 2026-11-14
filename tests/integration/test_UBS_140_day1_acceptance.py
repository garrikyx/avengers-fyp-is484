"""UBS-140 / spec 000 §7 #1/#4: real log-to-query acceptance evidence."""

import asyncio

import pytest

from scripts.day1_acceptance import Report, run_acceptance


@pytest.fixture(scope="module")
def acceptance(tmp_path_factory: pytest.TempPathFactory) -> Report:
    return asyncio.run(
        run_acceptance(
            tmp_path_factory.mktemp("ubs140"), rate=5000, outage=3, bucket_seconds=1
        )
    )


def test_reject_bursts_visible_within_five_seconds(acceptance: Report) -> None:
    # Spec 000 §7 #1 / FR-MET-024: Day-1 acceptance profile.
    assert len(acceptance.visibility_seconds) == 3
    assert all(v is not None and v <= 5 for v in acceptance.visibility_seconds)


def test_FR_TST_004_NFR_REL_002_003_rotation_and_outage(acceptance: Report) -> None:
    assert acceptance.rotation_events >= 1
    assert acceptance.failed_publish_attempts >= 1
    assert acceptance.outage_ingested_lines > 0
    assert acceptance.signed_callbacks_during_outage >= 1


def test_rotation_outage_counts_match_ground_truth(acceptance: Report) -> None:
    # NFR-REL-002: exact counts, with no arbitrary loss tolerance.
    assert acceptance.pre_restart_missing_orders == 0
    assert acceptance.pre_restart_missing_rejections == 0


def test_NFR_REL_004_restart_resumes_within_five_seconds(acceptance: Report) -> None:
    assert acceptance.restart_resume_seconds is not None
    assert acceptance.restart_resume_seconds <= 5


def test_NFR_REL_004_restart_is_marked(acceptance: Report) -> None:
    assert acceptance.restarted_snapshots > 0


def test_restart_counts_match_ground_truth(acceptance: Report) -> None:
    assert acceptance.missing_orders == 0
    assert acceptance.excess_orders == 0
    assert acceptance.queried_orders == acceptance.queried_rejections
