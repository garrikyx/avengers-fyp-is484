"""UBS-114: `config/agent.yaml` is read once and each section reaches the
loader its component owns."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from telemetry_agent.config import (
    AgentConfigError,
    host_rule_filter,
    load_agent_config,
)
from telemetry_agent.health.host_monitor import HostConfig, default_disk_paths
from telemetry_agent.rules.config_loader import SighupRuleReloader, load_rules
from telemetry_agent.rules.engine import RuleEngine

REPO_ROOT = Path(__file__).resolve().parents[3]

_MINIMAL = """
agent:
  id: agent-x
  instanceIds: [inst-x]
publish:
  endpoint: https://backend.example/telemetry/batch
logs:
  paths: [./logs/Fix.log]
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "agent.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_the_shipped_local_dev_config_loads() -> None:
    cfg = load_agent_config(REPO_ROOT / "config" / "agent.yaml")

    assert cfg.agent_id == "magic-agent-sg-01"
    assert cfg.instance_id == "magic-prod-01"
    assert cfg.publish.endpoint == "http://127.0.0.1:8080/telemetry/batch"
    assert cfg.publish.dry_run is False
    assert cfg.callbacks is not None
    assert cfg.callbacks.endpoint.startswith("http://127.0.0.1:9000/")
    assert [p.name for p in cfg.logs.paths] == ["Application.log", "Fix.log"]
    assert cfg.rules_path == (REPO_ROOT / "config" / "rules.yaml").resolve()
    assert {r.name for r in cfg.rules} >= {"RejectSpike", "HighRejectRate"}
    assert cfg.parse_workers == 1
    # ADR 0010: the shipped Day-1 profile evaluates frequently enough to keep
    # log-to-query visibility within five seconds.
    assert cfg.evaluation_interval_seconds == 0.1


def test_minimal_config_gets_the_defaults(tmp_path: Path) -> None:
    cfg = load_agent_config(_write(tmp_path, _MINIMAL))

    assert cfg.agent_id == "agent-x"
    assert cfg.callbacks is None  # no section, no dispatcher
    assert cfg.logs.state_dir == Path(".agent-state")
    assert cfg.logs.app_log_patterns == ()
    assert cfg.logs.log_stall_threshold_seconds == 300
    assert cfg.parse_workers == 1
    assert cfg.evaluation_interval_seconds == 10.0
    assert len(cfg.rules) > 0  # rules.yaml absent here -> DEFAULT_RULES


def test_rules_path_resolves_next_to_the_config_file(tmp_path: Path) -> None:
    (tmp_path / "custom-rules.yaml").write_text(
        "rules:\n"
        "  - name: OnlyRule\n"
        "    kind: threshold\n"
        "    source: counter\n"
        "    metric: orders_rejected\n"
        '    operator: ">"\n'
        "    tiers: [{severity: warning, threshold: 1}]\n"
        "    window: 1m\n",
        encoding="utf-8",
    )
    cfg = load_agent_config(
        _write(tmp_path, _MINIMAL + "rules:\n  path: custom-rules.yaml\n")
    )
    assert [r.name for r in cfg.rules] == ["OnlyRule"]


def test_disabled_callbacks_mean_no_dispatcher(tmp_path: Path) -> None:
    cfg = load_agent_config(
        _write(
            tmp_path,
            _MINIMAL
            + "callbacks:\n  enabled: false\n  endpoint: https://magic.example/cb\n",
        )
    )
    assert cfg.callbacks is None


@pytest.mark.parametrize(
    ("extra", "section"),
    [
        ("pipeline:\n  parseWorkers: 0\n", "pipeline"),
        ("pipeline:\n  evaluationInterval: soon\n", "pipeline"),
        ("pipeline:\n  typo: 1\n", "pipeline"),
        ("logs:\n  paths: []\n", "logs"),
        ("callbacks:\n  endpoint: http://magic.example/cb\n", "callbacks"),
    ],
)
def test_a_bad_section_is_named_in_the_error(
    tmp_path: Path, extra: str, section: str
) -> None:
    text = _MINIMAL.replace("logs:\n  paths: [./logs/Fix.log]\n", "") + extra
    if section != "logs":
        text += "logs:\n  paths: [./logs/Fix.log]\n"
    with pytest.raises(AgentConfigError, match=rf"^{section}:"):
        load_agent_config(_write(tmp_path, text))


