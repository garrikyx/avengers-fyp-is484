from __future__ import annotations

from typing import TypeVar

from telemetry_agent.parser.protocol import Confidence, Parser

_PARSERS: dict[str, Parser] = {}
P = TypeVar("P", bound=Parser)


def register_parser(parser: P) -> P:
    """Register a parser at import time"""
    key = parser.name()
    if key in _PARSERS:
        msg = f"parser {key!r} already registered"
        raise ValueError(msg)
    _PARSERS[key] = parser
    return parser


def get_parser(name: str) -> Parser:
    """Look up a registered parser by configuration name."""
    try:
        return _PARSERS[name]
    except KeyError as exc:
        msg = f"unknown parser {name!r}"
        raise KeyError(msg) from exc


def registered_names() -> frozenset[str]:
    return frozenset(_PARSERS)


class Registry:
    """Selects the first parser in a configured chain with Confidence.HIGH."""

    def __init__(self, parsers: dict[str, Parser] | None = None) -> None:
        self._parsers = parsers if parsers is not None else dict(_PARSERS)

    def select(self, chain: list[str], line: bytes) -> tuple[Parser | None, Confidence]:
        """FR-PRS-031: first parser returning HIGH wins."""
        for name in chain:
            parser = self._parsers.get(name)
            if parser is None:
                continue
            confidence = parser.classify(line)
            if confidence == Confidence.HIGH:
                return parser, confidence
        return None, Confidence.NONE

    def validate_chain(self, chain: list[str]) -> list[str]:
        """Return unknown parser names in chain."""
        return [name for name in chain if name not in self._parsers]
