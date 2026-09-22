from pathlib import Path

from simulator.mock_logger import rotate_if_needed


def test_rotation_retains_configured_number_of_archives(tmp_path: Path) -> None:
    """The newest archive is .1 and only the oldest is removed."""
    active_path = tmp_path / "Application.log"

    for generation in range(1, 5):
        active_path.write_text(f"generation-{generation}\n")
        assert rotate_if_needed(active_path, max_bytes=1, keep_rotated_files=3)

    assert not active_path.exists()
    assert (tmp_path / "Application.log.1").read_text() == "generation-4\n"
    assert (tmp_path / "Application.log.2").read_text() == "generation-3\n"
    assert (tmp_path / "Application.log.3").read_text() == "generation-2\n"
    assert not (tmp_path / "Application.log.4").exists()


def test_rotation_requires_at_least_one_archive(tmp_path: Path) -> None:
    active_path = tmp_path / "Application.log"
    active_path.write_text("line\n")

    try:
        rotate_if_needed(active_path, max_bytes=1, keep_rotated_files=0)
    except ValueError as error:
        assert str(error) == "keep_rotated_files must be at least 1"
    else:
        raise AssertionError("Expected invalid retention count to fail")
