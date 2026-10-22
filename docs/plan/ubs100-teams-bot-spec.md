# UBS-100 — Teams bot with Adaptive Card answers (spec)

## Problem Statement

Support engineers and developers who watch the Magic trading application have to leave Microsoft Teams, the tool they already live in, to find out why orders are rejecting, whether the FIX sessions are up, or whether an alert is open. The backend can already answer these questions in natural language, but nothing connects it to Teams, so the answers are out of reach where the questions come up.

## Solution

A Teams bot. A user @mentions it in a 1:1 or group chat and asks a question in plain English. The bot sends the text to the telemetry backend's natural-language query API and replies with an Adaptive Card showing the headline answer, a breakdown of the numbers, an alert badge when alerts are open, any caveats about data quality, and a "show query" button that reveals exactly how the question was interpreted. If the backend cannot interpret the question, the card suggests what can be asked. If the backend is unreachable, the card says so plainly.

## User Stories

1. As a support engineer, I want to ask a telemetry question in a Teams chat, so that I get an answer without opening another tool.
2. As a support engineer, I want to @mention the bot in a group chat, so that my team sees the answer too.
3. As a developer, I want to message the bot in a 1:1 chat, so that I can try questions privately while developing.
4. As a support engineer, I want the bot to ignore its own @mention text when interpreting my question, so that "@Telemetry why are orders rejecting" is understood the same as "why are orders rejecting".
5. As a support engineer, I want to see a typing indicator while the bot works, so that I know my question was received.
6. As a support engineer, I want the headline number that answers my question at the top of the card, so that I can read the answer at a glance.
7. As a support engineer, I want a breakdown of the numbers by category, so that I can see what is driving the headline (for example reject reasons).
8. As a support engineer, I want long breakdowns capped at ten rows with a note that more exist, so that the card stays readable.
9. As a support engineer, I want a "not enough data" message instead of a zero when a rate cannot be computed, so that I am never misled into thinking there were no problems.
10. As a support engineer, I want an alert badge showing how many alerts are open, so that I notice active problems even when my question was about something else.
11. As a support engineer, I want a plain statement when some agents are not reporting, so that I know the numbers may be incomplete.
12. As a support engineer, I want to see the resolved time range in my own timezone (Singapore by default, UTC+8), so that I know exactly what period the numbers cover.
13. As a support engineer, I want caveats such as clamped time ranges shown on the card, so that adjustments the backend made are never hidden.
14. As a support engineer, I want a "show query" button, so that I can see exactly how my question was interpreted and replay it.
15. As a support engineer, I want the interpreted query hidden until I ask for it, so that the card stays uncluttered.
16. As a support engineer, I want relative times like "since 9am" resolved in my own timezone, so that the answer matches my working day.
17. As a support engineer, I want a sensible default timezone when Teams does not tell the bot mine, so that questions still work.
18. As a support engineer, I want a helpful list of supported question types when the backend cannot interpret my question, so that I know how to rephrase.
19. As a support engineer, I want a clear message when the backend is down or slow, so that I know to retry instead of wondering.
20. As a support engineer, I want a clear message when natural-language queries are disabled, so that I do not think the bot is broken.
21. As a support engineer, I want error messages that never expose stack traces or internals, so that failures stay safe and readable.
22. As a security reviewer, I want every piece of backend or user-derived text escaped before it goes into a card, so that crafted text cannot inject markup, links or mentions.
23. As a security reviewer, I want the bot to only ever call the backend's query API, so that Teams never reads Redis or any store directly.
24. As a security reviewer, I want the bot to expose no mutating action, so that the read-only guarantee holds.
25. As a security reviewer, I want the bot's own logs to exclude the raw question, so that pasted sensitive content is not stored.
26. As a security reviewer, I want incoming Teams messages validated by the platform's token check, so that only genuine Teams traffic reaches the bot.
27. As a security reviewer, I want Microsoft app credentials supplied through environment variables and never committed, so that secrets stay out of the repository.
28. As a developer, I want to run the bot locally against the local backend using Microsoft's Agents Playground, so that I can iterate without Azure setup.
29. As a developer, I want a README covering env vars, running locally, and connecting real Teams through a dev tunnel and Azure Bot registration, so that the team can reproduce the demo.
30. As a team lead, I want the real-Teams demo to work against the local backend with synthetic data, so that the POC acceptance criterion is met.
31. As a developer, I want the bot's package to build into a non-empty wheel, so that it can be installed and deployed.
32. As a developer, I want the bot configuration (backend URL, default application, default timezone, timeout) in environment variables, so that nothing is hardcoded.
33. As a support engineer, I want the application fixed to Magic from configuration, so that my wording can never redirect the query to another application's data.
34. As a support engineer, I want one backend call per message, so that responses are fast and predictable.
35. As a support engineer, I want empty or whitespace-only messages ignored, so that stray messages do not trigger errors.
36. As a developer, I want the alert badge to read structured data from the API, so that it keeps working when the answer wording changes.
37. As a future maintainer, I want the choice of Microsoft's current Agents SDK recorded, so that the reason the archived SDK was not used is clear.

