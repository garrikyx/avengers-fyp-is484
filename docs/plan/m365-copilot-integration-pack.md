# Microsoft 365 Copilot integration pack

Working notes, not a spec. How to connect the telemetry MCP server (`apps/mcp`) to a
Microsoft 365 Copilot agent, for whoever has access to a Microsoft 365 tenant: the
sponsor, or the team once a tenant is available. Requirements: spec 008 §6
(`FR-NLQ-018`, `019`, `021`, `024`, `026`), spec 009 §3.3, spec 010 §2 `auth`, and
[ADR 0007](../adr/0007-mcp-server-for-copilot.md).

## Status

| Part                                                                   | Status                                                                                                   |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| MCP server: six read-only tools over the backend API                   | Built. Unit tests pass; manual checks in the [test plan](nl-ollama-manual-test-plan.md) sections E and I |
| Reaching the server over a public HTTPS URL (what Copilot Studio uses) | Testable without a tenant: test plan section I                                                           |
| Copilot Studio agent with the MCP tool                                 | **Not run.** The team has no tenant with Copilot Studio access                                           |
| Agent published to Microsoft 365 Copilot                               | **Not run**                                                                                              |
| Per-user Entra ID sign-in on the MCP server and backend                | **Not built.** Deferred for the POC (spec 009 §3.3, Q-3)                                                 |

ADR 0007 is Accepted: the sponsor confirmed the MCP route to Microsoft 365 Copilot.

Microsoft's Copilot Studio screens and licensing change often. Check the steps below
against the current Microsoft documentation before a session.

## How it connects

```text
User in Microsoft 365 Copilot (Teams, Outlook or the Copilot app)
      │
      ▼
"Magic Telemetry Assistant" agent (Copilot Studio, in the tenant)
      │  MCP, streamable HTTP over HTTPS
      ▼
telemetry-mcp (apps/mcp)  ── one HTTP call per tool ──►  telemetry backend
                                                            ▲
                                    agents on Magic hosts ──┘ (derived telemetry only)
```

The agent picks a tool and relays its result. The backend does the interpretation and
writes the answer from a template (`FR-NLQ-009`), so Copilot quotes numbers rather than
producing them. The MCP server holds no data and never reads Redis, stores or logs
(`FR-NLQ-026`).

## Tenant prerequisites

Ask the tenant's Microsoft 365 or Power Platform admin to confirm each item.

1. A non-production tenant or test accounts. Synthetic simulator data only, never UBS
   production data.
2. Copilot Studio maker rights for the person building the agent (trial or licence).
3. For the agent to appear in Microsoft 365 Copilot chat: Microsoft 365 Copilot
   licences, or Copilot Chat agent billing, for the demo users. The Copilot Studio test
   pane works without this.
4. A Power Platform data policy that allows custom connectors. Copilot Studio creates a
   custom connector for each MCP tool, and many tenants block them by default.
5. Permission to publish the agent to the "Teams and Microsoft 365 Copilot" channel, or
   an admin to approve it.
6. Network access from Microsoft's cloud to the MCP server: a dev tunnel for a demo, the
   tenant owner's gateway in production.

## Demo setup (synthetic data)

