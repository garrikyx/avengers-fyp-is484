"""Value objects published by the Log Monitor."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FileReadStatus:
    """Offset, size and read lag for one monitored file."""

    path: str
    offset: int
    size: int | None
    last_read_at: datetime | None
    read_lag_ms: float | None

    @property
    def has_read_any_line(self) -> bool:
        return self.last_read_at is not None
