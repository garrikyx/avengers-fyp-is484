# Demo script: Windows

Presenter script for the 20-minute slot: what to type, when to run the next command,
what to put on screen, and what to say. Total is about 16–17 minutes, leaving 3–4
minutes for questions.

macOS version: [demo-script-macos.md](demo-script-macos.md).

## How you run it

Windows has no paced storyline command, so you drive it with
`scripts\demo_windows.bat <command>` from **Command Prompt**, in the repo folder.
**Each command starts the next action straight away**, so run it only when the thing
you are waiting for has appeared (cues below).

- **Main Command Prompt:** every command in this script.
- **Second Command Prompt:** only for the MCP Inspector (optional).
- To rehearse hands-free: `uv run python -m scripts.demo --auto --showcase`. This is a
  slightly different guided storyline, so use it to get familiar, not as the script
  below.

Tip: press the **Up arrow** to recall `scripts\demo_windows.bat alerts` instead of
retyping it.

## Screen layout (set this up before you start)

What the audience sees should tell the story without you pointing at small text.

```text
+------------------------------+------------------------------+
|                              |                              |
|   Playground (Teams)         |   Main Command Prompt        |
|   alert cards + chat         |   answers, alert tables,     |
|                              |   showcase results           |
|                              |                              |
+------------------------------+------------------------------+
   Behind, ready to bring forward (Alt+Tab or the taskbar):
   "2 Magic callback STUB"   "4 agent"   "3 simulator"
```

- **Left half:** the Playground (drag it to the left edge, or press **Win and Left**).
  This is what support staff would see, so it's the main stage.
- **Right half:** the main Command Prompt (**Win and Right**).
- **Behind:** the Magic stub window (signed callbacks, 401), the agent window, and the
  simulator window. Bring one forward only when the script says so, then go back to
  the two-pane layout.
- Make the text big enough for the back of the room: in each window you show, hold
  **Ctrl and scroll up**.
- Turn on **Do not disturb** (Focus) and close other apps (chat, mail) so nothing pops
  up.
- Minimise the backend, Teams bot and MCP server windows. You name them in the intro
  but don't need them after that.

## Next-command cheat sheet

Run each command only when the cue is met. If you are still talking, keep talking:
waiting longer never hurts.

| # | Command | Run it when | Wait after the previous one |
| --- | --- | --- | --- |
| 1 | `burst` | You've done the step 2 extras **and** 3 minutes have passed since the start | 3 min |
| 2 | `alerts`, then `ask "Any alerts open for Magic?"` | A red card is in the Playground **and** the stub shows `AbnormalRejectRate firing` | 65 s |
| 3 | `normal` | You've explained the alert table and answer | – |
| 4 | `alerts` | **Resolved** cards for HighRejectRate and RejectSpike are in the Playground | 90 s |
| 5 | `app-fault` | Straight after | – |
| 6 | `alerts`, then `app-normal` | The stub shows both app alerts firing | 20 s |
| 7 | `logs-stop` | Straight after | – |
| 8 | `alerts`, then `logs-start` | The stub shows `NoLogActivity firing` | 65 s |
| 9 | `agent-stop` | The stub shows `NoLogActivity resolved` | 25 s |
| 10 | `alerts`, then `agent-start` | An `AgentHeartbeatMissing` card is in the Playground | 35 s |
| 11 | `tamper`, `reconcile`, `privacy`, `replay HighRejectRate` | Straight after; explain each result before running the next | – |
| 12 | `alerts` | You've finished explaining step 8 | 30 s |

Every command is `scripts\demo_windows.bat <command>`.

## 0. Before you start (5 minutes early, not on the clock)

1. Get the latest branch:

   ```bat
   git checkout Demo-Showcase-Extras
   git pull
   uv sync --all-packages
   ```

2. If Ollama only has `llama3.2:3b` (free-form questions need the name `llama3.2`):

   ```bat
   ollama cp llama3.2:3b llama3.2
   ```

3. Plug in the laptop and set it not to sleep.
4. Close any old demo windows, then start:

   ```bat
   scripts\demo_windows.bat stop
   scripts\demo_windows.bat
   ```

5. When the Playground opens, type **`hi`**. This makes it the chat that receives
   alert cards.