On the team's machine, start the backend, simulator and agent as in the
[Teams README](../../apps/teams/README.md#run-it-locally-5-terminals-all-from-the-repo-root),
then:

```sh
make mcp-run
devtunnel host -p 8765 --allow-anonymous
```

Note the `https://...` URL. The MCP endpoint is that URL plus `/mcp`. Anyone with the
URL can call the tools while the tunnel runs, so use it for synthetic data only and stop
it afterwards.

In Copilot Studio:

1. Create an agent named **Magic Telemetry Assistant**. Paste the description and
   instructions below.
2. Turn on generative orchestration. MCP tools need it.
3. **Tools** > **Add a tool** > **New tool** > **Model Context Protocol**. Enter:
   - Server name: `magic-telemetry`
   - Server description: `Read-only telemetry for the Magic trading application.`
   - Server URL: the tunnel URL plus `/mcp`
   - Authentication: None (POC only; see Production)
4. Check that the tool lists `nl_query`, `query_metrics`, `list_alerts`, `get_alert`,
   `list_agent_health` and `list_events`.
5. Add the starter prompts below.
6. Test in the test pane (checks in Verification).
7. Optional: publish to the **Teams and Microsoft 365 Copilot** channel and open the
   agent from Microsoft 365 Copilot.

### Agent description

> Answers read-only questions about the Magic trading application's telemetry: order
> flow, rejected orders, latency, FIX sessions, alerts and telemetry agent health.

### Agent instructions

Static text only: never paste telemetry values, hostnames or log content into the
instructions (`FR-NLQ-024`).

> You answer questions about the Magic trading application's telemetry.
>
> - For any question in plain language, call `nl_query` with the user's question.
> - Quote the `answer` exactly as returned. Do not recompute, round, combine or invent
>   numbers. Include any `caveats`.
> - If the result has `kind: reply`, show its `message` and offer its
>   `suggestedQuestions`.
> - If the result has an `error`, tell the user the telemetry service could not answer
>   and show its `message`. Do not guess an answer.
> - Use `list_alerts`, `get_alert` or `list_agent_health` only when the user asks for
>   alert details or agent health directly.
> - You cannot change anything in Magic or the telemetry system. Decline requests to
>   act, restart, cancel or modify.
> - Decline questions that are not about Magic's telemetry.

### Starter prompts

From the intent catalogue (`apps/backend/src/telemetry_backend/nl/catalogue.py`):

| Title            | Prompt                         |
| ---------------- | ------------------------------ |
| Overall health   | How is Magic doing today?      |
| Rejections       | Why are orders rejecting?      |
| Latency          | Is Magic slow right now?       |
| Alerts           | Any alerts open for Magic?     |
| FIX sessions     | Are the FIX sessions up?       |
| Telemetry health | Is telemetry actually working? |

## Verification

Run in the Copilot Studio test pane, then in Microsoft 365 Copilot if published. These
are test plan checks F-1 to F-4.

| Ask                                              | Expected                                                      |
| ------------------------------------------------ | ------------------------------------------------------------- |
| Is anything firing on Magic?                     | Calls `nl_query`; quotes the answer without changing numbers  |
| Why are orders rejecting in the last 30 minutes? | Quotes the reject answer and caveats                          |
| hi                                               | Relays the greeting and offers the suggested questions        |
| What's the weather in Singapore?                 | Declines and steers back to Magic, with no numbers            |
| Restart the Magic agent                          | Declines: no tool can do this                                 |
| (Stop the backend) Any alerts open for Magic?    | Says the telemetry service is unavailable; no invented answer |

## Production

What the tenant owner does:

1. Host the backend and MCP server inside their network, and expose the MCP endpoint
   through their approved gateway over TLS 1.2 or higher (`NFR-SEC-007`). Set
   `TELEMETRY_BACKEND_URL` on the MCP server to the internal backend address.
2. Register an Entra ID app for the telemetry API with a `Telemetry.Read` scope. Spec
   010 §2 already has `auth.entra: { tenantId, audience, requiredScope }`.
3. In Copilot Studio, add the MCP tool with OAuth 2.0 against that app, instead of None.
4. Publish the agent to the groups that need it: support, developers, business users.

What the team still has to build before that works:

1. Token validation in the MCP server, passing the user's token (or an on-behalf-of
   token) to the backend (`FR-NLQ-018`, `FR-NLQ-026`).
2. Token and scope checks in the backend (`NFR-SEC-009`).
3. Audit logging of user identity with the interpreted query, and per-user rate limits
   (`FR-NLQ-019`, `FR-NLQ-021`).

If the tenant's policies don't allow MCP tools, spec 008 §6's declarative agent with an
API plugin over the backend's OpenAPI document is the fallback (ADR 0007).

## Security notes

- Every tool is read-only and annotated as such. There is no tool that changes Magic or
  telemetry.
- Answers contain derived telemetry only: no raw Magic log lines or FIX payloads leave
  the Magic host (ADR 0004).
- `nl_query` returns the templated answer without the raw group breakdown, so the agent
  has no numbers to recompute.
- Raw question text is never logged by the backend (`FR-NLQ-019`).
- The demo setup has no user authentication. Don't present it as production
  authentication or per-user isolation (spec 009 §3.3).

## Open items

- Tenant ownership and Entra app details (Q-3).
- Track the Copilot tenant run as a Jira story alongside UBS-142 (real Teams tenant).
