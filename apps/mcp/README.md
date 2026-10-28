# Telemetry MCP server

Lets Microsoft 365 Copilot (or any MCP client) ask telemetry questions. It is a thin,
read-only adapter: each tool makes one call to the backend HTTP API and never touches
Redis, a store or log files. Design: spec 008 §6,
[ADR 0007](../../docs/adr/0007-mcp-server-for-copilot.md).

| Tool | Backend call |
| --- | --- |
| `nl_query(question, timezone?, audience?)` | `POST /telemetry/nl/query` |
| `query_metrics(request)` | `POST /telemetry/query/metrics` |
| `list_alerts(status?, application?, instance_id?, limit?)` | `GET /telemetry/alerts` |
| `get_alert(alert_id)` | `GET /telemetry/alerts/{id}` |
| `list_agent_health()` | `GET /telemetry/health/agents` |
| `list_events(application?, instance_id?, event_type?, severity?, since?, limit?)` | `GET /telemetry/events` |

All tools are marked read-only. `nl_query` returns the backend's templated answer with
the interpreted query, time range, data completeness and citations, but not the raw
group breakdown. For greetings, help and off-topic questions it returns a short reply
and `suggestedQuestions` (FR-NLQ-030). Backend failures come back as
`{"error": "disabled" | "bad_request" | "not_found" | "timeout" | "unavailable"}`.

The server sends no backend credentials (POC decision, spec 009 §3.3). Entra ID auth is
production work.

## Run it locally

Start the backend first (see [the Teams README](../teams/README.md#run-it-locally-5-terminals-all-from-the-repo-root)),
then from the repo root:

```sh
make mcp-run          # or: uv run telemetry-mcp
```

The server listens on `http://127.0.0.1:8765/mcp` (streamable HTTP).

Try it with the MCP Inspector:

```sh
npx @modelcontextprotocol/inspector
```

Choose **Streamable HTTP**, enter `http://127.0.0.1:8765/mcp`, connect, then call
`nl_query` with `"Is Magic slow right now?"`.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `TELEMETRY_BACKEND_URL` | `http://127.0.0.1:8080` | Backend public API |
| `MCP_BACKEND_TIMEOUT_SECONDS` | `12` | Keep above `nl.llm.timeout` (6s) so the backend's fallback reply arrives first |
| `MCP_DEFAULT_APPLICATION` | `Magic` | Sent as `context.defaultApplication` |
| `MCP_DEFAULT_TIMEZONE` | `Asia/Singapore` | Used when the caller gives no timezone |
| `MCP_BIND_HOST` | `127.0.0.1` | Bind address |
| `MCP_PORT` | `8765` | Port |

## Connect Copilot

1. Expose the server with a dev tunnel:

   ```sh
   devtunnel host -p 8765 --allow-anonymous
   ```

2. In Copilot Studio, open your agent, go to **Tools** > **Add a tool** > **Model
   Context Protocol**, and enter the tunnel URL with the `/mcp` path.
3. Ask the agent "Is anything firing on Magic?" It should call `nl_query` and quote the
   answer.

Anonymous tunnels are for the POC only. Don't expose a backend that holds UBS data this
way.
