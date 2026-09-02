.PHONY: sync parser-test parser-demo metrics-demo lint

sync:
	uv sync

parser-test: sync
	uv run pytest tests/unit/parser/ -v

parser-demo:
	uv run python -m telemetry_agent.parser.cli --corpus apps/agent/testdata/fix/

metrics-demo:
	uv run python -m telemetry_agent.metrics.demo

lint:
	uv run ruff check .
	uv run mypy apps/agent/src