6. Arrange the screen as in the layout above.
7. Start a stopwatch: the anomaly baseline needs **3 minutes** of normal traffic
   before the burst.

Ideally start this just before you are introduced, so the 3-minute baseline runs during
your intro and step 2.

## Intro (about 1 minute)

**On screen:** the Playground and the main Command Prompt, with all component windows
visible behind for a moment.

> "Magic is UBS's trading application. Today, when orders start failing, support finds
> out from traders or by digging through raw FIX logs on the host. We built **Unified
> Telemetry Intelligence**. A lightweight agent on the Magic host reads the logs, turns
> them into **sanitised metrics**, raises **alerts** to Magic and Teams, and lets
> support **ask questions in plain English**, from Teams or from Copilot. Raw logs and
> FIX payloads never leave the host."

Point at each window as you name it:

| Window | What it is |
| --- | --- |
| 3 simulator | Stands in for Magic, writing `Fix.log` and `Application.log` |
| 4 agent | Runs on the Magic host, reads the logs, publishes metrics |
| 1 backend | Stores metrics, evaluates heartbeats, answers questions |
| 2 Magic callback STUB | Magic's callback endpoint, checks signatures |
| 5 Teams bot | Sends alert cards and answers chat |
| 6 MCP server | The endpoint Copilot connects to |
| 7 Teams App Test Tool / Playground | Teams, running locally |

## Step 1: Start the stack (already done)

**On screen:** bring the **agent** window forward briefly.

> "Each component runs in its own window. The agent reads the two log files. Notice it
> publishes counts and rates, not log lines."

## Step 2: Normal trading, 3-minute baseline (about 3 minutes)

**On screen:** the main Command Prompt.

```bat
scripts\demo_windows.bat ask "Why are Magic orders rejecting in the last 30 minutes?"
```

> "First, the headline question. Notice three things. It was **answered by rule**, not
> guessed by an LLM. It says the data is **complete**, 1 of 1 agents reporting. And it
> **cites** the exact query it ran."

**Fill the rest of the 3 minutes:**

1. Copilot path:

   ```bat
   scripts\demo_windows.bat ask
   ```

   > "That was Teams. Copilot reaches the same intelligence through our **MCP
   > server**, the standard protocol Copilot Studio uses. These six questions go
   > through the exact tool Copilot calls: rejections, order flow, alerts, trends,
   > agent health and parse health."

2. Optional, about 60 seconds, MCP Inspector (in the second Command Prompt):

   ```bat
   npx @modelcontextprotocol/inspector
   ```

   **On screen:** the Inspector browser tab, full screen. Set Transport to
   **Streamable HTTP**, the URL to `http://127.0.0.1:8765/mcp`, then click **Connect**
   and **List Tools**.

   > "This is what Copilot sees: a fixed set of **read-only** tools. Copilot can't run
   > arbitrary queries or touch the logs."

3. Agent health:

   ```bat
   scripts\demo_windows.bat health
   ```

   > "The agent watches itself too: lag per file, parse errors, failed callbacks,
   > queue depth, dropped events."

4. Optional: type the headline question into the Playground yourself.

   > "And the same question works straight from Teams."

> "Meanwhile the anomaly rules are learning what *normal* looks like for this system.
> That's why we wait three minutes."

**Next:** when the stopwatch passes 3 minutes, go back to the two-pane layout.

## Step 3: Reject burst (about 65 seconds)

```bat
scripts\demo_windows.bat burst
```

**On screen:** the two-pane layout. At about 5 seconds, bring the **Magic stub**
window forward next to the Playground.

What happens: rejects jump to 60%. The stub shows
`signed callback OK: HighRejectRate firing`. **A card appears in the Playground.**

> "Now Magic starts rejecting most orders. Within seconds **HighRejectRate** is
> pending, then firing. That's a fixed threshold. **RejectSpike** catches the sudden
> jump. Watch the stub: Magic receives a **signed callback**. The HMAC signature proves
> it really came from us. And support gets this card in Teams without anyone looking at
> a log."

Point at the card in the Playground: rule, severity, value, time.

At about 55 seconds:

> "**AbnormalRejectRate** is different. It's not a fixed threshold, it compares against
> the baseline it just learned."

