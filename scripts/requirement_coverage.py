"""Report which spec requirement IDs have a referencing test (FR-TST-001, UBS-146).

Collects every `FR-*` / `NFR-*` ID *defined* in `docs/specs/` (a definition starts a
line, a bullet or a table row: `` `FR-X-001`: ... `` or `` | `FR-X-001` | ... ``) and
looks for it anywhere under `tests/`, in file names and file contents. Both
`FR-PRS-021` and `FR_PRS_021` count, and short ranges such as `FR-PRS-040–043` or
`FR_PRS_040_043` cover every ID in the range.

Report-only by default; pass `--fail-on-uncovered` to turn it into a gate.

    uv run python scripts/requirement_coverage.py
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_ID = r"(?P<prefix>N?FR)[-_](?P<area>[A-Z]+)[-_](?P<num>\d{3})"
_DEFINITION = re.compile(rf"^\s*(?:[-*]\s+)?(?:\|\s*)?`{_ID}`\s*(?::|\|)", re.MULTILINE)
# An ID optionally followed by "-/_/–/— NNN" (a range end).
_REFERENCE = re.compile(rf"(?<![A-Za-z0-9]){_ID}(?:[-_–—](?P<end>\d{{3}}))?(?!\d)")

# Longer spans are treated as unrelated numbers (e.g. FR_CBK_006_408: an HTTP status).
_MAX_RANGE_SPAN = 20


def collect_requirements(specs_dir: Path) -> dict[str, list[str]]:
    """Map each spec file stem to the requirement IDs it defines, in order."""
    found: dict[str, list[str]] = {}
    for spec in sorted(specs_dir.glob("*.md")):
        ids: list[str] = []
        for match in _DEFINITION.finditer(spec.read_text(encoding="utf-8")):
            req = f"{match['prefix']}-{match['area']}-{match['num']}"
            if req not in ids:
                ids.append(req)
        if ids:
            found[spec.stem] = ids
    return found


def _expand(text: str) -> set[str]:
    refs: set[str] = set()
    for match in _REFERENCE.finditer(text):
        prefix, area, start = match["prefix"], match["area"], int(match["num"])
        refs.add(f"{prefix}-{area}-{start:03d}")
        if match["end"] is not None:
            end = int(match["end"])
            if start < end <= start + _MAX_RANGE_SPAN:
                refs.update(f"{prefix}-{area}-{n:03d}" for n in range(start, end + 1))
    return refs


def collect_references(tests_dir: Path) -> set[str]:
    """Every requirement ID mentioned in a test file's name or contents."""
    refs: set[str] = set()
    for path in sorted(tests_dir.rglob("*.py")):
        refs |= _expand(path.name)
        refs |= _expand(path.read_text(encoding="utf-8", errors="replace"))
    return refs


def build_report(requirements: dict[str, list[str]], references: set[str]) -> str:
    lines: list[str] = []
    for spec, ids in requirements.items():
        covered = [i for i in ids if i in references]
        uncovered = [i for i in ids if i not in references]
        lines.append(f"{spec}: {len(covered)}/{len(ids)} covered")
        lines.append(f"  covered: {', '.join(covered) or '-'}")
        lines.append(f"  uncovered: {', '.join(uncovered) or '-'}")
    # An ID defined in more than one spec counts once in the total.
    unique = {i for ids in requirements.values() for i in ids}
    covered_total = len(unique & references)
    lines.append("")
    lines.append(
        f"Total: {covered_total}/{len(unique)} covered, "
        f"{len(unique) - covered_total} uncovered"
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--specs", type=Path, default=ROOT / "docs" / "specs")
    parser.add_argument("--tests", type=Path, default=ROOT / "tests")
    parser.add_argument(
        "--fail-on-uncovered",
        action="store_true",
        help="exit 1 if any requirement ID has no referencing test",
    )
    args = parser.parse_args(argv)

    requirements = collect_requirements(args.specs)
    references = collect_references(args.tests)
    print(build_report(requirements, references))

    uncovered = any(i not in references for ids in requirements.values() for i in ids)
    return 1 if args.fail_on_uncovered and uncovered else 0


if __name__ == "__main__":
    sys.exit(main())
