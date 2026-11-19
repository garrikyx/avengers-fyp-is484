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
- **Alternative:** the guided demo, which waits for each event by itself. See
  [Guided demo](#guided-demo-scriptsdemo) below.
- **Your part, the heartbeat:** the full talk track is in
  [Heartbeat: full talk track](#heartbeat-full-talk-track-your-part). Use it at step 7
  here, or step 8 of the guided demo.

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

### Your turn: what makes a reject rate "high"

Say this while the first card is on screen. Full talk track and numbers:
[Reject alerts: full talk track](#reject-alerts-full-talk-track-your-part).

> "What makes a rejection rate high, and what stops a single reject from waking us up?
> We divide rejected orders by acknowledged plus rejected orders in the window. If 18
> of 100 answered orders are rejected, that's 18%. That's above our warning tier of 3%
> and our critical tier of 5%, so it fires as critical. In the regular profile the rate
> must stay above the threshold for two minutes, with at least 20 answered orders. With
> fewer than 20 answered orders, the rate is unavailable rather than zero or 100%. We
> also track volume separately. For example, 51 rejects among 2,051 answered orders is
> only about 2.49%, below the rate threshold, but it's more than 50 rejects in a
> minute, so RejectSpike catches it."

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

This is your part. For the full sentences, use
[Heartbeat: full talk track](#heartbeat-full-talk-track-your-part). The short version:

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

## Guided demo (`scripts.demo`)

A different, self-pacing storyline. The script **waits for each event by itself** and
only shows a `>> … [Enter]` prompt once that event has happened. So explain what's on
screen, then press Enter. Pressing late is always safe.

### Start it

1. Main Terminal:

   ```bash
   cd ~/Documents/School/FYP
   uv run python -m scripts.demo --showcase
   ```

2. Second tab, for the Teams Playground (the guided demo doesn't start it):

   ```bash
   scripts/demo_mac/playground.sh
   ```

   When it opens in your browser, type **`hi`** so the alert cards come through.

### 1. Start (done)

**Say:** "Magic is UBS's trading application. Today, when orders start failing,
support finds out from traders or by digging through raw FIX logs. We built Unified
Telemetry Intelligence. A lightweight agent sits on the Magic host and turns its logs
into sanitised metrics. It alerts Magic and Teams, and lets support ask questions in
plain English. Raw logs never leave the host. You're seeing every real component
running locally, with a log generator standing in for Magic."

⏎ **Press Enter at** `Next: Normal trading`

### 2. Normal trading

**On screen:** counts print three times, then agent health.

**Say:** "This is normal trading: orders submitted, acknowledged, rejected, and the
reject rate, about half a percent. The backend only ever gets these counters, never the
log lines. The agent also reports its own health, so we know the monitor itself is
working."

⏎ **Press Enter at** `Next: Reject burst`

### 3. Reject burst

**On screen:** prints "visible after X s".

**Say:** "Now Magic suddenly starts rejecting most orders. Our requirement is that
support sees it within 5 seconds. It showed up in X seconds."

⏎ **Press Enter at** `Next: HighRejectRate alert`

### 4. Alert (about 15 s)

**On screen:** the callback reaches the Magic stub, a card appears in Teams, then a
tampered callback gets 401.

**Say:** "The HighRejectRate rule fires. Magic gets a callback signed with a shared
secret, so it can prove the alert came from us. Support gets this card in Teams without
opening a log. A forged callback is rejected with 401."

**Your turn:** while the card is on screen, use the paragraph in
[Your turn: what makes a reject rate "high"](#your-turn-what-makes-a-reject-rate-high).

⏎ **Press Enter at** `Stop the burst and watch it resolve`

### 5. Back to normal (about 65 s wait)

**Say:** "Rejects drop back. The rule looks at a 1-minute window, so once the burst ages
out, the alert steps down and resolves on its own, and Magic and Teams are told."

This wait is a good time to take a question.

⏎ **Press Enter at** `Next: Ask in plain English`

### 6. Plain-English question

**Say:** "Support can just ask why orders are rejecting. It was answered by a rule, not
guessed by an AI. It says whether the data is complete, and it shows the exact numbers
it used."

At `Ask the question in the Playground now`, type
`Why are Magic orders rejecting in the last 30 minutes?` in Teams and say: "Same answer
in Teams, including the alert and whether Magic got the callback."

⏎ **Press Enter**

### 7. Rotation and restart

**Say:** "Logs rotate and agents get restarted for upgrades, so I'll stop our agent
while Magic keeps logging."

⏎ **Press Enter at** `Agent is down; logs keep growing`

**Say:** "It saved its position in every log file, so it picks up exactly where it
stopped. Reconcile counts every order in every log file, rotated ones included, against
the backend. Zero lost."

Read the number before you say it. If it's negative, say a few lines were re-read after
the restart and nothing was lost.

⏎ **Press Enter at** `Next: Agent stops`

### 8. Agent dies (about 25 s, twice): your part

Use [Heartbeat: full talk track](#heartbeat-full-talk-track-your-part) for the full
sentences. The short version:

**Say:** "What if our own agent crashes? A dead process can't report its own death, so
the backend expects a heartbeat and raises AgentHeartbeatMissing on its own clock. We
never mistake a dead monitor for a quiet, healthy system."

⏎ **Press Enter at** `Bring the agent back`

**Say:** "It resolves. A second outage gets its own alert ID, so incidents are never
merged."

⏎ **Press Enter at** `Bring the agent back again`

### 9. Privacy

**Say:** "Order IDs are hashed on the host and reject text is dropped. We scanned
everything that left the host, and none of the raw IDs or reject text appear anywhere."

⏎ **Press Enter at** `Next: rule test mode`

### 10. Rule test mode

**Say:** "Engineers can test a new rule against real past logs before turning it on.
This replays today's logs in seconds and shows when it would fire and resolve.
'Dispatched: 0' means nothing was sent."

## Reject alerts: full talk track (your part)

Use this at the first alert: step 3 of the `demo.sh` storyline, or step 4 of the guided
demo. Numbers come from `config/rules.yaml` (regular profile),
`config/demo/rules.yaml` (demo profile) and spec 004 FR-QRY-010.

### How it works (for you)

**Reject rate** = rejected ÷ (acknowledged + rejected), over the rule's window. Orders
still waiting for an answer don't count, so the rate only covers orders Magic has
answered.

| | HighRejectRate (a rate) | RejectSpike (a volume) |
| --- | --- | --- |
| Measures | Reject rate | Number of rejects |
| Warning | above 3% | more than 50 in 1 minute |
| Critical | above 5% | none |
| Window: regular / demo | 5 min / 1 min | 1 min / 1 min |
| Minimum answered orders: regular / demo | 20 / 10 | none |
| Must hold for: regular / demo | 2 min / 10 s | 60 s (default) / 10 s |
| Resolves after: regular / demo | 5 min / 15 s | 5 min (default) / 15 s |

- **Below the minimum** answered orders, the rate is **unavailable** (null), not 0%
  and not 100%. One reject out of one order is not a 100% reject rate (FR-QRY-010).
- The **"for" time** stops one bad moment from paging anyone: the rate has to stay high.
- The **two rules cover each other's blind spots.** On heavy trading, many rejects can
  still be a low rate, which RejectSpike catches. On light trading, a high rate can be
  few rejects, which HighRejectRate catches.

Worked examples:

| Answered orders | Rejected | Rate | HighRejectRate | RejectSpike (in 1 min) |
| --- | --- | --- | --- | --- |
| 100 | 18 | 18% | Critical (above 5%) | No (18 is not more than 50) |
| 2,051 | 51 | 2.49% | No (below 3%) | **Yes** (51 is more than 50) |
| 10 | 3 | Unavailable (fewer than 20 in the regular profile) | No | No |
| Demo burst | about 60% | about 60% | Critical | Yes |

### What to say

> "What makes a rejection rate high, and what stops a single reject from waking us up?"
>
> "We divide rejected orders by acknowledged plus rejected orders in the window, so
> we're only looking at orders Magic has actually answered. If 18 of 100 answered
> orders are rejected, that's 18%. That's above our warning tier of 3% and our critical
> tier of 5%, so it fires as critical."
>
> "Two things stop a single reject from waking anyone up. First, in the regular
> profile the rate has to stay above the threshold for two minutes, so one bad moment
> doesn't page anyone. Second, we need at least 20 answered orders in the window. With
> fewer, the rate is unavailable, not zero and not 100%, so one reject out of one
> order is never treated as a 100% reject rate."
>
> "We also track volume separately. For example, 51 rejects among 2,051 answered orders
> is only about 2.49%, below the rate threshold. But that's more than 50 rejects in a
> minute, so RejectSpike fires. The two rules cover each other: the rate catches
> problems on quiet days, and the volume catches them on busy days."
>
> "For the demo we shortened the timings, a one-minute window and ten seconds above
> the threshold, so you can see it happen live."

### Likely questions

| Question | Answer |
| --- | --- |
| Why not divide by all submitted orders? | Orders still waiting for an answer aren't failures yet. Using answered orders means a slow Magic doesn't dilute the rate. |
| Why 3% and 5%? | They're the configured tiers, and they're config, not code. `reload strict` shows a threshold change taking effect live without a restart. |
| What if rejects stop briefly in the middle? | The alert doesn't resolve until the rate stays below the threshold for the resolve time (5 minutes in the regular profile), so it doesn't flap on and off. |
| Why didn't the card say warning first? | At about 60% the rate is over both tiers, so it goes straight to critical. As it falls back it steps down to warning, then resolves. |

## Heartbeat: full talk track (your part)

Use this at step 7 of the `demo.sh` storyline, or step 8 of the guided demo. It runs
about 2 minutes with the waits. The numbers below come from `config/demo/agent.yaml`,
`config/demo/backend.yaml` and `heartbeat_monitor.py`.

### How it works (for you)

| Piece | What it does | Demo value | Production default |
| --- | --- | --- | --- |
| Agent heartbeat | The agent sends a small health report to the backend on a timer | Every 5 s | Every 10 s (`config/agent.yaml`) |
| Backend registry | Remembers when it last heard from each agent | In memory | In memory |
| Heartbeat monitor | Checks every agent's last heartbeat on the backend's own clock | Every 10 s | Every 10 s |
| Threshold | No heartbeat for longer than this means the agent is "missing" | 20 s (4 missed heartbeats) | 60 s (6 missed heartbeats) |
| Alert | `AgentHeartbeatMissing`, severity critical, raised by the **backend** | Fires 20–30 s after the stop | 60–70 s |
| Resolve | The first fresh heartbeat resolves it immediately, without waiting for the next check | Within ~5 s of restart | Same |
| Alert ID | Stays the same for one outage; a new outage gets a new ID | | |
| Delivery | Teams card. No Magic callback, so the alert table shows "n/a" | | |

What the heartbeat carries: agent ID and version, uptime, status (healthy, degraded or
unhealthy), each log file's position, lag and rotations, parse errors, callback
failures, publish queue depth, dropped events, active alerts, and CPU and memory use.
It carries **no log lines and no order data**.

Requirements: FR-RUL-030 and FR-QRY-018 (backend-owned AgentHeartbeatMissing),
FR-QRY-019 and UBS-136 (a new ID for each outage), FR-QRY-015 (stale agents make the
data "partial"), UAT-10.

### What to say

**1. Hand-over** (before you stop the agent):

> "I worked on agent health monitoring, so I'll take you through this part in a bit
> more detail."

**2. The problem:**

> "Everything you've seen so far depends on our agent running on the Magic host. So
> the obvious question is: what happens if the agent itself fails? The process might
> crash, the host might be rebooted, or someone might stop it for an upgrade."
>
> "The tricky part is that a dead process can't tell anyone it's dead. If we relied on
> the agent to report its own failure, a crash would look exactly like a quiet, healthy
> system: no alerts, no rejects, nothing. For a trading application, that silence is
> the most dangerous state to be in."

**3. The solution:**

> "So we turn it around. Every five seconds, the agent sends the backend a heartbeat.
> It's a small health report: the agent's version, how long it's been running, where
> it is in each log file, how far behind it is, parse errors, failed callbacks, its
> queue, and its CPU and memory. No log lines and no order data, just health."
>
> "The backend remembers when it last heard from each agent, and it checks every ten
> seconds on its own clock. If an agent has been silent for twenty seconds, that's four
> missed heartbeats, the backend raises AgentHeartbeatMissing as a critical alert. In
> production it's a heartbeat every ten seconds and a sixty-second threshold; we
> shortened both for the demo."

**4. Stop the agent** (press Enter, or run `agent-stop`):

> "I'm stopping the agent now. Magic keeps trading and writing logs. The only thing
> that's gone is our monitor."

While you wait (20–30 s), point at the closed agent window, and optionally run this in
the second tab:

```bash
curl -s http://127.0.0.1:8080/telemetry/health/agents
```

> "Here you can watch the backend's view: the heartbeat age keeps climbing, and once
> it passes twenty seconds the status turns to missing."

**5. The alert arrives** (card in the Playground):

> "There it is. The card says there's been no heartbeat for that many seconds, against
> a threshold of twenty. Notice that it came from the backend, not the agent, and
> that's the whole point: the thing that failed isn't the thing that has to report it.
> It goes to Teams. The delivery to Magic shows 'n/a' because this is the backend
> raising it, not an agent callback."

**6. Bring the agent back** (press Enter, or run `agent-start`):

> "Now I'll bring the agent back. As soon as its first fresh heartbeat arrives, the
> backend resolves the alert straight away; it doesn't wait for the next check. And
> because the agent saved its position in every log file, it picks up exactly where it
> stopped, so the lines Magic wrote while it was down are still counted."

**7. Second outage** (guided demo only):

> "Let me do that once more. This second outage gets a new alert ID. Each outage is its
> own incident, so support can see this agent went down twice, rather than one long
> alert hiding a pattern."

**8. Why it matters:**

> "The same heartbeat also drives the 'data complete' label you saw in the answers
> earlier. If an agent's heartbeat goes stale, every answer says the data is partial,
> instead of quietly giving a number that's missing part of the picture."

### Likely questions

| Question | Answer |
| --- | --- |
| Why not just check whether the process is running? | The backend is on a different machine. A heartbeat proves the agent is alive, working **and** able to reach us, and it carries the health details. A running process that is stuck or cut off would pass a process check. |
| What if the network drops but the agent is fine? | The alert fires, which is correct, because data isn't reaching us. The agent buffers and sends everything once the link is back; the outage harness shows exact counts after a 30 s outage. |
| Won't it raise false alarms? | It needs four missed heartbeats in a row in the demo, and six in production (a heartbeat every 10 s, 60 s threshold). Both the interval and the threshold are config. |
| What if the backend restarts? | The registry is in memory, so it starts empty. Agents reappear with their next heartbeat, within 5 s. An outage that started before the restart isn't reported as resolved, which is a known limit. |
| Why is it critical severity? | While it's firing we're blind to Magic: no reject alerts, no answers we can trust. |
| Why 5 s and 20 s? | Short enough to show on stage. Production uses a heartbeat every 10 s and a 60 s threshold to tolerate brief pauses. |

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
