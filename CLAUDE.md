This is an SMU FinTech project sponsored by UBS called Unified Telemetry Intelligence for the Magic trading application.

Architecture constraints:

- Monorepo.
- Python 3.14+ unless a strong technical reason requires otherwise.
- No frontend. User interface is Microsoft Teams.
- One Magic instance has one Telemetry Agent deployed alongside it.
- Many Telemetry Agents send structured telemetry to one logical Telemetry Backend.
- Backend must support horizontal scaling.
- Backend instances should be stateless.
- Redis is the shared volatile Day-1 state store.
- Day-1 must not require persistent telemetry storage.
- Day-2 adds PostgreSQL for permitted historical telemetry.
- Never persist raw Magic logs or full raw FIX payloads.
- Persist only necessary derived/sanitised telemetry such as aggregated metrics, alert history, anomaly records, callback delivery state, configuration history, and approved structured fields.
- Telemetry Agent must target <2% host CPU and <500 MB RAM.
- Agent performs lightweight processing close to Magic:
  log monitor -> parser -> metrics aggregator -> rule engine -> callback dispatcher -> backend publisher -> health reporter.
- Expensive historical anomaly analysis belongs in the backend, not the Agent.
- Backend uses FastAPI.
- Shared schemas use Pydantic.
- Redis access must be abstracted through repositories/services, not called directly from FastAPI route handlers.
- Day-2 persistence should similarly use repository abstractions.
- Microsoft Teams integration talks only to Backend APIs and must not directly query Redis/PostgreSQL.
- Magic simulator generates configurable FIX send/receive logs for development.
- Docker Compose should eventually allow developers to run the local stack easily.
- Use pytest for testing.
- Use Ruff for formatting/linting.
- Use mypy or equivalent static type checking.
- Prefer asyncio/non-blocking I/O where appropriate.
- Keep dependencies lightweight, especially in the Telemetry Agent.
- Do not introduce Kubernetes unless specifically requested.
- Never commit secrets.
- Do not invent UBS-specific production data or thresholds.
- Thresholds and anomaly parameters must be configurable.
- Maintain clear separation between Day-1 deterministic rules and Day-2 anomaly detection.

Development principle:
Do not overengineer. Build the smallest testable implementation that supports the architecture and user stories.

Before implementing large changes:
1. inspect existing code,
2. explain the intended change,
3. identify affected files,
4. implement,
5. run tests/lint/type checks,
6. summarise results.

Do not make unrelated changes.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Agent skills

### Issue tracker

Issues live in Jira project UBS (avengersfyp.atlassian.net), via the Atlassian Rovo MCP tools. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), applied as Jira labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `GLOSSARY.md` (created lazily) + `docs/adr/`, with `docs/specs/` as the requirements source. See `docs/agents/domain.md`.
