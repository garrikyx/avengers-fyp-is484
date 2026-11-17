# UBS-134 — Day-1 demo runbook

One command runs the Day-1 story on a single machine, with the real entrypoints
and local hosting only:

```sh
uv run python -m scripts.demo            # guided: press Enter between steps
uv run python -m scripts.demo --auto     # rehearsal: timed waits, no input
uv run python -m scripts.demo --no-teams # skip the Teams bot
```

It works the same on Windows, macOS and Linux. `make` is not needed.

## What runs

| Process | Entrypoint | Port |
| --- | --- | --- |
| Backend | `telemetry-backend --config config/demo/backend.yaml` | 8080 (+8081 internal) |
| Agent | `telemetry-agent --config config/demo/agent.yaml` | none |
| Simulator | `apps/simulator/src/simulator/mock_logger.py` | writes `.demo-run/logs/` |
| Teams bot | `telemetry-teams` (dev credentials, as `make teams-run`) | 3978 |
| **STUB** Magic callback endpoint | `scripts.mock_magic_callback_receiver` | 9000 |

The callback receiver is the only stub. Magic owns the real endpoint, and the
Day-1 scope says to mock it (spec 000 §7). It verifies the HMAC signature with the
agent's own `sign` function (`FR-CBK-005`).

`scripts/demo.py` only starts these processes and calls the public APIs. It holds
no telemetry logic of its own. Process output goes to `.demo-run/proc/<name>.log`.
Each run starts from a fresh `.demo-run/` folder, which is gitignored.

## Demo profile (config/demo/)

The demo profile changes only timings, so that the story fits in about 10 minutes:

| Setting | Demo | Production config |
| --- | --- | --- |
| HighRejectRate window / for / resolveAfter | 1m / 10s / 15s | 5m / 2m / 5m |
| HighRejectRate minSamples | 10 | 20 |
| Agent heartbeat | 5s | 10s |
| Backend `missingHeartbeatThreshold` | 20s | 60s |
| Host monitor | off | on |

The thresholds (3% warning, 5% critical) and the Day-1 publication profile
(1s buckets and publication, 100ms evaluation; ADR 0010) are unchanged.

## Storyline (spec 000 §7)

1. **Start the stack.** The launcher waits until orders show up in the metrics query.
2. **Normal trading.** `POST /telemetry/query/metrics` shows submitted, acked and
   rejected counts plus the reject rate (simulator at 0.5% rejects), and the agent's
   health.
