"""Live walkthrough of SIGHUP rule reloading (`FR-RUL-008`/`009`).

    uv run python -m telemetry_agent.rules.demo_reload

Hot-reload is the one Rule Engine feature that can't be shown in a
non-interactive script: it needs a running process to send a signal to, and
nothing in this repo runs continuously yet (see `SighupRuleReloader`'s own
docstring). This is a purpose-built demo harness for that — explicitly not
the agent supervisor loop, which doesn't exist.

It holds one alert firing, then waits while you edit the rule file and
`kill -HUP` it, printing what the engine does each time:

  1. change a threshold  -> rules swap, the firing alert keeps its alertId
  2. delete a firing rule -> one synthetic `resolved` event
  3. corrupt the YAML     -> rejected, last-known-good rules keep running

By default it copies `config/rules.yaml` to a temp file and watches the
copy, so editing it can't leave the real config modified — the drift test
in `test_RE_05_config_loader.py` compares that file against DEFAULT_RULES.
Pass `--rules config/rules.yaml` to drive the real one instead.

Ctrl-C to stop; the temp copy is removed on exit.
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from telemetry_agent.rules.config_loader import (
    RuleConfigError,
    SighupRuleReloader,
    load_rules,
)
from telemetry_agent.rules.demo_quickstart import _RULES_PATH, _Demo, _show_alerts

_POLL_SECONDS = 2.0

# Enough rejects to clear RejectSpike's threshold of 50 with headroom, so
# the operator can raise the threshold and watch the alert survive the
# reload before raising it far enough to clear the condition.
_STANDING_REJECTS = 60
_WATCHED_RULE = "RejectSpike"


def _banner(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}", flush=True)


def _instructions(pid: int, watched: Path) -> None:
    print(f"\n  watching : {watched}", flush=True)
    print(f"  pid      : {pid}", flush=True)
    print(f"  reload   : kill -HUP {pid}", flush=True)
    print(
        "\n  Try these, in another terminal, re-running the reload command"
        "\n  after each edit:",
        flush=True,
    )
    print(
        f"""
  1. RAISE A THRESHOLD, STILL MATCHED — under `- name: RejectSpike`, set
         threshold: 55
     {_STANDING_REJECTS} rejects still clear 55, so the alert keeps firing
     on the SAME alertId: FR-RUL-008 hot-swaps the rules without losing
     alert state.

  2. RAISE IT PAST THE OBSERVED VALUE — set
         threshold: 500
     Now the condition stops matching, so the alert starts resolving — the
     new threshold took effect on the very next evaluation, with no
     restart.

  3. DELETE A FIRING RULE — remove the whole `- name: RejectSpike` block.
     Expect one synthetic `resolved` event: an alert can't stay open for a
     condition that no longer has a definition.

  4. CORRUPT THE FILE — on any rule, set
         operator: "!!"
     Expect an error naming the offending rule, and this process KEEPS
     RUNNING on its last-known-good rules (FR-RUL-009). A bad config
     deploy must not take alerting down with it.
""",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Live SIGHUP rule-reload demo (FR-RUL-008/009)."
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=None,
        help=(
            "Rule file to watch. Defaults to a temp copy of config/rules.yaml "
            "so edits can't dirty the real config."
        ),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=_POLL_SECONDS,
        help="Seconds between evaluations.",
    )
    args = parser.parse_args()

    # The reloader logs the reload/reject outcome — that logging *is* the
    # demo here, unlike demo_quickstart where it's noise.
    logging.basicConfig(
        level=logging.INFO, format="  [%(levelname)s] %(message)s", stream=sys.stdout
    )

    temp_dir: str | None = None
    if args.rules is not None:
        watched = args.rules
    else:
        temp_dir = tempfile.mkdtemp(prefix="rules-reload-demo-")
        watched = Path(temp_dir) / "rules.yaml"
        shutil.copy(_RULES_PATH, watched)

    try:
        _run(watched, interval=args.interval)
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"\n  cleaned up {temp_dir}", flush=True)


def _run(watched: Path, *, interval: float) -> None:
    demo = _Demo(rules_path=watched)

    _banner("RULE ENGINE — hot-reloading rules without losing alert state")
    print(f"  {len(demo.rules)} rules loaded from {watched.name}", flush=True)

    # A standing condition so there is always something firing to observe.
    # The ingest clock is pinned, so these rejects never age out of their
    # window and the alert stays up for as long as the demo runs.
    demo.feed([demo.logon()])
    demo.feed(demo.rejected_orders(_STANDING_REJECTS, start=1))
    fired = demo.settle("1m", for_seconds=demo.rule_for_seconds(_WATCHED_RULE))
    print(f"\n  standing alert ({_STANDING_REJECTS} rejects):", flush=True)
    _show_alerts(fired)
    held_alert_id = fired[0].alert_id if fired else "(none)"

    reloader = SighupRuleReloader(demo.engine, watched)
    reloader.install()

    _instructions(os.getpid(), watched)
    print("  --- watching for SIGHUP (Ctrl-C to stop) ---\n", flush=True)

    rule_count = len(demo.rules)
    try:
        while True:
            time.sleep(interval)
            changed = demo.tick("1m", advance=int(interval))
            if changed:
                _show_alerts(changed)

            # `apply_rules` swapped the engine's rules in place, so re-read
            # them from disk only to report the count the operator sees.
            current = _safe_rule_count(watched, fallback=rule_count)
            if current != rule_count:
                print(f"  rule count now {current} (was {rule_count})", flush=True)
                rule_count = current

            status = demo.engine.status_of(_WATCHED_RULE)
            if status is not None:
                print(
                    f"  {_WATCHED_RULE}: status={status.value}  "
                    f"alertId={held_alert_id[:8]} (same alert throughout)",
                    flush=True,
                )
            else:
                print(
                    f"  {_WATCHED_RULE}: no longer tracked — its rule left the "
                    "config, so the alert was resolved and the key freed",
                    flush=True,
                )
    except KeyboardInterrupt:
        print("\n  stopped.", flush=True)


def _safe_rule_count(path: Path, *, fallback: int) -> int:
    """The watched file may be mid-edit or deliberately broken; a failed
    read here must not kill the demo any more than it kills the engine.
    """
    try:
        return len(load_rules(path))
    except (RuleConfigError, OSError):
        return fallback


if __name__ == "__main__":
    main()
