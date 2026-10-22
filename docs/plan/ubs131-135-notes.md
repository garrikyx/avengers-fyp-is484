# UBS-131 / UBS-135 — MCP server and NL query access: status and next steps

Status: 2026-10-22 · Branches `UBS-135-Secure-NL-Query-API` → `UBS-131-MCP-Server`
(stacked; merge UBS-135 first) · Specs: spec 008 §6–7, spec 009 §3.3 ·
[ADR 0007](../adr/0007-mcp-server-for-copilot.md)

## What is built

| Ticket  | Piece                                       | Where                                                         | Requirement                |
| ------- | ------------------------------------------- | ------------------------------------------------------------- | -------------------------- |
| UBS-135 | `read_access` checkpoint on every read route | `apps/backend/src/telemetry_backend/api/access.py`            | FR-NLQ-018                 |
| UBS-135 | Question rate limit, default 20/min, 429 + `Retry-After` | `services/question_limiter.py`, `nl_query` in `main.py` | FR-NLQ-021                 |
| UBS-135 | One audit line per NL / metrics query (no question text) | `_audit_query` in `main.py`, logger `telemetry_backend.audit` | FR-NLQ-019, NFR-SEC-011 |
| UBS-135 | Copilot API plugin fallback (read operations only) | `deployment/copilot/`                                   | spec 008 §6                |
| UBS-131 | MCP server, six read-only tools             | `apps/mcp/src/telemetry_mcp/server.py` (`telemetry-mcp`)      | FR-NLQ-026, FR-NLQ-024     |
| UBS-131 | VS Code MCP registration                    | `.vscode/mcp.json`                                            | —                          |

MCP tools: `nl_query`, `query_metrics`, `list_alerts`, `get_alert`,
`list_agent_health`, `list_events`. Each is one backend HTTP call returning the API's
JSON unchanged. The server imports nothing from `telemetry_backend` or `redis`
(enforced by `tests/unit/mcp/test_UBS_131_mcp_server.py`).

## Verified

- Unit tests: `tests/unit/backend/api/test_UBS_135_read_access.py`,
  `tests/unit/mcp/test_UBS_131_mcp_server.py` (MCP tools run against the real backend
  in-process).
- Live, against a local backend: a scripted stdio MCP client, MCP Inspector, and
  **GitHub Copilot agent mode in VS Code** (lists the six tools and answers questions;
  the backend writes the audit line).
- Copilot Studio's "Add MCP server" wizard reached the server through an ngrok tunnel
  and listed all six tools.

## Limitations

**The MCP server is proven with a local Copilot agent (VS Code), not with Microsoft
365 Copilot or Copilot Studio / Power Platform.** It is not ready to connect to Power
Platform as is:

1. **Licence.** Creating the Copilot Studio agent failed with "You don't have
   permission to create agents · User license not found" on the SMU tenant. No
   end-to-end test in Copilot Studio, Microsoft 365 Copilot or Teams has run.
2. **No authentication.** The MCP endpoint and backend accept anonymous calls (POC
   exception, spec 009 §3.3). Fine on localhost; a public tunnel exposes them to anyone
   with the URL. Use simulator data only.
3. **No hosted endpoint.** Remote access is an ngrok tunnel from a laptop. The free
   hostname changes on restart, and `--allowed-host` must match it (the SDK's
   DNS-rebinding check otherwise returns 421).
4. **Shared rate-limit bucket.** Without user identity the limit is keyed by request
   source, so every MCP user shares one 20/min bucket.
5. **No identity forwarding.** The MCP server does not forward `Authorization` or
   `X-Request-Id` (marked `shortcut:` in `server.py`).
6. **`dataCompleteness` only on two tools.** `nl_query` and `query_metrics` return it;
   the alert, health and events APIs have no such field (spec 007).
7. **No declarative-agent MCP manifests.** Only the API-plugin fallback manifests exist
   (`deployment/copilot/`); neither has been provisioned in a tenant.
8. **`nl_query` answers use the stub renderer** until UBS-99 lands; no MCP change is
   needed then.

## Run it locally (VS Code Copilot)

1. Create `config/backend.yaml` (local only, do not commit):

   ```yaml
   nl:
     enabled: true
     llm:
       provider: mock
   ```

2. Start the stack, one terminal each:

   ```bash
   uv run telemetry-backend --config config/backend.yaml
   uv run python apps/simulator/src/simulator/mock_logger.py
   uv run telemetry-agent --config config/agent.yaml
   ```

3. Open the repo in VS Code, start `magic-telemetry` from `.vscode/mcp.json`, switch
   Copilot Chat to **Agent** mode and ask "Is telemetry actually working?".

Alternative client: `npx @modelcontextprotocol/inspector uv run telemetry-mcp`.

## Continuing the implementation

In order; each step assumes the previous one.

1. **Get a tenant.** Ask UBS or SMU IT for a Copilot Studio licence with Environment
   Maker on a Power Platform environment, or a Microsoft 365 tenant with Copilot and
   custom app upload. Same blocker as the Teams bot (UBS-100).
2. **Re-run the Copilot Studio path** (Tools → Add a tool → Model Context Protocol):
   - `uv run telemetry-mcp --transport streamable-http --port 8090 --allowed-host <tunnel-host>`
   - `ngrok http --url=<static-domain> 8090` (claim the free static domain so the URL
     survives restarts)
   - Server URL `https://<tunnel-host>/mcp`, authentication None (POC only)
   - Paste the agent instructions from `deployment/copilot/declarativeAgent.json`,
     test in the Test pane, then publish to **Teams and Microsoft 365 Copilot**.
   Guide: <https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent>
3. **Or the declarative-agent path** (Microsoft 365 Agents Toolkit ≥ 6.12, VS Code):
   Create a New Agent/App → Declarative Agent → Add an Action → Start with an MCP
   Server. Commit the generated manifests under `deployment/copilot-mcp/`.
   Guide: <https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/build-mcp-plugins>
4. **Host it.** Deploy the backend and `telemetry-mcp` behind HTTPS (`deployment/azure/`
   is empty), replacing the tunnel. Pass the public hostname with `--allowed-host`.
5. **Production auth (Q-3), when the tenant is known:**
   - validate Entra bearer tokens (scope `Telemetry.Read`) in `read_access`; nothing
     else in the backend changes;
   - forward the caller's `Authorization` and `X-Request-Id` from `_call` in
     `server.py`;
   - switch the MCP tool / plugin auth from None to OAuth 2.0 (Copilot Studio) or SSO
     (Agents Toolkit);
   - the rate limit then becomes per user automatically (`rate_limit_key`).
6. **Decide `dataCompleteness` for alerts, health and events** (spec 007 change) if the
   sponsor wants it on every tool.

## Open points for the team

- ADR 0007 is still `Proposed`; this work implements it.
- `apps/teams/pyproject.toml` builds `src/teams` but the package is `src/teams_agent`
  (UBS-100).
