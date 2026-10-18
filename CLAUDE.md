# Project instructions

SMU FinTech project sponsored by UBS: Unified Telemetry Intelligence for the
Magic trading application.

## Requirements and decisions

Before changing code, read [domain guidance](docs/agents/domain.md), the specs in
`docs/specs/` that cover the affected components, and the relevant decisions in
`docs/adr/`. Use requirement IDs in tests and proposals. Specs are authoritative
requirements; `docs/plan/` contains working notes. Surface conflicts with accepted
ADRs or specs explicitly rather than silently overriding them.

Use the Python version declared in `pyproject.toml` (currently 3.14+). Older
architecture documents mentioning Python 3.12 do not lower the workspace minimum.

## Architecture constraints

- Keep the monorepo and shared Pydantic schemas in `packages/telemetry_shared/`.
- User interaction is through Microsoft Teams or Copilot and backend APIs; a
  standalone frontend is outside the current scope.
- Default to one Telemetry Agent per Magic host, with multiple instances supported
  through per-file-set `instanceId` configuration. Per-instance deployment is an
  option when isolation is required (spec 001 §4).
- Many agents publish structured telemetry to one logical, horizontally scalable
  FastAPI backend.
- Day-1 metric storage uses process-local, bounded in-memory time buckets
  ([ADR 0005](docs/adr/0005-in-memory-metric-store.md)). Cross-replica queries must
  preserve completeness through the routing and scatter-gather requirements in
  specs 001 and 006. Redis is not a required Day-1 dependency.
- Keep storage access behind repository/service abstractions; route handlers and
  Teams/Copilot adapters use those interfaces or backend APIs.
- Day-1 requires no durable telemetry storage. Day-2 historical storage must hold
  only approved derived/sanitised telemetry and remain behind storage abstractions.
- Raw Magic logs and full raw FIX payloads must remain on the Magic host and must
  never be copied into telemetry storage, published payloads or diagnostic output
  ([ADR 0004](docs/adr/0004-no-raw-log-persistence.md)). Publish only allowlisted,
  sanitised fields and derived metrics/events.
- Target Agent resource usage: <2% host CPU and <500 MB RAM at the agreed load
  (`NFR-PERF-003`). Keep dependencies lightweight and queues bounded.
- Keep log monitoring, parsing, aggregation, deterministic rules and signed Magic
  callbacks in the Agent. Alerting must continue during a backend outage; callback
  dispatch must not depend on successful backend publication.
- Expensive historical anomaly analysis belongs in the backend. Keep Day-1
  deterministic rules separate from Day-2 anomaly detection.
- Thresholds and anomaly parameters must be configurable. Use synthetic development
  data; UBS production data and thresholds require an approved source.
- The Magic simulator generates configurable FIX send/receive logs for development.
- Prefer asyncio/non-blocking I/O where appropriate. Keep CPU-bound parsing off the
  supervisor loop as described in ADR 0006.
- Use Docker Compose for local stack orchestration when needed. Introduce
  Kubernetes only when explicitly requested.
- Keep secrets out of commits.

## Development workflow

Build the smallest testable implementation that supports the requirements. Keep
changes within the requested scope.

Before implementing large changes:

1. Inspect the affected code, specs and ADRs.
2. Explain the intended change and identify affected files.
3. Implement the change.
4. Run relevant pytest tests, Ruff formatting/lint checks and mypy type checks.
   Consult `Makefile` and `pyproject.toml` for commands and configured scope.
5. Summarise the result, validation and any remaining limitations.

## Graphify

When `graphify-out/graph.json` exists and the `graphify` command is available:

- For codebase questions, first run `graphify query "<question>"`. Use
  `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"`
  for focused concepts.
- Use `graphify-out/wiki/index.md` for broad navigation when it exists.
- Read `graphify-out/GRAPH_REPORT.md` for broad architecture reviews or when the
  scoped commands provide insufficient context.
- After modifying code, run `graphify update .` to refresh the graph (AST-only).

If Graphify is unavailable or its results are stale or incomplete, inspect the
source directly. Graph results are navigation aids; verify findings against code.

## Agent guidance

- **Jira work:** Read [issue tracker guidance](docs/agents/issue-tracker.md) before
  reading or updating UBS issues. Use the configured Atlassian Rovo MCP tools when
  available; report unavailable access rather than substituting GitHub Issues.
- **Triage:** Read [triage label mappings](docs/agents/triage-labels.md) when applying
  Jira triage labels.
- **Domain terminology:** Follow [domain guidance](docs/agents/domain.md) when
  naming concepts or proposing spec, glossary or ADR changes.

## Git attribution

- Use the existing Git-configured identity as the commit author; preserve
  `user.name` and `user.email`.
- Commit messages and pull requests must contain no `Co-Authored-By` trailers,
  AI contributor claims, signatures or attribution footers.

## Subagent usage policy

When delegation is appropriate and the runtime supports model selection, prefer
Sonnet for basic exploration and independent implementation. Use Opus subagents
only when advanced reasoning is necessary. If these models are unavailable, use
supported models without assuming a cross-provider equivalent.
