"""Host Monitor gauge names (spec 004 §4.7, FR-MET-034), shared by the agent's
sampler, snapshot builder and rule engine so none of them hand-types a name.

`Snapshot.gauges` on the wire is a flat `dict[str, float]` with no dimensions,
so spec 004's `mount` dimension is encoded in the key: the gauge
`host_disk_used_ratio` is the worst (maximum) ratio over the readable mounts,
and each readable mount also gets `host_disk_used_ratio:<mount>`, where
`<mount>` is the configured `host.diskPaths` entry verbatim. Everything after
the first `:` is the mount, so a Windows `C:\\` mount needs no escaping. This
mirrors the `action_runs:<action>:<outcome>` key convention of spec 005 §5.1.
"""

from __future__ import annotations

HOST_DISK_USED_RATIO = "host_disk_used_ratio"
HOST_MEMORY_USED_RATIO = "host_memory_used_ratio"
MAGIC_PROCESS_UP = "magic_process_up"

# The gauges the Host Monitor owns. For these a missing value means "could not
# be read" (or the monitor is off), never "condition clear", so the rule engine
# holds a live alert's state instead of resolving it.
HOST_GAUGES: frozenset[str] = frozenset(
    {HOST_DISK_USED_RATIO, HOST_MEMORY_USED_RATIO, MAGIC_PROCESS_UP}
)

_MOUNT_SEPARATOR = ":"


def disk_mount_gauge(mount: str) -> str:
    """The wire key carrying one mount's ratio (see the module docstring)."""
    return f"{HOST_DISK_USED_RATIO}{_MOUNT_SEPARATOR}{mount}"
