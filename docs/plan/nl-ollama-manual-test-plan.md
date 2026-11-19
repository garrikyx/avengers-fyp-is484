# NL query manual test plan: Ollama, Teams and Copilot (MCP)

Working notes, not a spec. These checks cover the NL query path end to end on a
developer machine: the local Ollama fallback, conversational replies, the Teams bot and
the MCP server for Copilot. Requirements: spec 008 (`FR-NLQ-006`, `007`, `009`, `019`,
`021`, `022`, `026`, `030`) and spec 007 §6.1.

Automated coverage already exists
(`uv run pytest tests/unit/backend/nl tests/unit/teams tests/unit/mcp`). This plan
checks what the unit tests can't: a real model, real latency, the Playground UI and an
MCP client.

The expected timings come from a run on 2026-10-28 (Apple Silicon laptop, `llama3.2`,
Ollama 0.40). Slower machines will be slower on LLM rows only.

## 0. Setup

Do this once. See [Prerequisites](../../README.md#prerequisites).

| ID  | Step                                                           | Expected                                                                         |
| --- | -------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| S-1 | `uv sync --all-packages`                                       | Completes; `telemetry-mcp` is installed                                          |
| S-2 | `make ollama-setup`                                            | `llama3.2` pulled (about 2 GB the first time)                                    |
| S-3 | Start Ollama (app or `ollama serve`), then `make ollama-check` | `Ollama OK: llama3.2 at http://127.0.0.1:11434`                                  |
| S-4 | `make ollama-check OLLAMA_MODEL=nope`                          | `Model nope is not pulled. Run: make ollama-setup`, exit 1                       |
| S-5 | Quit Ollama, run `make ollama-check`, then start Ollama again  | `Ollama is not running at ... Start the Ollama app or run: ollama serve`, exit 1 |

Define this helper in the terminal you use for section B. It prints the reply, then the
HTTP status and the time taken:

```sh
ask() {
  curl -s -w '\n%{http_code} %{time_total}s\n' http://127.0.0.1:8080/telemetry/nl/query \
    -H 'Content-Type: application/json' -d "{\"question\": \"$1\"}"
}
```

## A. Backend startup

Start the stack: `make backend-run`, `make simulator-run` and `make agent-run` in three
terminals. Wait about 30 seconds for data.

| ID  | Step                                                                                                                          | Expected                                                                                                       | Req           |
| --- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------- |
| A-1 | Watch the `make backend-run` output                                                                                           | `ollama-check` passes, the backend starts, then `ollama model llama3.2 is loaded` appears within a few seconds | `FR-NLQ-021`  |
| A-2 | `curl -s http://127.0.0.1:8080/telemetry/nl/intents`                                                                          | 200 with the intent catalogue                                                                                  | spec 007 §6.2 |
| A-3 | Startup time with Ollama stopped (repeat A-1 with Ollama quit, using `uv run telemetry-backend --config config/backend.yaml`) | Backend starts normally. One warning: `ollama warm-up failed (ConnectError)`                                   | `FR-NLQ-021`  |

## B. Direct API

Run each question with `ask "<question>"`.

| ID   | Question                                                           | Expected `kind` / `reason` or `source`                                                                                                          | Expected time | Req                        |
| ---- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | -------------------------- |
| B-1  | `hi`                                                               | `clarification` / `greeting`; message "Hi! I can answer questions about Magic's telemetry..."; 6 `suggestedQuestions`                           | under 50 ms   | `FR-NLQ-030`               |
| B-2  | `what can you do?`                                                 | `clarification` / `help` and suggestions                                                                                                        | under 50 ms   | `FR-NLQ-030`               |
| B-3  | `thanks!`                                                          | `clarification` / `greeting` ("You're welcome...")                                                                                              | under 50 ms   | `FR-NLQ-030`               |
| B-4  | `Why are orders rejecting in the last 30 minutes?`                 | `answer`, `source: rule`, `intent: rejection_summary`                                                                                           | under 100 ms  | `FR-NLQ-006`               |
| B-5  | `Is anything firing on Magic that I should worry about right now?` | `answer`, `source: llm`, `intent: alert_status`                                                                                                 | 1 to 5 s      | `FR-NLQ-007`               |
| B-6  | `give me a rejection summary`                                      | `answer`, `source: llm`, `intent: rejection_summary`                                                                                            | 1 to 5 s      | `FR-NLQ-007`               |
| B-7  | `what's the weather like in Singapore?`                            | `clarification` / `out_of_scope`. The message steers back to Magic and contains no digits. It never offers to help with the weather             | 1 to 5 s      | `FR-NLQ-030`               |
| B-8  | `tell me a joke`                                                   | Same as B-7. Either the model's own sentence or the template "I can only answer questions about Magic's telemetry. Try one of these questions." | 1 to 5 s      | `FR-NLQ-030`               |
| B-9  | `hi, why are orders rejecting?`                                    | `answer` (not small talk): a greeting with a real question goes through the matcher                                                             | under 5 s     | `FR-NLQ-030`               |
| B-10 | Every answer in B-4 to B-6                                         | Includes `interpretedQuery` and `data`; every number in `answer` appears in `data`                                                              |               | `FR-NLQ-009`, `FR-NLQ-020` |
| B-11 | Any 10 questions from B-1 to B-9                                   | No reply takes longer than about 7 s (6 s LLM budget plus the query)                                                                            |               | `FR-NLQ-021`               |
| B-12 | `What's rejecting on GOOGL?` (after `demo.sh burst`)               | `answer`, `intent: symbol_drilldown`; a non-zero reject count and real reason codes such as `OrderExceedsLimit`, not "unspecified"              | under 100 ms  | `FR-QRY-034`               |
| B-13 | `Are rejects worse than yesterday?`                                | `answer`, `intent: compare_period`; `caveats` says the period is outside the retention window and compares the last 30m with the 30m before it  | under 100 ms  | `FR-NLQ-013`               |

## C. Ollama slow or down

| ID  | Step                                                                                    | Expected                                                                                                                                                                                 | Expected time | Req          |
| --- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ------------ |
| C-1 | Quit Ollama (menu bar > Quit Ollama, or stop `ollama serve`). Leave the backend running |                                                                                                                                                                                          |               |              |
| C-2 | `ask "hi"`                                                                              | Same as B-1                                                                                                                                                                              | under 50 ms   | `FR-NLQ-030` |
| C-3 | `ask "is it slow"`                                                                      | `answer`, `source: rule`, `intent: latency_summary`. `caveats` includes "Interpreted by keyword matching because the language model was unavailable..."                                  | under 100 ms  | `FR-NLQ-021` |
| C-4 | `ask "give me a rejection summary"`                                                     | `answer`, `source: rule`, with the same caveat                                                                                                                                           | under 100 ms  | `FR-NLQ-021` |
| C-5 | `ask "what's the weather"`                                                              | `clarification` / `llm_unavailable`: "I'm having trouble understanding that right now..." plus suggestions                                                                               | under 100 ms  | `FR-NLQ-021` |
| C-6 | Backend log                                                                             | `ollama is unavailable: ConnectError` warnings. No stack traces and no 5xx responses                                                                                                     |               |              |
| C-7 | Start Ollama again and run `ask "give me a rejection summary"`                          | `source: llm` again with no backend restart. The first call may take a few seconds while the model loads; if it takes more than 6 s you get the C-4 fallback. Run it again and it's fast |               | `FR-NLQ-021` |
| C-8 | Cold model: run `ollama stop llama3.2`, then B-5                                        | Reply within about 7 s: an LLM answer if the model loads in time, otherwise a keyword fallback or `llm_unavailable`. Never a timeout                                                     |               | `FR-NLQ-021` |

## D. Teams (Agents Playground)

Add `make teams-run` and `make playground`, then open <http://localhost:56150> and wait
for "Connected" in the log panel.

| ID  | Step                                                                              | Expected                                                                                                        | Req          |
| --- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------ |
| D-1 | Send `hi`                                                                         | A card with the greeting and six suggested-question buttons. No "supported intents" line                        | `FR-NLQ-030` |
| D-2 | Tap **Is Magic slow right now?**                                                  | The question appears as your message, and an answer card follows                                                | `FR-NLQ-030` |
| D-3 | Send `Why are orders rejecting in the last 30 minutes?`                           | Answer card: headline, breakdown, caveats and **Show query**                                                    | `FR-NLQ-015` |
| D-4 | Tap **Show query** on an LLM answer (B-5 wording)                                 | Shows `source: llm` and the interpreted query                                                                   | `FR-NLQ-017` |
| D-5 | Send `what's the weather like`                                                    | A reply card that steers back to Magic, with the buttons                                                        | `FR-NLQ-030` |
| D-6 | Send `<b>bold</b> **stars** [link](http://x) what's up`                           | The card shows no rendered HTML, bold or link. The reply is the plain template or a plain sentence              | `FR-NLQ-022` |
| D-7 | Quit Ollama, send `is it slow`                                                    | Answer card with the keyword-matching caveat, in under a second. No "took too long" error card                  | `FR-NLQ-021` |
| D-8 | Stop the backend, send `hi`                                                       | The bot's error card ("I couldn't reach the telemetry service..."), not a crash. Restart the backend afterwards |              |
| D-9 | Optional: open the app's command menu (needs the manifest in a real Teams tenant) | Lists the six example questions and `help`                                                                      |              |

## E. MCP server (MCP Inspector)

Add `make mcp-run` (listens on `http://127.0.0.1:8765/mcp`), then `make mcp-inspector`.
In the Inspector, choose **Streamable HTTP**, enter the URL and connect.

| ID  | Step                                                   | Expected                                                                                                                                          | Req          |
| --- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| E-1 | **Tools** > **List tools**                             | Exactly `nl_query`, `query_metrics`, `list_alerts`, `get_alert`, `list_agent_health`, `list_events`. Each is marked read-only and not destructive | `FR-NLQ-026` |
| E-2 | `nl_query` with `question: "Is Magic slow right now?"` | `kind: answer` with `answer`, `interpretedQuery`, `effectiveTimeRange`, `dataCompleteness` and `citations`. No raw `data.groups`                  | `FR-NLQ-026` |
| E-3 | `nl_query` with `question: "hi"`                       | `kind: reply`, `reason: greeting` and `suggestedQuestions`                                                                                        | `FR-NLQ-030` |
| E-4 | `list_alerts` with defaults                            | The same items as `curl -s http://127.0.0.1:8080/telemetry/alerts`                                                                                | `FR-NLQ-026` |
| E-5 | `list_agent_health`                                    | The same as `curl -s http://127.0.0.1:8080/telemetry/health/agents`                                                                               | `FR-NLQ-026` |
| E-6 | `get_alert` with `alert_id: "../health/agents"`        | `error: not_found`. It must not return the agent health list                                                                                      | `FR-NLQ-023` |
| E-7 | `list_events` with `limit: 1000`                       | Rejected by the Inspector or the server (limit is 1 to 500)                                                                                       |              |
| E-8 | Stop the backend and call `nl_query`                   | `error: unavailable` and a short message. The server stays up                                                                                     |              |
| E-9 | Quit Ollama and call `nl_query` with `"is it slow"`    | Same as C-3, reached through MCP                                                                                                                  | `FR-NLQ-021` |

## F. Copilot Studio (optional)

Needs a Microsoft 365 tenant with Copilot Studio. Steps, agent instructions and tenant
prerequisites are in the [integration pack](m365-copilot-integration-pack.md). Use
synthetic simulator data only. Without a tenant, run section I instead.

| ID  | Step                                                       | Expected                                                               |
| --- | ---------------------------------------------------------- | ---------------------------------------------------------------------- |
| F-1 | Expose `:8765` with a dev tunnel and add it as an MCP tool | Copilot Studio lists the six tools                                     |
| F-2 | Ask the agent "Is anything firing on Magic?"               | It calls `nl_query` and quotes the answer without changing the numbers |
| F-3 | Ask "hi"                                                   | It relays the greeting and offers the suggested questions              |
| F-4 | Stop the tunnel afterwards                                 | The tunnel URL no longer responds                                      |

## G. Safety

| ID  | Step                                                                     | Expected                                                             | Req                        |
| --- | ------------------------------------------------------------------------ | -------------------------------------------------------------------- | -------------------------- |
| G-1 | After sections B to E, run `grep -i "weather\|joke\|bold" <backend log>` | No matches: raw question text is never logged                        | `FR-NLQ-019`               |
| G-2 | Inspect any `nl_query` and MCP output                                    | No FIX tag/value strings and no raw log lines                        | CLAUDE.md safety rules     |
| G-3 | Look through the off-topic replies from B-7, B-8 and D-5                 | None contain a digit, link or markup character, or a telemetry claim | `FR-NLQ-009`, `FR-NLQ-030` |

## H. Regression

| ID  | Step                                                                     | Expected                                    |
| --- | ------------------------------------------------------------------------ | ------------------------------------------- |
| H-1 | `make nl-eval`                                                           | All evaluation fixtures pass (`FR-NLQ-025`) |
| H-2 | `uv run pytest tests/unit/backend/nl tests/unit/teams tests/unit/mcp -q` | All pass                                    |

## I. No tenant: public URL and demo

Copilot Studio runs in Microsoft's cloud and connects to a public HTTPS URL, not
`localhost`. These checks test that path with the MCP Inspector, so the only untested
step is adding the URL in Copilot Studio. Keep the section E setup running.

One-time setup: `brew install --cask devtunnel`, then `devtunnel user login`. A personal
Microsoft or GitHub account works.

| ID  | Step                                                                                               | Expected                                                     | Req          |
| --- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------ |
| I-1 | `devtunnel host -p 8765 --allow-anonymous`                                                         | Prints an `https://...` URL for port 8765                    |              |
| I-2 | In the Inspector, connect with **Streamable HTTP** to the I-1 URL plus `/mcp`, then **List tools** | Same six read-only tools as E-1                              | `FR-NLQ-026` |
| I-3 | `nl_query` with `question: "Is Magic slow right now?"`                                             | Same shape as E-2, in under about 7 s                        | `FR-NLQ-021` |
| I-4 | `nl_query` with `question: "hi"`                                                                   | Same as E-3                                                  | `FR-NLQ-030` |
| I-5 | `curl -s -o /dev/null -w '%{http_code}\n' <I-1 URL>/telemetry/alerts`                              | Not 200: only the MCP server is exposed, not the backend API |              |
| I-6 | Stop the tunnel, then repeat I-5                                                                   | The URL no longer responds                                   |              |
| I-7 | Run G-1 and G-2 again                                                                              | Still no matches and no raw log content                      | `FR-NLQ-019` |

Anyone with the URL can call the tools while the tunnel runs. Synthetic data only.

### Demo script without a tenant

Run the stack, the Teams bot and the MCP server beforehand. Record the run as a backup.

| Beat | Show                                                                              | Say                                                                                                                                                      |
| ---- | --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Agents Playground: `hi`, then tap **Why are orders rejecting?**                   | "A support user asks in plain language, in a Teams-style chat built on Microsoft's Agents SDK."                                                          |
| 2    | **Show query** on the answer                                                      | "Every number comes from a validated query. The model never writes the numbers."                                                                         |
| 3    | Inspector over the tunnel: the six tools, then `nl_query`                         | "This is the MCP server Microsoft 365 Copilot connects to, reached over the same kind of public HTTPS URL Copilot Studio uses. Every tool is read-only." |
| 4    | The diagram and steps in the [integration pack](m365-copilot-integration-pack.md) | "In UBS's tenant, an admin adds this URL as an MCP tool on a Copilot agent and publishes it. Production adds Entra ID sign-in and internal hosting."     |
| 5    | Limits                                                                            | "We haven't run it inside a Microsoft 365 tenant, and the POC has no per-user sign-in."                                                                  |

Don't show mock Microsoft 365 Copilot screens.

## Results log

Copy this table into the PR or the Jira story.

| Section               | Tester | Date | Machine and model | Pass/fail | Notes |
| --------------------- | ------ | ---- | ----------------- | --------- | ----- |
| 0 Setup               |        |      |                   |           |       |
| A Backend startup     |        |      |                   |           |       |
| B Direct API          |        |      |                   |           |       |
| C Ollama slow or down |        |      |                   |           |       |
| D Teams               |        |      |                   |           |       |
| E MCP                 |        |      |                   |           |       |
| F Copilot Studio      |        |      |                   |           |       |
| G Safety              |        |      |                   |           |       |
| H Regression          |        |      |                   |           |       |
| I No tenant           |        |      |                   |           |       |

## Known behaviour (not failures)

- `thanks` returns `reason: greeting`. There is no separate `thanks` reason.
- LLM wording for off-topic replies varies between runs. Any sentence that steers back
  to Magic and passes G-3 is a pass.
- Answers show "No order activity" if the simulator or agent isn't running, or started
  less than a window ago.
- Questions about other periods outside the 6-hour window, such as "Why were orders
  rejecting yesterday?", get a clarification that earlier data is not retained.
- A symbol with no rejects in the window answers 0. Run `demo.sh burst` first for B-12.