def test_missing_required_sections(tmp_path: Path) -> None:
    with pytest.raises(AgentConfigError, match="^publish:"):
        load_agent_config(_write(tmp_path, "logs:\n  paths: [a.log]\n"))
    with pytest.raises(AgentConfigError, match="^logs:"):
        load_agent_config(
            _write(tmp_path, "publish:\n  endpoint: https://b.example/x\n")
        )


def test_insecure_publish_endpoint_needs_the_explicit_flag(tmp_path: Path) -> None:
    text = _MINIMAL.replace("https://backend.example", "http://backend.example")
    with pytest.raises(AgentConfigError, match="^publish:"):
        load_agent_config(_write(tmp_path, text))


def test_missing_file_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(AgentConfigError, match="not found"):
        load_agent_config(tmp_path / "nope.yaml")


def test_error_signatures_are_read_from_parsing(tmp_path: Path) -> None:
    """UBS-116: `parsing.errorSignatures` reaches the app-log parser."""
    shipped = load_agent_config(REPO_ROOT / "config" / "agent.yaml")
    assert ("out_of_memory", "OutOfMemoryError|std::bad_alloc") in (
        shipped.parsing.error_signatures
    )

    minimal = load_agent_config(_write(tmp_path, _MINIMAL))
    assert minimal.parsing.error_signatures == ()
    assert minimal.parsing.max_dynamic_signature_labels == 50


def test_invalid_error_signature_regex_is_rejected(tmp_path: Path) -> None:
    text = _MINIMAL + "parsing:\n  errorSignatures:\n    - {label: bad, match: '('}\n"

    with pytest.raises(AgentConfigError, match="errorSignatures 'bad'"):
        load_agent_config(_write(tmp_path, text))


@pytest.mark.parametrize(("value", "seconds"), [("2m", 120), ("30s", 30), ("0.5", 0.5)])
def test_log_stall_threshold_is_configurable(
    tmp_path: Path, value: str, seconds: float
) -> None:
    cfg = load_agent_config(
        _write(tmp_path, _MINIMAL + f"  logStallThreshold: {value}\n")
    )
    assert cfg.logs.log_stall_threshold_seconds == seconds


@pytest.mark.parametrize("value", ["0s", "-1", ".inf", ".nan", "soon"])
def test_invalid_log_stall_threshold_is_rejected(tmp_path: Path, value: str) -> None:
    with pytest.raises(AgentConfigError, match="logs: logStallThreshold"):
        load_agent_config(
            _write(tmp_path, _MINIMAL + f"  logStallThreshold: {value}\n")
        )


def test_binary_parsing_defaults_to_disabled(tmp_path: Path) -> None:
    """FR-PRS-046: no `binaryMagic` means magic-binary never joins the chain."""
    cfg = load_agent_config(_write(tmp_path, _MINIMAL))

    assert cfg.parsing.binary_magic == b""
    assert cfg.parsing.binary_detect_window == 64


def test_binary_magic_is_read_as_hex(tmp_path: Path) -> None:
    text = _MINIMAL + "parsing:\n  binaryMagic: '4d414731'\n  binaryDetectWindow: 32\n"
    cfg = load_agent_config(_write(tmp_path, text))

    assert cfg.parsing.binary_magic == b"MAG1"
    assert cfg.parsing.binary_detect_window == 32


@pytest.mark.parametrize(
    "section",
    [
        "binaryMagic: 'zz'",
        "binaryMagic: '4d4'",
        "binaryDetectWindow: 0",
        "binaryMagic: '4d414731'\n  binaryDetectWindow: 2",
    ],
)
def test_invalid_binary_parsing_settings_are_rejected(
    tmp_path: Path, section: str
) -> None:
    text = _MINIMAL + f"parsing:\n  {section}\n"
    with pytest.raises(AgentConfigError, match="parsing"):
        load_agent_config(_write(tmp_path, text))


# --- UBS-129: host: (spec 010, FR-HLT-013) ---------------------------------


def test_host_defaults_follow_spec_010(tmp_path: Path) -> None:
    host = load_agent_config(_write(tmp_path, _MINIMAL)).host

    assert host.enabled is True
    assert host.sample_interval_seconds == 30.0
    assert host.disk_paths == default_disk_paths()  # spec 010's, or a Windows drive
    assert host.memory is True
    assert host.process_name == ""


