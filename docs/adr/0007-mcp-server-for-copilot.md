# ADR 0007 — Expose telemetry to Microsoft 365 Copilot through an MCP server

Status: Proposed · Date: 2026-10-16 · Deciders: TBD

## Context

Spec 008 §6 connects Copilot through a declarative agent and an API plugin pointed at the
backend's OpenAPI document. The sponsor's requirements document asks only that the backend
"exposes query APIs" and "integrates with Copilot or Microsoft Teams". It does not name a
mechanism.

On the 2026-10-16 call the sponsor described the target explicitly:

- an **MCP server** runs the telemetry access;
- "Microsoft 365 Copilot agent connect to this MCP server";
- developers, support and business users then query it and are alerted through it.

Options considered:

1. Keep the API plugin only.
2. Replace the API plugin with MCP.
3. Add an MCP server beside the API plugin and the Teams bot.

## Decision

Add an **MCP server** as a third integration surface (option 3). It is a **thin, read-only
adapter over the existing backend HTTP APIs**: `POST /telemetry/nl/query`, the metrics
query, the alert list and detail, agent health, and events (spec 008 `FR-NLQ-026`).

- The Teams bot (UBS-100) is unchanged.
- The OpenAPI document stays, because the MCP tools are generated from the same contracts.

## Rationale

- **It is what the sponsor asked for.** Copilot agents can consume MCP servers, so MCP is the
  connection point they described.
- **No new data path.** The MCP server calls the same APIs as every other surface, so the
  architecture rule that the Teams/Copilot integration talks only to the backend APIs, never
  to Redis or the stores, still holds. Anti-fabrication (spec 008 §3), `dataCompleteness` and
  query clamping are inherited rather than re-implemented.
- **Small.** A read-only tool per existing endpoint. No intent logic lives in the MCP server;
  `nl_query` delegates to the NL layer.

## Consequences

- One more process to deploy and authenticate. It MUST use the same Entra ID auth, read-only
  scope, rate limits and audit logging as the other surfaces (`FR-NLQ-018`/`019`/`021`).
  This is the production target. The team settled the local synthetic-data POC exception
  on 2026-10-16 (spec 009 §3.3): custom backend auth is deferred; Microsoft platform
  credentials/message validation remain required. Production identity/tenant details
  remain open ([Q-3](../plan/open-questions.md)).
- Tool descriptions are prompt surface. They MUST be static and never include data from
  telemetry or logs (`FR-NLQ-024`).
- If Copilot's MCP support does not fit the UBS tenant, the API plugin in spec 008 §6 remains
  a working fallback at no extra cost.
