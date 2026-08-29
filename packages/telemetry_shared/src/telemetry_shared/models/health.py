from datetime import datetime

from pydantic import BaseModel


class FileReadHealth(BaseModel):
    """Per-file read health, as required by spec 002 `FR-LOG-010` and the spec 011
    health signals table (`files[].offset`, `log_read_lag_ms`).

    `read_lag_ms` is `None` rather than `0` until the file has actually produced a
    line — spec 011 `FR-HLT-004` requires that a data gap never be reported as a zero.
    """

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
    # Populated by the Health Reporter (UBS-30 / `FR-HLT-001`). Parse error counts,
    # callback failure counts and the full healthy/degraded/unhealthy rollup
    # (`FR-HLT-002`) depend on the Parser Engine and Callback Dispatcher, neither of
    # which exist yet (M2/M5), so only the Log Monitor's own signals are wired here.
    files: list[FileReadHealth] = []
    read_lag_ms: float | None = None