**Next:** when the card is in the Playground and the stub shows
`AbnormalRejectRate firing`:

```bat
scripts\demo_windows.bat alerts
scripts\demo_windows.bat ask "Any alerts open for Magic?"
```

**On screen:** the main Command Prompt.

> "Here's every alert with its callback delivery status. And ask the bot now: the
> answer **names the live alert** and whether Magic got the callback."

## Step 4: Back to normal (about 90 seconds)

```bat
scripts\demo_windows.bat normal
```

**On screen:** the Playground, as the resolved cards arrive.

> "Rejects drop back to half a percent. Alerts don't just fire, they **resolve on their
> own**, and Magic and Teams are told, so nobody chases a problem that's already gone."

While you wait, scroll the Playground up to show the firing card and the resolved card
together.

**Next:** when the resolved cards for HighRejectRate and RejectSpike are in the
Playground, run `scripts\demo_windows.bat alerts`.

## Step 5: Application faults (about 20 seconds)

```bat
scripts\demo_windows.bat app-fault
```

**On screen:** the Magic stub window.

> "Not every problem is a FIX reject. Here the application log shows an
> **OutOfMemoryError**. **AppOutOfMemory** and **AppLogFailure** fire within seconds,
> from a different log file with different rules."

**Next:** when the stub shows both app alerts firing:

```bat
scripts\demo_windows.bat alerts
scripts\demo_windows.bat app-normal
```

## Step 6: Logs stop (about 2 minutes)

```bat
scripts\demo_windows.bat logs-stop
```

**On screen:** the two-pane layout. Point out that the **simulator window has
closed**.

> "The most dangerous failure is silence. If Magic stops logging, a naive system shows
> *zero rejects, all good*. We alert on **NoLogActivity**: a full minute with no new
> lines."

While you wait (about 60 seconds), this is a good moment for a question from the
audience, or to explain the app-fault alerts resolving.

**Next:** when the stub shows `NoLogActivity firing`:

```bat
scripts\demo_windows.bat alerts
scripts\demo_windows.bat logs-start
```

> "Logs are back..."

**Next:** wait until the stub shows `NoLogActivity resolved` (about 25 seconds).

> "...and it resolves."

Do step 7 only **after** NoLogActivity has resolved. The agent keeps alert state in
memory, so an alert still firing when it stops is never resolved.

## Step 7: Agent stops (about 40 seconds)

```bat
scripts\demo_windows.bat agent-stop
```

**On screen:** point out that the **agent window has closed**, then watch the
Playground. This alert comes from the backend, not the agent, so it appears as a Teams
card but not in the stub ("n/a" delivery in the alert table).

> "What if our own agent dies? The backend expects a **heartbeat**. When it stops, we
> raise **AgentHeartbeatMissing**, so we never mistake a dead monitor for a healthy
> system."

**Next:** when the `AgentHeartbeatMissing` card is in the Playground:

```bat
scripts\demo_windows.bat alerts
scripts\demo_windows.bat agent-start
```

> "On restart it **resumes from saved offsets**, so nothing is missed or counted
> twice."

## Step 8: Showcase (about 1 minute)

**On screen:** the main Command Prompt, full screen. Run one command at a time and
explain the result before running the next. At the tamper result, bring the **Magic
stub** forward to show the 401.

```bat
scripts\demo_windows.bat tamper
scripts\demo_windows.bat reconcile
scripts\demo_windows.bat privacy
scripts\demo_windows.bat replay HighRejectRate
```

| On screen | Say |
| --- | --- |
| **Tamper: 401** | "Someone forges a callback. Magic rejects it with 401, because the signature doesn't match." |
| **Reconcile: lost 0 (exact)** | "We count every order in every rotated log file and compare with the backend. Exactly the same, through log rotation and an agent restart: **zero lost**." |
| **Privacy: 13 passed, none found** | "Our leak sentinel checks that no order IDs or reject text leave the host. Order IDs are **hashed**. We also scan this run's live events, alerts and callbacks: thousands of raw IDs in the logs, none in our data." |
| **Replay HighRejectRate** | "**Rule test mode**: support can test a rule against real historical logs (pending, firing, resolved) with **dispatched: 0**. Nothing is sent to Magic." |

