# Project instructions

SMU FinTech project sponsored by UBS: Unified Telemetry Intelligence for the Magic
trading application.

## Requirements and decisions

Before changing code, read [domain guidance](docs/agents/domain.md), the specs in
`docs/specs/` that cover the affected components, and the relevant decisions in
`docs/adr/`. Use requirement IDs in tests and proposals. Specs are authoritative
requirements; `docs/plan/` contains working notes. Surface conflicts with accepted ADRs
or specs explicitly rather than silently overriding them.

Use the Python version declared in `pyproject.toml` (currently 3.14+).

## Architecture constraints

## Safety

- Never expose, persist, or transmit raw Magic logs or full FIX payloads outside the
  Magic host. Use approved, sanitized telemetry only.
- Never commit secrets or use unapproved UBS production data.

## Development workflow

Build the smallest testable implementation that supports the requirements. Keep changes
within the requested scope.

Before implementing large changes:

1. Inspect the affected code, specs and ADRs.
2. Explain the intended change and identify affected files.
3. Implement the change.
4. Run relevant pytest tests, Ruff formatting/lint checks and mypy type checks. Consult
   `Makefile` and `pyproject.toml` for commands and configured scope.
5. Summarise the result, validation and any remaining limitations.

## Graphify

When `graphify-out/graph.json` exists and the `graphify` command is available:

- For codebase questions, first run `graphify query "<question>"`. Use
  `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for
  focused concepts.
- Use `graphify-out/wiki/index.md` for broad navigation when it exists.
- Read `graphify-out/GRAPH_REPORT.md` for broad architecture reviews or when the scoped
  commands provide insufficient context.
- After modifying code, run `graphify update .` to refresh the graph (AST-only).

If Graphify is unavailable or its results are stale or incomplete, inspect the source
directly. Graph results are navigation aids; verify findings against code.

## Agent guidance

- **Jira work:** Read [issue tracker guidance](docs/agents/issue-tracker.md) before
  reading or updating UBS issues. Use the configured Atlassian Rovo MCP tools when
  available; report unavailable access rather than substituting GitHub Issues.
- **Triage:** Read [triage label mappings](docs/agents/triage-labels.md) when applying
  Jira triage labels.
- **Domain terminology:** Follow [domain guidance](docs/agents/domain.md) when naming
  concepts or proposing spec, glossary or ADR changes.

## Git attribution

- Use the existing Git-configured identity as the commit author; preserve `user.name`
  and `user.email`.
- Commit messages and pull requests must contain no `Co-Authored-By` trailers, AI
  contributor claims, signatures or attribution footers.

## Subagent usage policy

When delegation is appropriate and the runtime supports model selection, prefer Sonnet
for basic exploration and independent implementation. Use Opus subagents only when
advanced reasoning is necessary. If these models are unavailable, use supported models
without assuming a cross-provider equivalent.
