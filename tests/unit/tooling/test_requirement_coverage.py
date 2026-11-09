"""Tests for scripts/requirement_coverage.py (UBS-146, FR-TST-001)."""

from pathlib import Path

from scripts import requirement_coverage as rc


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_FR_TST_001_collects_ids_defined_in_each_spec(tmp_path: Path) -> None:
    _write(
        tmp_path / "specs" / "002-agent.md",
        "`FR-PIP-001`: Blocking enqueue.\n"
        "- `FR-PIP-002`: Queue sizing.\n"
        "| `FR-PIP-003` | Worker pool |\n"
        "| `NFR-PERF-001` | CPU budget | Load test |\n"
        "Cross-reference only: see `FR-PRS-003`.\n",
    )
    _write(tmp_path / "specs" / "003-fix-parsing.md", "`FR-PRS-003`: Registry.\n")

    found = rc.collect_requirements(tmp_path / "specs")

    assert found == {
        "002-agent": ["FR-PIP-001", "FR-PIP-002", "FR-PIP-003", "NFR-PERF-001"],
        "003-fix-parsing": ["FR-PRS-003"],
    }


def test_FR_TST_001_accepts_hyphen_and_underscore_reference_styles(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "tests" / "test_a.py", "# FR-PRS-021 hashing\n")
    _write(tmp_path / "tests" / "test_FR_PRS_022_normalize.py", "def test_x(): ...\n")
    _write(tmp_path / "tests" / "test_b.py", "def test_NFR_SEC_002_allowlist(): ...\n")

    refs = rc.collect_references(tmp_path / "tests")

    assert {"FR-PRS-021", "FR-PRS-022", "NFR-SEC-002"} <= refs


def test_FR_TST_001_expands_short_ranges_but_not_status_codes(tmp_path: Path) -> None:
    _write(
        tmp_path / "tests" / "test_FR_PRS_040_043_binary.py",
        "# also FR-RUL-004–006 and FR_CBK_006_408\n",
    )

    refs = rc.collect_references(tmp_path / "tests")

    assert {"FR-PRS-040", "FR-PRS-041", "FR-PRS-042", "FR-PRS-043"} <= refs
    assert {"FR-RUL-004", "FR-RUL-005", "FR-RUL-006"} <= refs
    assert "FR-CBK-007" not in refs  # 006..408 is a status code, not a range


def test_FR_TST_001_report_lists_covered_and_uncovered_per_spec() -> None:
    report = rc.build_report(
        {"002-agent": ["FR-PIP-001", "FR-PIP-002"], "009-nfr": ["NFR-SEC-001"]},
        {"FR-PIP-001", "NFR-SEC-001"},
    )

    assert "002-agent: 1/2 covered" in report
    assert "uncovered: FR-PIP-002" in report
    assert "covered: FR-PIP-001" in report
    assert "009-nfr: 1/1 covered" in report
    assert "Total: 2/3 covered, 1 uncovered" in report


def test_FR_TST_001_main_is_report_only_unless_asked_to_fail(
    tmp_path: Path, capsys: object
) -> None:
    _write(tmp_path / "specs" / "002-agent.md", "`FR-PIP-001`: Blocking enqueue.\n")
    _write(tmp_path / "tests" / "test_empty.py", "")
    args = ["--specs", str(tmp_path / "specs"), "--tests", str(tmp_path / "tests")]

    assert rc.main(args) == 0
    assert rc.main([*args, "--fail-on-uncovered"]) == 1
