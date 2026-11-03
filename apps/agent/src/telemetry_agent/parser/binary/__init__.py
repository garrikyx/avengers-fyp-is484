from telemetry_agent.parser.binary.classify import (
    DEFAULT_BINARY_DETECT_WINDOW,
    looks_like_magic_binary,
)
from telemetry_agent.parser.binary.parser import MagicBinaryParser

__all__ = [
    "DEFAULT_BINARY_DETECT_WINDOW",
    "MagicBinaryParser",
    "looks_like_magic_binary",
]
