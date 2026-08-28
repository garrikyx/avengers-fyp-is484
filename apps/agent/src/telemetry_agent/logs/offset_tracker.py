import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class OffsetTracker:
    """Registrar subsystem for tracking offsets of log files.

    Stores file offsets indexed by OS (devide, inode) fingerprints and persists
    them using JSON schema and atomic rename pattern    
    """

    def __init__(self, registry_path: Path = Path("offsets.json")):
        self.registry_path = Path(registry_path)
        self._states: Dict[str, Dict[str, Any]] = {}
        self.load()

    def _make_key(self, dev:int, ino:int) -> str:
        """Generates internal state ID format (e.g., 'native::16777232-1048201')."""
        return f"native::{dev}-{ino}"

    def load(self) -> None:
        """Loads state registry into memory
        
        Supports Filebeat's native JSON list array schema (`[{"source": ..., "fileStateOS": ...}]`)
        and handles corrupted files safely by defaulting to an empty registry.
        """
        if not self.registry_path.exists():
            return

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for state in data:
                    os_meta = state.get("fileStateOS", {})
                    dev = os_meta.get("device")
                    ino = os_meta.get("inode")  
                    if dev is not None and ino is not None:
                        key = self._make_key(dev, ino)
                        self._states[key] = state
            elif isinstance(data, dict):
                self._states = data

        except (json.JSONDecodeError, OSError) as e:
            logger.warning(
                f"Corrupted or unreadable state registry '{self.registry_path}': '{e}'. "
                "Defaulting to empty state (offset 0)."
            )
            self._states = {}

    def get_offset(self, dev:int, ino:int) -> int:
        """Retrieves the last known offset for a given (device, inode) pair."""
        key = self._make_key(dev, ino)
        state = self._states.get(key)
        if state:
            return state.get("offset", 0)
        return 0

    def update_offset(self, source_path: str, dev:int, ino:int, offset:int) -> None:
        """Updates the offset for a given (device, inode) pair in memory."""
        key = self._make_key(dev, ino)
        self._states[key] = {
            "source": str(Path(source_path).resolve()),
            "offset": offset,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fileStateOS": {
                "device": dev,
                "inode": ino
            },
        }

    def save(self) -> None:
        """Persists the current state registry to disk using atomic rename."""
        temp_path = self.registry_path.with_suffix(".tmp")
        try:
            # Export as list of state dicts
            state_list = list(self._states.values())

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(state_list, f, indent=2)

            #Atomic OS replace ensures zero corruption during sudden shutdowns
            os.replace(temp_path, self.registry_path)
        except OSError as e:
            logger.error(f"Failed to save state registry '{self.registry_path}': {e}")

        