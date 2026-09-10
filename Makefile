.PHONY: sync parser-test parser-demo metrics-demo metrics-quickstart stream-processor-quickstart lint

sync:
	uv sync

parser-test: sync
	uv run pytest tests/unit/agent/parser/ -v

MAGIC_TELEMETRY_ID_HASH_KEY ?= dev-only
export MAGIC_TELEMETRY_ID_HASH_KEY

parser-demo:
	uv run python -m telemetry_agent.parser.cli \
	  --corpus apps/agent/testdata/fix/demo_logs.txt \
	  --corpus apps/agent/testdata/magic/ \
	  --config apps/agent/testdata/magic/demo_config.yaml

metrics-demo:
	uv run python -m telemetry_agent.metrics.demo

metrics-quickstart:
	uv run python -m telemetry_agent.metrics.demo_quickstart

stream-processor-quickstart:
	uv run python -m telemetry_backend.services.demo_quickstart

lint:
	uv run ruff check .
	uv run mypy apps/agent/src
