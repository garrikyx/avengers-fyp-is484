# Demo script: macOS

Presenter script for the 20-minute slot: what to type, when to press Enter, what to
put on screen, and what to say. Total is about 16–17 minutes, leaving 3–4 minutes for
questions.

Windows version: [demo-script-windows.md](demo-script-windows.md).

> On Linux the same commands work, but there is no Terminal.app: start with
> `DEMO_TMUX=1 scripts/demo_mac/demo.sh run` to get tmux panes instead of windows.

## How you run it

- **Main Terminal:** `scripts/demo_mac/demo.sh run`, without `--auto`. Step 1 and the
  headline question run straight away. After that, the script stops at each
  `[press Enter]` prompt. **Pressing Enter ends the wait and starts the next action**,
  so press it only when the thing you are waiting for has appeared (cues below).
- **Second Terminal tab** in the same folder: for the extra commands.
- To rehearse hands-free: `scripts/demo_mac/demo.sh run --auto` (about 9.5 minutes,
  storyline only).

## Screen layout (set this up before you start)

What the audience sees should tell the story without you pointing at small text.

```text
+------------------------------+------------------------------+
|                              |                              |
|   Playground (Teams)         |   Main Terminal              |
|   alert cards + chat         |   storyline: answers,        |
|                              |   alert tables, results      |
|                              |                              |
+------------------------------+------------------------------+
   Behind, ready to bring forward (Cmd+Tab or click):
   "2 Magic callback STUB"   "4 agent"   "3 simulator"   second tab
```

- **Left half:** the Playground. This is what support staff would see, so it's the
  main stage.
- **Right half:** the main Terminal running the storyline.
- **Behind:** the Magic stub window (signed callbacks, 401), the agent window, the
  simulator window, and your second tab. Bring one forward only when the script says
  so, then go back to the two-pane layout.
- Make the text big enough for the back of the room: in each Terminal you show, press
  **Cmd and +** two or three times.
- Turn on **Do Not Disturb** and close other apps (chat, mail) so nothing pops up.
- Minimise the backend, Teams bot and MCP server windows. You name them in the intro
  but don't need them after that.

## Enter cheat sheet

Press Enter only when the cue is met. If you are still talking, keep talking: waiting
longer never hurts.

