"""FR-CBK-005 request-signing tests."""

from __future__ import annotations

import re

import pytest
from telemetry_agent.callbacks.signing import load_callback_secret, sign

_SIGNATURE_RE = re.compile(r"^v1=[0-9a-f]{64}$")


def test_FR_CBK_005_signature_format() -> None:
    signature = sign(b"secret", "1700000000", b'{"alertId":"a1"}')
    assert _SIGNATURE_RE.match(signature)


def test_FR_CBK_005_same_input_is_stable() -> None:
    body = b'{"alertId":"a1"}'
    assert sign(b"secret", "1700000000", body) == sign(b"secret", "1700000000", body)


def test_FR_CBK_005_different_body_produces_different_signature() -> None:
    sig_a = sign(b"secret", "1700000000", b'{"alertId":"a1"}')
    sig_b = sign(b"secret", "1700000000", b'{"alertId":"a2"}')
    assert sig_a != sig_b


def test_FR_CBK_005_different_timestamp_produces_different_signature() -> None:
    body = b'{"alertId":"a1"}'
    sig_a = sign(b"secret", "1700000000", body)
    sig_b = sign(b"secret", "1700000001", body)
    assert sig_a != sig_b


def test_FR_CBK_005_different_secret_produces_different_signature() -> None:
    body = b'{"alertId":"a1"}'
    sig_a = sign(b"secret-a", "1700000000", body)
    sig_b = sign(b"secret-b", "1700000000", body)
    assert sig_a != sig_b


def test_FR_CBK_005_load_callback_secret_reads_env_var() -> None:
    secret = load_callback_secret({"MAGIC_TELEMETRY_CALLBACK_SECRET": "devsecret"})
    assert secret == b"devsecret"


def test_FR_CBK_005_load_callback_secret_fails_fast_when_unset() -> None:
    with pytest.raises(RuntimeError):
        load_callback_secret({})


def test_FR_CBK_005_load_callback_secret_fails_fast_when_empty() -> None:
    with pytest.raises(RuntimeError):
        load_callback_secret({"MAGIC_TELEMETRY_CALLBACK_SECRET": ""})
