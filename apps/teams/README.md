# Teams bot

Lets you ask telemetry questions in a Teams-style chat. The bot forwards the message to
the backend's `POST /telemetry/nl/query` and replies with an Adaptive Card (headline,
breakdown, alert badge, caveats, "Show query"). It only talks to the backend API, never
to Redis or any store. Design: spec 008 §5–6,
[ADR 0009](../../docs/adr/0009-m365-agents-sdk-for-teams-bot.md).

The bot sends no backend credentials (POC decision, spec 009 §3.3; per-user auth is
UBS-135). Microsoft's own app registration and incoming-message validation are still
required for real Teams.

## Run it locally (5 terminals, all from the repo root)

**Prerequisite:** Ollama running with `llama3.2` pulled, and Node.js for step 5. See the
[root README](../../README.md#prerequisites); `make ollama-check` confirms it.

Start them in this order. After step 3, wait about 30 seconds so the backend has data.
Each step shows its `make` shortcut and the full command.

**1. Backend.** The API that answers questions (public API on :8080). The log should
show `ollama model llama3.2 is loaded` within a few seconds.

```sh
make backend-run
# or: uv run telemetry-backend --config config/backend.yaml
```

**2. Simulator.** Writes fake Magic logs (`logs/Fix.log`, `logs/Application.log`) with orders, fills and rejects.

```sh
make simulator-run
# or: uv run python apps/simulator/src/simulator/mock_logger.py
```

**3. Agent.** Reads those logs, turns them into metrics, and sends them to the backend every ~10s.

```sh
make agent-run
# or: uv run telemetry-agent --config config/agent.yaml
```

**4. Teams bot.** The bot itself, listening on :3978. The dummy credentials plus `ANONYMOUS_ALLOWED=true` let it run without an Azure app. **Dev only, never use this on a deployed bot.**

```sh
make teams-run
# or:
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=00000000-0000-0000-0000-000000000000 \
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=dummy \
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=00000000-0000-0000-0000-000000000000 \
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED=true \
uv run telemetry-teams
```

**5. Agents Playground.** Microsoft's local Teams-style chat window, pointed at the bot. Needs Node; the first run downloads the tool.

```sh
make playground
# or: npx @microsoft/teams-app-test-tool start -e http://localhost:3978/api/messages -c msteams
```

Open http://localhost:56150. The log panel on the right should say "Connected". Type a
question in the box at the bottom.

If every answer says "0 submitted", restart the simulator: one started before the
order-flow change writes lines without orders.

## Questions to try

The backend recognises ten kinds of question. Every phrasing below was sent to a running
backend and answered by its rule matcher, with no LLM involved. The simulator and the agent
must both be running: a short window like "last 15 minutes" is rejected ("available
range is ...") when no data arrived in that window.

| Ask about | Try |
| --- | --- |
| Why orders are rejecting | "Why are orders rejecting in the last 30 minutes?"<br>"What's the reject rate for the last 15 minutes?"<br>"Reject rate on instance magic-prod-01" |
| Overall order flow | "How is Magic doing in the last 10 minutes?"<br>"How is Magic doing today?"<br>"Order flow summary for the last 1 hour" |
| Alerts | "Any alerts open for Magic?"<br>"Show active alerts"<br>"Any alerts on magic-prod-01?" |
| FIX sessions | "Are the FIX sessions up?"<br>"Session status for the last 1 hour" |
| Is telemetry working | "Is telemetry actually working?"<br>"Agent health" |
| Parse problems | "Are we failing to parse anything?"<br>"Show parse errors in the last 1 hour" |
| Over time | "Show rejects over the last 1 hour"<br>"Reject trend over the last 2 hours" |

Also try:

- Tap **Show query** on any card to see how the question was interpreted.
- "hi", "thanks" or "help" for an instant reply with suggested-question buttons. Tap a
  button to ask it.
- An off-topic question ("what's the weather like") for a short reply that steers back
  to Magic, with the same buttons.
- A phrasing the rules don't know ("Is anything firing on Magic that I should worry
  about?") for an answer interpreted by the LLM. "Show query" shows `source: llm`.
- Quit Ollama and ask "is it slow". The answer says it was interpreted by keyword
  matching. Nothing times out.
- Stop the backend and ask again, for the error card.
- Wait a few minutes with the simulator running, then ask "Any alerts open for Magic?".
  An alert only shows if a rule has fired; the first card has none.

**Known issues (backend, not the bot):**

- "What's rejecting on AAPL?" answers "0 rejects" for every symbol. Filtering by symbol
  returns nothing even when that symbol has rejects.
- "Are rejects worse than yesterday?" fails with "fromUtc is not before toUtc": yesterday
  is outside the 6-hour data window.
- The breakdown by reject reason shows "All": the backend can't match the agent's
  `rejectReason` and `instanceId` names when grouping.

**Time wording matters.** These are understood: "last 15 minutes", "last 60 minutes",
"last 2 hours", "last 1 hour", "today" (capped at 6 hours of data), "since 09:00", "between
09:00 and 10:00". These are **not**: "last hour", "past hour", "since 9am", "between 9am
and 10am". They silently use the default 30 minutes, and the card's caveat line says
"Using default time range of last 30m."

Phrasings the rules don't match, such as "give me a rejection summary", go to the local
Ollama model, which usually takes 1 to 5 seconds. If it can't answer within 6 seconds,
the backend falls back to keyword matching or replies with suggested questions.
Some answers (latency, sessions, trend) are short one-liners until UBS-99's full answer
renderer lands.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `TELEMETRY_BACKEND_URL` | `http://127.0.0.1:8080` | Backend public API base URL |
| `TEAMS_DEFAULT_APPLICATION` | `Magic` | Application every question is scoped to |
| `TEAMS_DEFAULT_TIMEZONE` | `Asia/Singapore` | Used when Teams does not report the user's timezone |
| `TEAMS_BACKEND_TIMEOUT_SECONDS` | `12` | Backend request timeout; keep above the backend `nl.llm.timeout` (6s) |
| `TEAMS_BIND_HOST` | `127.0.0.1` | Interface to listen on (use `0.0.0.0` in a container) |
| `PORT` | `3978` | Port the bot listens on |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID` | | Azure app (client) ID |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET` | | Azure app secret, never commit |
| `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID` | | Azure tenant ID |

A `.env` file in the working directory is loaded automatically (git-ignored; see
`.env.example`).

## Real Teams (later, not tested against a real tenant)

1. Create an **Azure Bot** (Single Tenant, new Entra app). Note the App ID and Tenant ID,
   and create a client secret. Put the three values in `.env` instead of the dummy ones
   in step 4, and drop `ANONYMOUS_ALLOWED`.
2. Tunnel port 3978 (`ngrok http 3978` or a dev tunnel with anonymous access) and set the
   bot's **Messaging endpoint** to `https://<tunnel>/api/messages`. Add the **Microsoft
   Teams** channel.
3. For a group chat, build the app package with `APP_ID=<app id> apps/teams/appPackage/build.sh`
   and upload the zip in Teams (**Apps → Manage your apps → Upload a custom app**). Your
   tenant may block custom app uploads.
