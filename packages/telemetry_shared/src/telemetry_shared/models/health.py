from datetime import datetime

from pydantic import BaseModel


class FileReadHealth(BaseModel):
    """Per-file read health (UBS-30). See docs/plan/ubs30-notes.md."""

    path: str
    offset: int
    size: int | None = None
    last_read_at: datetime | None = None
    read_lag_ms: float | None = None


class AgentHeartbeat(BaseModel):
    agent_id: str
    instance_id: str
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    queue_depth: int
    # Populated by the Health Reporter (UBS-30). See docs/plan/ubs30-notes.md.
    files: list[FileReadHealth] = []
    read_lag_ms: float | None = None
