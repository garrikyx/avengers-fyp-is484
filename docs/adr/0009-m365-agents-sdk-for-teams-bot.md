# ADR 0009 — Build the Teams bot on the Microsoft 365 Agents SDK

Status: Accepted · Date: 2026-10-21 · Deciders: UBS-100 implementer

## Context

The Teams bot (UBS-100) must receive Teams messages, validate Microsoft's incoming
tokens, and reply with Adaptive Cards. Three options were considered:

1. Microsoft 365 Agents SDK for Python (`microsoft-agents-*`).
2. `botbuilder-python`, the long-standing Bot Framework SDK.
3. A hand-rolled `/api/messages` endpoint.

## Decision

Use the Microsoft 365 Agents SDK, hosted on aiohttp with MSAL authentication.

- `botbuilder-python` was archived on 2026-01-05 and Bot Framework support tickets
  ended on 2025-12-31. Microsoft directs new work to the Agents SDK.
- Hand-rolling means implementing Bot Connector JWT validation and token acquisition
  ourselves. That is security-sensitive and easy to get wrong; the SDK already does it.
- The packages declare Python 3.14 support, which the project requires.

## Consequences

- Four lockstep-versioned packages (`microsoft-agents-hosting-core`, `-hosting-aiohttp`,
  `-activity`, `-authentication-msal`) plus aiohttp, which is heavier than a plain
  `httpx` client. This is acceptable because the bot is not the Telemetry Agent and has
  no CPU or memory budget (CLAUDE.md applies that budget only to the agent).
- The SDK is young; its API may move between minor versions. Pin and upgrade the four
  packages together.
- Message handling sits behind a single function (`build_reply`) that takes an activity
  and returns a reply, so the SDK is confined to the entrypoint and a thin handler.