## Implementation Decisions

- A new Teams bot component is the only holder of Microsoft app credentials and the only part that talks to Teams. It is a thin adapter: receive a message, call the backend, render a card. It contains no interpretation or numeric logic.
- It uses the Microsoft 365 Agents SDK (hosting on aiohttp, MSAL auth). The previously common Bot Framework SDK for Python is archived and not used. An ADR records this.
- The bot calls only the backend's natural-language query endpoint and parses its two response shapes (answer and clarification) using the shared Pydantic models, so there are no duplicate schemas. It treats unavailable-service, bad-request, timeout and connection failures as typed errors.
- Supported conversation types are 1:1 and group chat. The bot strips its own mention using the SDK's helper. Channels and threaded flows are not supported.
- The request carries a context with the configured application (always Magic, never taken from user text) and the user's timezone: the activity's local timezone if present, else the client-info entity, else the configured default (Asia/Singapore).
- Cards use Adaptive Card schema 1.4. The breakdown is built from column-set rows rather than the Table element, to avoid client-support risk. Breakdown rows are capped at ten, with a note when the backend marks results truncated.
- Card content, in order: headline answer, breakdown, alert badge (when alert citations are present), caveats and data-completeness statement with the resolved time range in the user's timezone (Singapore, UTC+8, by default), and a hidden pretty-printed interpreted query revealed by a toggle action.
- The bot never recomputes or rephrases numbers. It renders the backend's answer text and structured fields. Null indicators render as "not enough data", never zero.
- All backend- or user-derived strings are escaped for Markdown, HTML-like markup and mentions before being placed in card text. The interpreted query is shown in a monospace block, also escaped.
- Backend change (small, additive): when the intent is alert status, the response cites each active alert using the existing alert citation type, so the bot's badge is driven by structured data and not by parsing answer text.
- Failures produce a short plain card. Client timeout is ten seconds. Logs record the failure type only, never the raw question or any conversation content.
- Backend authentication, per-user rate limits and audit are not implemented here (POC decision; they belong to the follow-up security ticket). The bot's logs must not claim the backend authenticated the user.
- Docs created with this work: a project glossary (Teams bot, Integration Service, clarification, Adaptive Card), an ADR for the SDK choice, and a bot README.
- Packaging bug fixed: the bot's wheel must include the real package directory.

## Testing Decisions

- A good test drives external behavior only: a Teams activity goes in, and the reply activity's card content is asserted. Tests do not call the card builders or the escape helper directly.
- Seam 1 (new, highest available): the bot's message boundary, with the backend stubbed at the HTTP level. It covers answer card layout, breakdown cap and truncation note, null-indicator wording, alert badge, partial-completeness statement, show-query toggle, clarification card, each error card, @mention stripping, timezone selection and fallback, empty-message handling, and escaping of hostile strings in every rendered field.
- The same seam is run once against the real backend app with the mock LLM, to catch response-shape drift between bot and backend.
- Seam 2 (existing): the natural-language query service's tests, extended to assert alert citations on alert-status questions.
- Prior art: the existing backend natural-language service, rule matcher and LLM fallback tests, and the integration tests that run the real backend app in-process.
- No live Teams in CI. Real Teams connectivity is verified manually via the README steps.
- Quality gates: Ruff, strict mypy, pytest.

