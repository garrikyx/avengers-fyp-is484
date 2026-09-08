.PHONY: sync parser-test parser-demo metrics-demo lint

sync:
	uv sync

parser-test: sync
	uv run pytest tests/unit/agent/parser/ -v

MAGIC_TELEMETRY_ID_HASH_KEY ?= dev-only
export MAGIC_TELEMETRY_ID_HASH_KEY

parser-demo:
	uv run python -m telemetry_agent.parser.cli --corpus apps/agent/testdata/fix/

metrics-demo:
	uv run python -m telemetry_agent.metrics.demo

lint:
	uv run ruff check .
	uv run mypy apps/agent/src
