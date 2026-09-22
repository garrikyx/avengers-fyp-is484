# Demo run sheet — Health Reporter (UBS-30 / 58 / 59 / 60)

**Your line:** *"The agent watches Magic's logs. My part is the agent watching **itself** — and telling the backend, every few seconds, whether it can still be trusted."*

Everything below runs off **`main`** — UBS-58/59/60 merged as PRs #14/#15/#16. Nothing depends on unmerged work.

---

> Runs on macOS, Linux or Windows (Git Bash). Paths below are relative to the repo root.

## Pre-flight (do this ~10 min before, not live)

```bash
cd <repo root>
git checkout main && git pull
uv sync
```

Then create the demo config **once** (it is git-ignored nowhere, so delete it after):

```bash
printf 'agent:\n  id: magic-agent-sg-01\n  instanceIds: [magic-prod-01]\nheartbeat:\n  interval: 2s\nhealth:\n  readLagDegraded: 5s\n' > demo-agent.yaml
```

> 2s heartbeat and a 5s lag threshold are demo-speed. Production defaults are 10s / 5s (spec 010).

Smoke test it now, then Ctrl-C:
```bash
uv run telemetry-agent-heartbeat --config demo-agent.yaml --log demo_logs/Fix.log
```
You should see a JSON heartbeat every 2 seconds. If you do, you're safe.

**Reset between runs:** `rm -rf demo_logs`

---

## Terminal layout

| Terminal | Purpose |
| --- | --- |
| **T1** | the agent — the thing everyone watches |
| **T2** | the driver script — feeds the log on a timer |
| (T3) | optional: the backend, for the integration beat |

Make T1's font big. The heartbeat JSON is the star.

---

## The demo (≈3 minutes)

**T1 — start the agent:**
```bash
uv run telemetry-agent-heartbeat --config demo-agent.yaml --log demo_logs/Fix.log
```

**T2 — drive it:**
```bash
bash docs/demo/drive.sh demo_logs/Fix.log
```

The driver prints a cyan banner before each beat so you always know what's coming.

### Beat 1 — idle (≈10s)
Heartbeats every 2s with an empty log. `status: healthy`, `readLagMs: null`.

> *"Nothing is happening in the log, and the agent still reports. That's the point: a quiet agent and a dead agent look identical to a backend unless the agent keeps saying 'I'm here'. Note `readLagMs` is **null**, not zero — we've never read a line, so we don't claim a lag of zero. A gap is never reported as a number."*

### Beat 2 — a real order arrives
`files[].state` flips to `reading`, `readLagMs` gets a value, offset moves.

> *"One FIX new-order. The agent now knows when it last read a line."*

### Beat 3 — the log goes quiet (>5s)
`status: degraded` + `statusReasons: ["demo_logs\Fix.log: read lag 5447ms exceeds 5000ms threshold"]`

> *"This is the dangerous failure: the file is there, the agent is alive, but it has stopped keeping up. Every metric downstream would look like 'no trading activity'. The reason names the file and the number — the operator doesn't have to guess."*

### Beat 4 — an unparseable line
`parseErrorCountLast5Min: 1`, `status: unhealthy`, reason `parse error rate 50.0% (1/2 lines in last 300s) exceeds 25%`

> *"A MsgType we don't support. Rate, not raw count — 1 bad line out of 2 is an emergency, 1 out of 10,000 is noise. The denominator comes from the same 5-minute window."*

### Beat 5 — recovery
Clean traffic arrives; the rate decays `50% → 8.3%` and severity drops back to `degraded`.

> *"Sliding window, so the agent recovers on its own — no restart, no manual reset."*

**Close on:** *"One `status`, one list of reasons, on a fixed interval, whether or not there's anything else to say."*

---

## Optional beat — it talks to the real backend (+40s)

Only if the room wants it. **T3:**
```bash
uv run uvicorn telemetry_backend.main:app --port 8080 --log-level warning
```
Restart T1 with:
```bash
uv run telemetry-agent-heartbeat --config demo-agent.yaml --log demo_logs/Fix.log --sink http://127.0.0.1:8080/telemetry/heartbeat
```
Backend logs `202 Accepted` per heartbeat.

> *"Ingestion (UBS-66) landed a heartbeat contract in parallel with mine. Rather than block, the agent adapts to theirs at the wire boundary — internally we keep the richer shape. That's why there's a reconciliation item on the board."*

**Do not** show `--sink` against a backend you haven't started; a failing sink is fine (it's designed to keep ticking) but it's a distraction.

---

## Questions you should expect

**"Is it in production?"**
> No. Merged to main and tested. The transport is still a placeholder — the real Backend Publisher (batching, gzip, auth, retry) is M4. The pipeline bridge landed last week, so wiring the parser's real output into the reporter is the next small ticket.

**"What's `null` vs `0` about?"**
> `null` means nobody is measuring that signal yet; `0` means measured and genuinely zero. Collapsing them is how a monitoring system reports a broken agent as perfectly healthy. FR-HLT-004.

**"Why doesn't the backend show these?"**
> The backend read side is UBS-69 — health endpoints and agent liveness — in review. The backend can't be the one to notice an agent died *by asking the agent*, so staleness is decided backend-side there.

**"Who decides degraded vs unhealthy?"**
> One documented rule set, spec 011 §2. Read lag >5s or parse rate >1% is degraded; parse rate >25% or a full publish queue is unhealthy. Thresholds are config, not code.

**If asked about the two competing heartbeat models:** be straight — parallel development, both to the same spec section, mine nullable and theirs required; the agent adapts for now and the team reconciles. It's in the notes doc with the reversal path.

---

## Don't do these live

- **Don't run the full `pytest` unless you've checked it on the demo machine first.** On Windows 9 tests fail for CRLF/file-handle reasons unrelated to this work. Those are platform-specific and **may well pass on macOS** — verify before you rely on it. The always-safe number is **`uv run pytest -q tests/unit/agent/health`** → **84 passed**.
- Don't demo UBS-69/96 from `main` — they're not merged. If you want them, check out `UBS-69-Backend-Health-Endpoints` beforehand and rehearse separately.
- Don't leave `demo-agent.yaml` / `demo_logs/` lying around in a commit.

## If something breaks

| Symptom | Do this |
| --- | --- |
| No heartbeats | Wrong cwd — must be the repo root. Check `demo-agent.yaml` exists. |
| `--interval must be > 0` | You passed `--interval 0`; drop the flag, the config sets 2s. |
| Port 8080 busy | `--port 8081` and change the `--sink` URL to match. |
| Stale state from a previous run | `rm -rf demo_logs` and restart T1. |
| Everything on fire | Drop the backend beat entirely. Beats 1–5 need **no** network and are the actual story. |
