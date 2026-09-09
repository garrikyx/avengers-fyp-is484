"""Applog signature template tests."""

from __future__ import annotations

from telemetry_agent.parser.applog.signatures import (
    SignatureMatcher,
    compile_signature_rules,
    resolve_label_template,
)


def test_dynamic_label_gr_disconnect() -> None:
    matcher = SignatureMatcher(
        compile_signature_rules([("%_connection_disconnected", r"(\w+) connection disconnected")])
    )
    label = matcher.match(b"07:52:15.027292 <413010> [F] VS_788: GR connection disconnected")
    assert label == "gr_connection_disconnected"


def test_dynamic_label_md_disconnect() -> None:
    matcher = SignatureMatcher(
        compile_signature_rules([("%_connection_disconnected", r"(\w+) connection disconnected")])
    )
    label = matcher.match(b"MD connection disconnected")
    assert label == "md_connection_disconnected"


def test_static_connect_timeout() -> None:
    matcher = SignatureMatcher(
        compile_signature_rules([("connect_timeout", r"timed out after")])
    )
    label = matcher.match(b"timed out after 00:00:30")
    assert label == "connect_timeout"


def test_resolve_label_template_sanitizes() -> None:
    assert resolve_label_template("%_connection_disconnected", "GR") == "gr_connection_disconnected"
    assert resolve_label_template("%_connection_disconnected", "!!!") is None


def test_cardinality_overflow_to_other() -> None:
    rules = compile_signature_rules([("%_connection_disconnected", r"(\w+) connection disconnected")])
    matcher = SignatureMatcher(rules, max_dynamic_labels=2)
    assert matcher.match(b"AA connection disconnected") == "aa_connection_disconnected"
    assert matcher.match(b"BB connection disconnected") == "bb_connection_disconnected"
    assert matcher.match(b"CC connection disconnected") == "__other__"