def test_host_block_is_read(tmp_path: Path) -> None:
    host = load_agent_config(
        _write(
            tmp_path,
            _MINIMAL + "host:\n  enabled: false\n  sampleInterval: 5s\n"
            "  diskPaths: ['/a', '/b']\n  memory: false\n"
            "  process:\n    name: magic.exe\n",
        )
    ).host

    assert host.enabled is False
    assert host.sample_interval_seconds == 5.0
    assert host.disk_paths == ("/a", "/b")
    assert host.memory is False
    assert host.process_name == "magic.exe"


def test_the_shipped_config_uses_a_disk_path_that_exists_on_dev_machines() -> None:
    host = load_agent_config(REPO_ROOT / "config" / "agent.yaml").host

    assert host.enabled is True
    assert host.sample_interval_seconds == 30.0
    assert host.process_name == ""  # UBS-specific, left empty (spec 010)
    assert host.disk_paths
    assert all(Path(p).exists() for p in host.disk_paths)


@pytest.mark.parametrize(
    "block",
    [
        "host:\n  sampleInterval: 0s\n",
        "host:\n  sampleInterval: nonsense\n",
        "host:\n  diskPaths: ['/a','/b','/c','/d','/e','/f','/g','/h','/i']\n",
        "host:\n  diskPaths: ['']\n",
        "host:\n  unknownKey: 1\n",
    ],
)
def test_invalid_host_settings_are_rejected(tmp_path: Path, block: str) -> None:
    with pytest.raises(AgentConfigError, match="host"):
        load_agent_config(_write(tmp_path, _MINIMAL + block))


# --- spec 005 §1.2: host rules load only when the host block enables the gauge ---

_HOST_RULES = {"HostDiskFull", "HostMemoryHigh", "ApplicationDown"}


def _rule_names(tmp_path: Path, host_block: str) -> set[str]:
    cfg = load_agent_config(_write(tmp_path, _MINIMAL + host_block))
    return {r.name for r in cfg.rules}


def test_host_rules_load_only_for_the_gauges_the_host_block_enables(
    tmp_path: Path,
) -> None:
    # Defaults: disk and memory on, process.name empty -> no ApplicationDown.
    names = _rule_names(tmp_path, "")
    assert {"HostDiskFull", "HostMemoryHigh"} <= names
    assert "ApplicationDown" not in names

    with_process = _rule_names(tmp_path, "host:\n  process:\n    name: magic.exe\n")
    assert _HOST_RULES <= with_process


def test_host_disabled_loads_none_of_the_host_rules_and_keeps_the_rest(
    tmp_path: Path,
) -> None:
    enabled = _rule_names(tmp_path, "host:\n  process:\n    name: magic.exe\n")
    disabled = _rule_names(
        tmp_path, "host:\n  enabled: false\n  process:\n    name: magic.exe\n"
    )
    assert disabled == enabled - _HOST_RULES
    assert len(disabled) == 17  # every non-host default rule is untouched


def test_each_host_rule_follows_its_own_gauge(tmp_path: Path) -> None:
    no_memory = _rule_names(tmp_path, "host:\n  memory: false\n")
    assert "HostMemoryHigh" not in no_memory
    assert "HostDiskFull" in no_memory

    no_disk = _rule_names(tmp_path, "host:\n  diskPaths: []\n")
    assert "HostDiskFull" not in no_disk
    assert "HostMemoryHigh" in no_disk


def test_a_reload_cannot_bring_back_a_disabled_host_rule(tmp_path: Path) -> None:
    rules_path = REPO_ROOT / "config" / "rules.yaml"
    keep = host_rule_filter(HostConfig(enabled=True, process_name=""))
    engine = RuleEngine(
        load_rules(rules_path, keep=keep),
        instance_id="i",
        application="Magic",
        agent_id="a",
        started_at=datetime.now(UTC),
    )
    assert "ApplicationDown" not in {r.name for r in engine.rules}

    SighupRuleReloader(engine, rules_path, keep=keep).reload()

    names = {r.name for r in engine.rules}
    assert "ApplicationDown" not in names
    assert {"HostDiskFull", "HostMemoryHigh"} <= names


def test_the_shipped_config_leaves_application_down_unloaded_until_a_name_is_set() -> (
    None
):
    cfg = load_agent_config(REPO_ROOT / "config" / "agent.yaml")
    names = {r.name for r in cfg.rules}
    assert {"HostDiskFull", "HostMemoryHigh"} <= names
    assert "ApplicationDown" not in names  # spec 010: inactive until process.name
