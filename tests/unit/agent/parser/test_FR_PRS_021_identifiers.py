"""FR-PRS-021 identifier hashing tests."""

from __future__ import annotations

import re

import pytest

from telemetry_agent.parser.fix.fields import extract_allowlisted_fields
from telemetry_agent.parser.fix.identifiers import hash_identifier, load_hash_key

_HEX16 = re.compile(r"^[0-9a-f]{16}$")


def test_FR_PRS_021_same_input_and_key_is_stable() -> None:
    assert hash_identifier("CLORD-1", b"key-a") == hash_identifier("CLORD-1", b"key-a")


def test_FR_PRS_021_different_input_produces_different_hash() -> None:
    assert hash_identifier("CLORD-1", b"key-a") != hash_identifier("CLORD-2", b"key-a")


def test_FR_PRS_021_different_key_produces_different_hash() -> None:
    assert hash_identifier("CLORD-1", b"key-a") != hash_identifier("CLORD-1", b"key-b")


def test_FR_PRS_021_output_is_16_lowercase_hex_chars() -> None:
    assert _HEX16.match(hash_identifier("CLORD-1", b"key-a"))


def test_FR_PRS_021_plaintext_never_appears_in_hash() -> None:
    raw = "UNHASHED_CLORDID_PLAINTEXT"
    hashed = hash_identifier(raw, b"key-a")
    assert raw not in hashed


def test_FR_PRS_021_load_hash_key_reads_env_var() -> None:
    key = load_hash_key({"MAGIC_TELEMETRY_ID_HASH_KEY": "devkey"})
    assert key == b"devkey"


def test_FR_PRS_021_load_hash_key_fails_fast_when_unset() -> None:
    with pytest.raises(RuntimeError):
        load_hash_key({})


def test_FR_PRS_021_load_hash_key_fails_fast_when_empty() -> None:
    with pytest.raises(RuntimeError):
        load_hash_key({"MAGIC_TELEMETRY_ID_HASH_KEY": ""})


def test_FR_PRS_021_extracted_fields_carry_hashes_not_plaintext() -> None:
    raw_fields = {
        "35": "8",
        "11": "UNHASHED_TAG11_CLORDID",
        "41": "UNHASHED_TAG41_ORIGCLORDID",
        "37": "UNHASHED_TAG37_ORDERID",
        "17": "UNHASHED_TAG17_EXECID",
    }
    extracted = extract_allowlisted_fields(raw_fields, hash_key=b"key-a")

    assert extracted.cl_ord_id_hash == hash_identifier("UNHASHED_TAG11_CLORDID", b"key-a")
    assert extracted.orig_cl_ord_id_hash == hash_identifier("UNHASHED_TAG41_ORIGCLORDID", b"key-a")
    assert extracted.order_id_hash == hash_identifier("UNHASHED_TAG37_ORDERID", b"key-a")
    assert extracted.exec_id_hash == hash_identifier("UNHASHED_TAG17_EXECID", b"key-a")

    for value in (
        extracted.cl_ord_id_hash,
        extracted.orig_cl_ord_id_hash,
        extracted.order_id_hash,
        extracted.exec_id_hash,
    ):
        assert value is not None
        assert "UNHASHED" not in value


def test_FR_PRS_021_no_hash_key_omits_identifiers_rather_than_leaking_plaintext() -> None:
    raw_fields = {"11": "UNHASHED_TAG11_CLORDID"}
    extracted = extract_allowlisted_fields(raw_fields, hash_key=None)
    assert extracted.cl_ord_id_hash is None