3. **Reject burst within 5 s (#1).** The simulator switches to 60% rejects. The
   launcher times how long the burst takes to appear in the query.
4. **HighRejectRate (#2).** The firing callback reaches the Magic stub, signed, and
   `GET /telemetry/alerts` shows the alert. After the burst stops, the severity
   steps down (critical, then warning) and the alert resolves, each with its own
   callback. Resolving takes about 1 minute because the burst has to age out of
   the 1m window.
5. **Ask in Teams (#3).** Ask "Why are Magic orders rejecting in the last 30
   minutes?" in the Teams App Test Tool:
   `npx @microsoft/teams-app-test-tool start -e http://localhost:3978/api/messages -c msteams`.
   The launcher also sends the same question to `POST /telemetry/nl/query` and
   prints the matching metrics query. The two should show the same numbers.
6. **Rotation and restart (#4, short form).** The simulator rotates logs every
   100 KB. The agent stops gracefully, misses about 6 seconds of logs, then
   restarts from its saved offsets. Counts continue and `restartedBuckets` goes up.
   The full evidence (5-minute outage at 5,000 lines/s, exact counts) is in
   [ubs140-day1-acceptance.md](./ubs140-day1-acceptance.md).
7. **Agent stops.** About 20–30 s later the backend raises `AgentHeartbeatMissing`.
   When the agent comes back, the alert resolves.

## Before the demo

- Run `uv sync --all-packages`.
- Optional: run Ollama with `llama3.2` pulled. The headline question is
  rule-matched and answers without the LLM; free-form questions need Ollama.
- Make sure ports 8080, 8081, 9000 and 3978 are free. Preflight refuses to start
  if any of them is taken.
- Do one `--auto` rehearsal. It takes about 4 minutes.

## Show every piece live (Windows, one window each)

For showing each component running, use the window launcher instead of the
guided script. It uses the same entrypoints and `config/demo/*`:

```bat
scripts\demo_windows.bat
```

It runs `uv sync --all-packages`, refuses to start if 8080, 8081, 9000, 3978 or
8765 is taken, checks Ollama, then opens one titled window per process. It waits
for each one to come up before starting the next:

| Window | What it proves |
| --- | --- |
| `FYP demo: 1 backend :8080` | Backend receiving batches and serving the query, alerts and NL APIs |
| `FYP demo: 2 Magic callback STUB :9000` | #2: one line per signed callback (`signed callback OK: HighRejectRate firing (critical)`); unsigned or tampered ones get 401 |
| `FYP demo: 3 simulator` | The Magic log generator, writing `.demo-run\logs\Application.log` and `Fix.log` and rotating them every 100 KB |
| `FYP demo: 4 agent` | The on-host agent tailing those logs; only derived counters leave it |
| `FYP demo: 5 Teams bot :3978` | The bot endpoint the playground talks to |
| `FYP demo: 6 MCP server (Copilot) :8765` | The MCP server Copilot Studio (or MCP Inspector) connects to at `http://127.0.0.1:8765/mcp` |
| `FYP demo: 7 Teams App Test Tool` | The playground (#3): ask "Why are Magic orders rejecting in the last 30 minutes?" |

The playground is `npx -y @microsoft/teams-app-test-tool ...`, which downloads
the tool on first use. Run it once before the demo so the download isn't live.
`set DEMO_SKIP_TEST_TOOL=1` skips that window.

### Rules showcase

The demo loads 7 agent rules: `config/demo/rules.yaml`, plus
`config/demo/anomaly.yaml` beside it. The backend adds `AgentHeartbeatMissing`.
Each rule has a command that fires it. Run them in a second terminal and use
`alerts` to show the result:

| Command | Fires | Then |
| --- | --- | --- |
| `scripts\demo_windows.bat alerts` | Nothing. Prints every alert so far: rule, severity, status, observed value, threshold, first seen, resolved | |
| `scripts\demo_windows.bat burst` | `HighRejectRate` (rate over 3% / 5%), `RejectSpike` (more than 50 rejects in 1 minute), `AbnormalRejectRate` and `AbnormalExecutionIssueRate` (well above the learned baseline). Each sends a signed callback to the stub (#1, #2) | `normal`: the alerts step down and resolve |
| `scripts\demo_windows.bat app-fault` | `AppOutOfMemory` (OutOfMemoryError signature) and `AppLogFailure` (any `[F]` line in Application.log) | `app-normal`: they resolve once the 1-minute window has no faults |
| `scripts\demo_windows.bat logs-stop` | `NoLogActivity`, once a full minute passes with no new log lines | `logs-start`: lines flow and it resolves |
| `scripts\demo_windows.bat agent-stop` | `AgentHeartbeatMissing`, raised by the backend about 20 s after the last heartbeat | `agent-start`: it clears and counts continue from the saved offsets |
| `scripts\demo_windows.bat stop` | Nothing. Closes every demo window and frees the ports | |

**Baseline first.** The anomaly rules compare the last minute with a 3-minute
baseline and need at least 100 samples. Let normal trading run for 3+ minutes
after start-up before `burst`. Otherwise the Abnormal* rules can't judge yet, and
only HighRejectRate and RejectSpike fire.

**Live rule reload.** The agent watches `config/demo/rules.yaml` and
`anomaly.yaml`. Edit a threshold during the demo and save: the agent reloads it
in about 10 s without a restart. For example, set HighRejectRate's warning tier
from `0.03` to `0.004` and it fires on normal traffic. A broken file is
rejected and the old rules stay in force.

The simulator has no live controls, so `burst`, `normal`, `app-fault`,
`app-normal` and `logs-start` restart it with new arguments. The current reject
rate and fault rate are saved in `.demo-run\`, so each command changes only its
own setting. The logs and the agent's offsets carry on, so no counts are lost.

**App faults.** The simulator's new `--app-faults RATE` sets what share of
Application.log lines are `[F] OutOfMemoryError`. The demo starts it at `0`, so
AppOutOfMemory and AppLogFailure stay quiet until `app-fault` sets 5%. Without
the flag, the simulator behaves as before: `[F]` lines appear at random
(about 7.5% of application lines), which suits the other tests but would keep
those two alerts firing all through a demo.

Query the backend by hand (PowerShell):

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8080/telemetry/query/metrics -ContentType application/json -Body '{"timeRange":{"last":"30m"},"metrics":["orders_submitted","orders_acked","orders_rejected","reject_rate"]}' | Select-Object -ExpandProperty totals
Invoke-RestMethod "http://127.0.0.1:8080/telemetry/alerts?status=active" | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method Post http://127.0.0.1:8080/telemetry/nl/query -ContentType application/json -Body '{"question":"Why are Magic orders rejecting in the last 30 minutes?"}' | Select-Object answer
```

Or with curl:

```sh
curl -s -X POST http://127.0.0.1:8080/telemetry/query/metrics -H "Content-Type: application/json" -d "{\"timeRange\":{\"last\":\"30m\"},\"metrics\":[\"orders_submitted\",\"orders_rejected\",\"reject_rate\"]}"
curl -s "http://127.0.0.1:8080/telemetry/alerts?status=active"
```

`status` takes `active`, `resolved` or `all`.

**Ollama model name.** `config/demo/backend.yaml` asks for `llama3.2`, but a
machine with only `llama3.2:3b` pulled answers "model not found". The launcher
warns about this. The headline question is rule-matched and still answers;
free-form questions get the fallback reply until the name matches.

## macOS: one script per component plus `demo.sh`

`scripts/demo_mac/` is the macOS version of `demo_windows.bat`. It uses the same
entrypoints, `config/demo/*` and commands. The scripts work with the bash 3.2
that ships with macOS.

| Script | What it runs |
| --- | --- |
| `backend.sh` | `telemetry-backend --config config/demo/backend.yaml` (:8080) |
| `magic_stub.sh` | **STUB** Magic callback endpoint (:9000) |
| `simulator.sh [rate] [faults]` | log generator (`mock_logger.py`) writing `.demo-run/logs/` |
| `agent.sh` | `telemetry-agent --config config/demo/agent.yaml` |
| `teams_bot.sh` | Teams bot with dev credentials (:3978) |
| `mcp.sh` | MCP server for Copilot (:8765) |
| `playground.sh` | Agents Playground (:56150); opens the browser |
| **`demo.sh`** | starts and stops all of them, and runs the storyline |

```sh
scripts/demo_mac/demo.sh              # start every component, one Terminal window each
scripts/demo_mac/demo.sh run          # start, then the guided storyline (press Enter between steps)
scripts/demo_mac/demo.sh run --auto   # the same with timed waits (~12 min incl. the 3 min baseline)
scripts/demo_mac/demo.sh alerts       # alert table
scripts/demo_mac/demo.sh ask "Any alerts open for Magic?"
scripts/demo_mac/demo.sh stop
```

`burst`, `normal`, `app-fault`, `app-normal`, `logs-stop`, `logs-start`,
`agent-stop` and `agent-start` work as in the Windows table above. `run` plays
them in order:

1. start the stack;
2. 3 minutes of normal trading (anomaly baseline) and the headline question;
3. burst and alerts;
4. normal, and the alerts resolve;
5. app faults;
6. log generator stopped (NoLogActivity);
7. agent stopped (AgentHeartbeatMissing);
8. summary.

**Where components show up:**
- **Default:** one titled Terminal.app window per component, opened with `osascript`.
- **`DEMO_TMUX=1`:** one tmux session (`tmux attach -t fypdemo`) with a window per component.
- **`DEMO_HEADLESS=1`:** background processes, with logs in `.demo-run/proc/<name>.log`.

Every component writes a PID file to `.demo-run/pids/`. `stop` sends SIGTERM, so
the agent drains, publishes and checkpoints, then SIGKILL after 10 s.

**Prerequisites:**
- `brew install uv node`, plus `tmux` if you use it;
- the Ollama app with `llama3.2` (`ollama pull llama3.2`, or `ollama cp llama3.2:3b llama3.2`);
- `uv sync --all-packages`.

**macOS notes:**
- The first `demo.sh start` asks to let your terminal control Terminal.app
  (System Settings → Privacy & Security → Automation). Allow it, or use
  `DEMO_TMUX=1` / `DEMO_HEADLESS=1`.
- If you copied the repo from Windows, the executable bit may be missing. Run
  `chmod +x scripts/demo_mac/*.sh`, or call them as `bash scripts/demo_mac/demo.sh`.
- **Not yet run on a real Mac.** The scripts pass `bash -n` and were smoke-tested
  headless under Git Bash on Windows. Do one full `run --auto` on the demo Mac
  before presenting.

## Known limits to say out loud

- **Teams is the local Agents Playground, not a real tenant.** The real tenant is
  UBS-142.
- **The reject reason shows as "unspecified"**, even though the simulator writes
  reason codes (the events API shows `OrderExceedsLimit`). The query layer looks up
  `reject_reason`, but the agent publishes `rejectReason`
  (`telemetry_shared/query/aliases.py`). That is a backend fix, not part of this demo.
- **Free-form questions go through a small local LLM (llama3.2 3b).** It can make up
  a filter value (e.g. `instanceId: "orders"`) and then answer 0. Stick to the
  suggested questions on stage.
- **Steps 6 and 7 are a graceful stop.** Crash and disconnected-loss bounds are
  covered by FR-PUB-008 and ADR 0010, not by this demo.
- **The leak sentinel (#5) is not a demo step.** Show it by running
  `uv run pytest -q tests/integration/test_UBS_137_data_leak_sentinel.py` (UBS-137).

Fixed on main since the first version of this runbook:
- **Alert cards in the chat (UBS-120)** are on in the demo profile.
- **A second outage of the same agent** now alerts again (UBS-136).
- **The reject summary** states the rate in its own sentence (UBS-141).

## Alert cards in the chat (UBS-120)

`config/demo/backend.yaml` turns on `notifications.teams`. When an alert fires and
when it resolves, the backend posts the alert to the bot's `/api/notify`, and the bot
sends an Adaptive Card into the chat.

- Every launcher (`scripts.demo`, `demo_windows.bat`, `demo_mac/demo.sh`)
  generates `MAGIC_TELEMETRY_TEAMS_NOTIFY_TOKEN` for each run and gives it to the
  backend and the bot. Set it yourself to use a fixed value. The backend refuses to
  start without it, by design.
- The bot runs with `TEAMS_NOTIFY_ALLOW_PERSONAL=true`, because the Playground is a
  1:1 chat.
- **Say "hi" to the bot once** after it starts. The bot only learns which chat to post
  into from a message (it saves it to `.teams-state/conversation.json`). Until then the
  backend logs a 409 for each card and counts it.
- Expect one card per firing and one per resolve: `burst` gives HighRejectRate and
  RejectSpike, `normal` resolves them, and `agent-stop` gives AgentHeartbeatMissing.
  A severity step-down (critical to warning) posts nothing.

## Windows notes

- The agent now treats Ctrl+Break (`SIGBREAK`) as a graceful stop, the same as
  SIGINT and SIGTERM. That is the only console signal one Windows process can send
  to another, so the launcher uses it to stop the agent.
- If a run is killed, child processes can outlive it. Free the ports before
  running again.