| # | Prompt you see | Press Enter when | At least |
| --- | --- | --- | --- |
| 1 | `Show the playground and the metrics while the baseline builds` | You've done the step 2 extras **and** 3 minutes have passed since the headline answer | 3 min |
| 2 | `HighRejectRate, RejectSpike and the Abnormal* rules fire` | A red card is in the Playground **and** the stub shows `AbnormalRejectRate firing` | 65 s |
| 3 | `The burst ages out of the 1-minute window` | **Resolved** cards for HighRejectRate and RejectSpike are in the Playground | 90 s |
| 4 | `AppOutOfMemory and AppLogFailure fire` | The stub shows both app alerts firing | 20 s |
| 5 | `A full minute with no new lines, then NoLogActivity` | The stub shows `NoLogActivity firing` | 80 s |
| 6 | `Lines flow again; NoLogActivity resolves` | The stub shows `NoLogActivity resolved` | 25 s |
| 7 | `The backend notices the missing heartbeat` | An `AgentHeartbeatMissing` card is in the Playground (the backend raises it, so it doesn't go to the stub) | 35 s |
| 8 | `Everything resolves` | You've finished explaining step 8's results | 30 s |

After Enter 7, step 8 runs by itself (about 30 seconds of output) and stops at prompt 8.

## 0. Before you start (5 minutes early, not on the clock)

1. In a separate Terminal window, keep the Mac awake and leave it open:

   ```bash
   caffeinate -d
   ```

2. Close any old demo windows:

   ```bash
   osascript -e 'tell application "Terminal" to close (every window whose name contains "FYP demo")'
   ```

3. Start the storyline in your main Terminal:

   ```bash
   cd ~/Documents/School/FYP
   scripts/demo_mac/demo.sh run
   ```

   The windows open, it waits for orders to flow, asks the headline question, and stops
   at prompt 1. **Don't press Enter yet.**

4. When the Playground opens, type **`hi`**. This makes it the chat that receives
   alert cards.
5. Arrange the screen as in the layout above.

Ideally start this just before you are introduced, so the 3-minute baseline runs during
your intro and step 2.

## Intro (about 1 minute)

**On screen:** the Playground and the main Terminal, with all component windows
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
| Playground | Teams, running locally |

## Step 1: Start the stack (already done)

**On screen:** bring the **agent** window forward briefly.

> "Each component runs in its own window. The agent reads the two log files. Notice it
> publishes counts and rates, not log lines."

## Step 2: Normal trading, 3-minute baseline (about 3 minutes)

**On screen:** the main Terminal, with the headline answer highlighted.

> "First, the headline question: *Why are Magic orders rejecting in the last 30
> minutes?* Notice three things. It was **answered by rule**, not guessed by an LLM. It
> says the data is **complete**, 1 of 1 agents reporting. And it **cites** the exact
> query it ran."

**Fill the 3-minute wait from the second tab** (bring it forward):

1. Copilot path:

   ```bash
   scripts/demo_mac/demo.sh ask
   ```

   > "That was Teams. Copilot reaches the same intelligence through our **MCP
   > server**, the standard protocol Copilot Studio uses. These six questions go
   > through the exact tool Copilot calls: rejections, order flow, alerts, trends,
   > agent health and parse health."

2. Optional, about 60 seconds, MCP Inspector:

   ```bash
   npx @modelcontextprotocol/inspector
   ```

   **On screen:** the Inspector browser tab, full screen. Set Transport to
   **Streamable HTTP**, the URL to `http://127.0.0.1:8765/mcp`, then click **Connect**
   and **List Tools**.

   > "This is what Copilot sees: a fixed set of **read-only** tools. Copilot can't run
   > arbitrary queries or touch the logs."

3. Agent health:

   ```bash
   scripts/demo_mac/demo.sh health
   ```

   > "The agent watches itself too: lag per file, parse errors, failed callbacks,
   > queue depth, dropped events."

4. Optional: type the headline question into the Playground yourself.

   > "And the same question works straight from Teams."

> "Meanwhile the anomaly rules are learning what *normal* looks like for this system.
> That's why we wait three minutes."

**Press Enter (prompt 1)** in the main Terminal when 3 minutes have passed. Go back to
the two-pane layout first.

## Step 3: Reject burst (about 65 seconds)

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

**Press Enter (prompt 2)** when the card is in the Playground and the stub shows
`AbnormalRejectRate firing`.

**On screen:** the main Terminal. It prints the alert table and the "Any alerts open
for Magic?" answer.

> "Here's every alert with its callback delivery status. And ask the bot now: the
> answer **names the live alert** and whether Magic got the callback."

Step 4 starts straight away.

## Step 4: Back to normal (about 90 seconds)

**On screen:** the Playground, as the resolved cards arrive.

> "Rejects drop back to half a percent. Alerts don't just fire, they **resolve on their
> own**, and Magic and Teams are told, so nobody chases a problem that's already gone."

While you wait, scroll the Playground up to show the firing card and the resolved card
together.

**Press Enter (prompt 3)** when the resolved cards for HighRejectRate and RejectSpike
are in the Playground. The main Terminal prints the alert table, then step 5 starts.

## Step 5: Application faults (about 20 seconds)

**On screen:** the Magic stub window.

> "Not every problem is a FIX reject. Here the application log shows an
> **OutOfMemoryError**. **AppOutOfMemory** and **AppLogFailure** fire within seconds,
> from a different log file with different rules."

**Press Enter (prompt 4)** when the stub shows both app alerts firing. The faults stop,
and step 6 starts straight away.

## Step 6: Logs stop (about 2 minutes)

**On screen:** the two-pane layout. Point out that the **simulator window has
closed**.

> "The most dangerous failure is silence. If Magic stops logging, a naive system shows
> *zero rejects, all good*. We alert on **NoLogActivity**: a full minute with no new
> lines."

While you wait (about 60 seconds), this is a good moment for a question from the
audience, or to explain the app-fault alerts resolving.

**Press Enter (prompt 5)** when the stub shows `NoLogActivity firing`. The log
generator restarts.

> "Logs are back..."

**Press Enter (prompt 6)** when the stub shows `NoLogActivity resolved`.

> "...and it resolves."

Step 7 starts straight away.

## Step 7: Agent stops (about 40 seconds)

**On screen:** point out that the **agent window has closed**, then watch the
Playground. This alert comes from the backend, not the agent, so it appears as a Teams
card but not in the stub ("n/a" delivery in the alert table).

> "What if our own agent dies? The backend expects a **heartbeat**. When it stops, we
> raise **AgentHeartbeatMissing**, so we never mistake a dead monitor for a healthy
> system."

**Press Enter (prompt 7)** when the `AgentHeartbeatMissing` card is in the Playground.
The agent restarts.

> "On restart it **resumes from saved offsets**, so nothing is missed or counted
> twice."

## Step 8: Showcase (about 30 seconds, all automatic)

**On screen:** the main Terminal, full screen. Scroll back to each result as you
explain it. At the tamper result, bring the **Magic stub** forward to show the 401.

| On screen | Say |
| --- | --- |
| **Tamper: 401** | "Someone forges a callback. Magic rejects it with 401, because the signature doesn't match." |
| **Reconcile: lost 0 (exact)** | "We count every order in every rotated log file and compare with the backend. Exactly the same, through log rotation and an agent restart: **zero lost**." |
| **Privacy: 13 passed, none found** | "Our leak sentinel checks that no order IDs or reject text leave the host. Order IDs are **hashed**. We also scan this run's live events, alerts and callbacks: thousands of raw IDs in the logs, none in our data." |
| **Replay HighRejectRate** | "**Rule test mode**: support can test a rule against real historical logs (pending, firing, resolved) with **dispatched: 0**. Nothing is sent to Magic." |

**Press Enter (prompt 8)** when you've finished explaining these.

## Step 9: Summary (about 30 seconds)

**On screen:** the main Terminal's final alert table, then the Playground scrolled
through all the cards.

> "Everything we triggered has resolved on its own."

## Extras after the storyline (about 2 minutes, if time allows)

**On screen:** the second tab next to the Playground. The stack keeps running after
step 9.

| Command | Time | Show | Say |
| --- | --- | --- | --- |
| `scripts/demo_mac/demo.sh reload strict`, wait for the alert, then `scripts/demo_mac/demo.sh reload reset` | ≈45 s | Second tab, then the card in the Playground | "Rules are config, not code. I tighten the threshold, and the agent **reloads it live with no restart**. The alert fires on normal traffic. I put it back and it clears." |
| `scripts/demo_mac/demo.sh outage 30` | ≈40 s | Second tab, full screen | "A 30-second network outage plus a log rotation plus a restart, checked against ground truth: **exact counts**, about 1 s to visibility, and it resumes in under 0.1 s." |
| `scripts/demo_mac/demo.sh stub-stop`, `burst`, `alerts`, `stub-start` | ≈1 min | Second tab (delivery column) | "If Magic's endpoint is down, callbacks **retry with backoff** (5 attempts) and we show the delivery status." Only if you have spare time. |

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

```bash
scripts/demo_mac/demo.sh stop
osascript -e 'tell application "Terminal" to close (every window whose name contains "FYP demo")'
```

## If something goes wrong

| Problem | Fix |
| --- | --- |
| No cards in the Playground | Type `hi` in the Playground. The first chat to say something receives the cards |
| You pressed Enter too early | Keep going: run `scripts/demo_mac/demo.sh alerts` in the second tab a few seconds later to show the alert |
| NoLogActivity fires when you didn't stop the logs | `scripts/demo_mac/demo.sh logs-start` |
| "Preflight refused": something is still running | `scripts/demo_mac/demo.sh stop`, then start again |
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