## Step 9: Summary (about 30 seconds)

```bat
scripts\demo_windows.bat alerts
```

**On screen:** the final alert table, then the Playground scrolled through all the
cards.

> "Everything we triggered has resolved on its own."

## Extras after the storyline (about 2 minutes, if time allows)

**On screen:** the main Command Prompt next to the Playground.

| Command | Time | Show | Say |
| --- | --- | --- | --- |
| `scripts\demo_windows.bat reload strict`, wait for the alert, then `scripts\demo_windows.bat reload reset` | ≈45 s | Command Prompt, then the card in the Playground | "Rules are config, not code. I tighten the threshold, and the agent **reloads it live with no restart**. The alert fires on normal traffic. I put it back and it clears." |
| `scripts\demo_windows.bat outage 30` | ≈40 s | Command Prompt, full screen | "A 30-second network outage plus a log rotation plus a restart, checked against ground truth: **exact counts**, about 1 s to visibility, and it resumes in under 0.1 s." |
| `scripts\demo_windows.bat stub-stop`, `burst`, `alerts`, `stub-start` | ≈1 min | Command Prompt (delivery column) | "If Magic's endpoint is down, callbacks **retry with backoff** (5 attempts) and we show the delivery status." Only if you have spare time. |

Run `ask` before `outage`. After an outage, answers say the data is partial for a
while.

## Close (about 1 minute): say the limits out loud

**On screen:** the Playground with the cards, or your closing slide.

> "Honest limits. Teams here is the local Playground, not a real tenant. That's next
> (UBS-142). Copilot connects through the same MCP endpoint, but we haven't connected a
> live Copilot Studio tenant. Free-form questions go to a small local LLM, so on stage
> we use the rule-matched questions. And alert state is held in memory, so a restart
> mid-alert is a known gap."

## When you're done

```bat
scripts\demo_windows.bat stop
```

## If something goes wrong

| Problem | Fix |
| --- | --- |
| No cards in the Playground | Type `hi` in the Playground. The first chat to say something receives the cards |
| You ran a command too early | Keep going: run `scripts\demo_windows.bat alerts` a few seconds later to show the alert |
| NoLogActivity fires when you didn't stop the logs | `scripts\demo_windows.bat logs-start` |
| A port is already in use | `scripts\demo_windows.bat stop`, then start again |
| Abnormal* not in the table yet | Wait. It needs about 55–70 s after the burst |
| A free-form question answers 0 or oddly | Use the suggested questions; free-form goes to the small LLM |

## Features shown beyond the basic demo

The basic demo is: logs, then agent, then backend, then alert, then a Teams card. On
top of that you show:

| Feature | Where | Why it matters |
| --- | --- | --- |
| Natural-language answers with rule/LLM label, data completeness and citations | Step 2, `ask` | Trustworthy AI: says how it answered and from what data |
| **Copilot via MCP** (read-only tools) | Step 2 extras | Enterprise AI integration, governed access |
| Agent self-health | `health` | The monitor is monitored |
| Anomaly detection against a learned baseline (Abnormal*) | Step 3 | Beyond fixed thresholds |
| Context-aware answers (names the live alert and callback status) | Step 3 | Chat and alerts are joined up |
| HMAC-signed callbacks plus tamper rejection | Steps 3 and 8 | Security of the alert channel |
| Auto-resolve with resolved notifications | Step 4 | Less alert fatigue |
| Multi-log rules (Application.log faults) | Step 5 | Not just FIX |
| Silence detection (NoLogActivity) | Step 6 | Catches the "zero = fine" trap |
| Heartbeat monitoring plus offset resume | Step 7 | Resilience, no double counting |
| Exact reconciliation (lost 0) across rotation and restart | Step 8 | Data integrity |
| Privacy: hashed IDs, leak sentinel, live leak scan | Step 8 | UBS data-handling requirement |
| Rule test mode (replay, dispatched 0) | Step 8 | Safe rule tuning |
| Live rule reload | Extras | Ops-friendly config |
| Outage harness with exact counts | Extras | Resilience under failure |
| Callback retries and delivery status | Extras | Reliable delivery to Magic |
