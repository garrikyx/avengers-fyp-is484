"""UBS-104: exponential backoff with jitter, shared between the Callback
Dispatcher (`FR-CBK-004`) and the Backend Publisher (`FR-PUB-005`).

Moved here verbatim from `callbacks/backoff.py` (which now just re-exports
it) once the Publisher needed the identical retry math -- no behavior
change, see that module for the shim.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Exponential backoff with jitter. Defaults match spec 010's example:
    base 1s, factor 2, cap 60s, jitter 0.2 (+/-20%).

    `max_attempts` is meaningful to the Callback Dispatcher (`FR-CBK-004`),
    which gives up and marks an alert `FAILED` after that many tries. The
    Backend Publisher (`FR-PUB-005`) has no such cap -- it retries
    indefinitely, bounded only by the buffer's own byte/age eviction, so
    it simply never reads this field.
    """

    base_seconds: float = 1.0
    factor: float = 2.0
    cap_seconds: float = 60.0
    jitter: float = 0.2
    max_attempts: int = 5

    def delay_for_attempt(
        self, attempt: int, *, retry_after: float | None = None
    ) -> float:
        """Delay before `attempt` (1-indexed: the Nth retry), in seconds.

        `retry_after` overrides the computed delay when the server supplied
        one and it's larger (`FR-CBK-006`'s "honouring Retry-After when
        present").
        """
        raw = min(self.base_seconds * (self.factor ** (attempt - 1)), self.cap_seconds)
        jittered = raw * random.uniform(1 - self.jitter, 1 + self.jitter)
        if retry_after is not None:
            return max(jittered, retry_after)
        return jittered