## Out of Scope

- Entra ID per-user authentication, per-user rate limits, audit logging and the Copilot API-plugin fallback (follow-up security ticket).
- The Copilot MCP server.
- Proactive alert notifications posted into Teams.
- The alert delivery-status detail view.
- The executive answer style and the end-of-day summary.
- Channels, threads, message-reply flows, proactive messaging, and mutating actions.
- A Docker Compose service for the bot.
- Production Azure tenant ownership, credential rotation and application permissions.

## Further Notes

- The backend's answer text is currently a stub until the template-rendering ticket lands. The bot depends on structured fields plus the answer string, so it should survive that change without rework.
- Exact Agents SDK class and function names must be verified against the installed package before coding. The research relied partly on a reconstructed example.
- The real-Teams demo needs an Azure Bot registration and a public tunnel, which is tenant setup work for the team and not code.

## As Built

What was implemented, including additions and deviations from the decisions above.

**Additions beyond the original scope**

- **Simulator order flow.** The bundled FIX simulator wrote only bare execution reports, so the agent derived no order counters and every answer read "0 submitted". It now writes complete order lifecycles (new order, then a reject or an ack and full fill), one FIX line per write, with a `--reject-rate` option (default 0.2). Without this the demo shows no data.
- **`config/backend.yaml`** enables the NL API with the mock LLM for local runs. The backend treats a missing file as defaults, which leaves NL off. This path is also used by an unmerged branch (UBS-96); the two files will need merging.
- **Dev-only anonymous mode.** Without an Azure app registration the bot cannot start. For local use the SDK's `ANONYMOUS_ALLOWED=true` plus dummy credentials lets Microsoft's Agents Playground drive it. The README states it must never be used on a deployed bot. Real Teams (Azure Bot, tunnel) is documented but not tested against a tenant.
- **Teams app package** (`apps/teams/appPackage/`): manifest, placeholder icons and a build script, for uploading to a real tenant. Untested against one.
- **Card polish.** Dimension values the backend labels `unspecified` render as "All", and the range line is shown in the user's timezone (Singapore, UTC+8 by default) instead of UTC. The backend's own timestamps and the "Show query" JSON stay UTC.

**Deviations**

- FR-NLQ-012 asks for the resolved UTC range to be shown. The card shows it in the user's timezone instead, on request.
- The alert badge sits after the breakdown, matching FR-NLQ-015's order (number, breakdown, open alert, caveats).

**Not done**

- The real-Teams group-chat demo (user story 30) has not been run: the Azure app registration was blocked by tenant permissions. The Agents Playground was used instead.
- HTTP 429 (rate limiting) has no dedicated card yet; it shows the generic "couldn't reach the telemetry service" card until the security ticket (UBS-135) defines the response.

**Backend issues found while testing (not fixed here, owned by the query service)**

- Grouping by `rejectReason` or `instanceId` returns `unspecified`: the store keeps the agent's camelCase dimension names, the query looks up snake_case names. Cards therefore show one "All" row instead of a per-reason breakdown.
- Filtering by dimension (for example symbol) returns nothing, so symbol drilldown answers "0 rejects".
- "Worse than yesterday" fails with "fromUtc is not before toUtc" (yesterday is outside the 6-hour window).
- The time parser does not understand "last hour", "past hour", "since 9am" or "between 9am and 10am"; they silently fall back to 30 minutes.
- Unmatched phrasings such as "give me a rejection summary" fall through to the LLM; with the mock LLM the user sees "could not interpret ... within the time limit", which is misleading wording.
