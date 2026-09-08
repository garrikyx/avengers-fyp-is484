"""FR-PRS-020 / NFR-SEC-002 / NFR-PERF-004 allowlisted field extraction tests."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

from telemetry_agent.parser.fix.fields import FixFields, extract_allowlisted_fields
from telemetry_agent.parser.fix.parser import FixParser
from telemetry_agent.parser.protocol import SourceMeta

_KEY = b"unit-test-key"


def test_FR_PRS_020_only_allowlisted_tags_extracted() -> None:
    fields = {"8": "FIX.4.2", "35": "D", "55": "GOOG", "54": "1"}
    extracted = extract_allowlisted_fields(fields, hash_key=_KEY)
    assert extracted.fix_version == "FIX.4.2"
    assert extracted.msg_type == "D"
    assert extracted.symbol == "GOOG"
    assert extracted.side == "1"


def test_FR_PRS_020_missing_tags_default_to_none() -> None:
    extracted = extract_allowlisted_fields({}, hash_key=_KEY)
    assert extracted.fix_version is None
    assert extracted.msg_type is None
    assert extracted.symbol is None


def test_FR_PRS_020_excluded_tags_never_appear_in_output() -> None:
    fields = {
        "8": "FIX.4.2",
        "35": "D",
        "44": "EXCLUDED_TAG44_PRICE",
        "31": "EXCLUDED_TAG31_LASTPX",
        "6": "EXCLUDED_TAG6_AVGPX",
        "1": "EXCLUDED_TAG1_ACCOUNT",
        "448": "EXCLUDED_TAG448_PARTYID",
        "447": "EXCLUDED_TAG447_PARTYIDSOURCE",
        "452": "EXCLUDED_TAG452_PARTYROLE",
        "9999": "EXCLUDED_TAG9999_UNKNOWN",
    }
    extracted = extract_allowlisted_fields(fields, hash_key=_KEY)
    rendered = repr(dataclasses.asdict(extracted))
    for excluded in (
        "EXCLUDED_TAG44_PRICE",
        "EXCLUDED_TAG31_LASTPX",
        "EXCLUDED_TAG6_AVGPX",
        "EXCLUDED_TAG1_ACCOUNT",
        "EXCLUDED_TAG448_PARTYID",
        "EXCLUDED_TAG447_PARTYIDSOURCE",
        "EXCLUDED_TAG452_PARTYROLE",
        "EXCLUDED_TAG9999_UNKNOWN",
    ):
        assert excluded not in rendered


def test_FR_PRS_020_fixed_struct_has_no_dict_no_map_allocation() -> None:
    """NFR-PERF-004: fixed slotted struct, not a dict, per parsed message."""
    extracted = extract_allowlisted_fields({"35": "D"}, hash_key=_KEY)
    assert not hasattr(extracted, "__dict__")
    assert FixFields.__slots__


def test_FR_PRS_020_end_to_end_excluded_tag_never_in_parse_result() -> None:
    line = (
        b"8=FIX.4.2|35=D|49=SENDER|56=TARGET|55=GOOG|54=1|"
        b"44=EXCLUDED_TAG44_PRICE|1=EXCLUDED_TAG1_ACCOUNT|"
        b"448=EXCLUDED_TAG448_PARTYID|10=000|"
    )
    parser = FixParser(hash_key=_KEY)
    meta = SourceMeta(
        instance_id="test",
        path="corpus",
        log_type="fix",
        read_at=datetime.now(tz=UTC),
    )
    result = parser.parse(line, meta)
    assert result.framed
    assert result.fields is not None
    rendered = repr(dataclasses.asdict(result.fields))
    assert "EXCLUDED_TAG44_PRICE" not in rendered
    assert "EXCLUDED_TAG1_ACCOUNT" not in rendered
    assert "EXCLUDED_TAG448_PARTYID" not in rendered
    assert result.fields.symbol == "GOOG"
