import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class OffsetTracker:
    """Registrar subsystem for tracking offsets of log files.

    Stores file offsets indexed by OS (device, inode) fingerprints and persists
    them using JSON schema and atomic rename pattern.
    """

    def __init__(self, registry_path: Path = Path("offsets.json")) -> None:
        self.registry_path = Path(registry_path)
        self._states: dict[str, dict[str, Any]] = {}
        self.state_reset_reason: str | None = None
        self.load()

    def _make_key(self, dev: int, ino: int) -> str:
        """Generates internal state ID format (e.g., 'native::16777232-1048201')."""
        return f"native::{dev}-{ino}"

    def load(self) -> None:
        """Loads state registry into memory

        Supports Filebeat's native list schema with source/fileStateOS entries.
        Handles corrupted files safely by defaulting to an empty registry.
        """
        if not self.registry_path.exists():
            self.state_reset_reason = "missing"
            return

        try:
            with open(self.registry_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for state in data:
                    if not isinstance(state, dict):
                        raise ValueError("invalid registry entry")
                    os_meta = state.get("fileStateOS", {})
                    if not isinstance(os_meta, dict):
                        raise ValueError("invalid registry identity")
                    dev = os_meta.get("device")
                    ino = os_meta.get("inode")
                    if type(dev) is int and type(ino) is int:
                        key = self._make_key(dev, ino)
                        self._states[key] = state
                    else:
                        raise ValueError("invalid registry identity")
            elif isinstance(data, dict):
                self._states = data
            else:
                raise ValueError("invalid registry shape")
            for state in self._states.values():
                if not isinstance(state, dict):
                    raise ValueError("invalid registry entry")
                offset = state.get("offset", 0)
                if type(offset) is not int or offset < 0:
                    raise ValueError("invalid registry offset")
            self.state_reset_reason = None

        except (ValueError, OSError) as e:
            self.state_reset_reason = (
                "unreadable" if isinstance(e, OSError) else "corrupt"
            )
            logger.warning(
                "Corrupted or unreadable state registry '%s': '%s'. "
                "Defaulting to empty state (offset 0).",
                self.registry_path,
                e,
            )
            self._states = {}

    def get_offset(self, dev: int, ino: int) -> int:
        """Retrieves the last known offset for a given (device, inode) pair."""
        key = self._make_key(dev, ino)
        state = self._states.get(key)
        if state:
            offset = state.get("offset", 0)
            # Registries may have been hand-edited or created by an older
            # agent; never seek using an untrusted JSON value.
            if type(offset) is int and offset >= 0:
                return offset
        return 0

    def commit_offset(self, source_path: str, dev: int, ino: int, offset: int) -> None:
        """Persist committed offset after parse+ingest (FR-PIP-006)."""
        key = self._make_key(dev, ino)
        current = self._states.get(key, {}).get("offset", 0)
        if offset <= current:
            return
        self._states[key] = {
            "source": str(Path(source_path).resolve()),
            "offset": offset,
            "timestamp": datetime.now(UTC).isoformat(),
            "fileStateOS": {
                "device": dev,
                "inode": ino,
            },
        }

    def update_offset(self, source_path: str, dev: int, ino: int, offset: int) -> None:
        """Deprecated alias for commit_offset."""
        self.commit_offset(source_path, dev, ino, offset)

    def save(self) -> None:
        """Persists the current state registry to disk using atomic rename."""
        temp_path = self.registry_path.with_suffix(".tmp")
        try:
            # Export as list of state dicts
            state_list = list(self._states.values())

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(state_list, f, indent=2)

            # Atomic OS replace ensures zero corruption during sudden shutdowns
            os.replace(temp_path, self.registry_path)
        except OSError as e:
            logger.error(f"Failed to save state registry '{self.registry_path}': {e}")
