"""UBS-114: `config/agent.yaml` is read once and each section reaches the
loader its component owns."""

from pathlib import Path

import pytest
from telemetry_agent.config import AgentConfigError, load_agent_config

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
    assert cfg.evaluation_interval_seconds == 10.0


def test_minimal_config_gets_the_defaults(tmp_path: Path) -> None:
    cfg = load_agent_config(_write(tmp_path, _MINIMAL))

    assert cfg.agent_id == "agent-x"
    assert cfg.callbacks is None  # no section, no dispatcher
    assert cfg.logs.state_dir == Path(".agent-state")
    assert cfg.logs.app_log_patterns == ()
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
