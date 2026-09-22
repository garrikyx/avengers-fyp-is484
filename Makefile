.PHONY: sync parser-test pipeline-test pipeline-demo parser-demo metrics-demo metrics-quickstart stream-processor-quickstart callback-test callback-demo lint

sync:
	uv sync

parser-test: sync
	uv run pytest tests/unit/agent/parser/ -v

pipeline-test: sync
	uv run pytest tests/unit/agent/pipeline/ tests/integration/agent/ -k "FR_PIP or pipeline_demo" -v

pipeline-demo: sync
	uv run python apps/agent/src/pipeline_demo.py \
	  --corpus apps/agent/testdata/fix/demo_logs.txt \
	  --config apps/agent/testdata/magic/demo_config.yaml

MAGIC_TELEMETRY_ID_HASH_KEY ?= dev-only
export MAGIC_TELEMETRY_ID_HASH_KEY

parser-demo:
	uv run python -m telemetry_agent.parser.cli \
	  --corpus apps/agent/testdata/fix/demo_logs.txt \
	  --corpus apps/agent/testdata/magic/ \
	  --config apps/agent/testdata/magic/demo_config.yaml

callback-test: sync
	uv run pytest tests/unit/agent/callbacks/ -v

callback-demo:
	uv run python -m telemetry_agent.callbacks.demo_quickstart

metrics-demo:
	uv run python -m telemetry_agent.metrics.demo

metrics-quickstart:
	uv run python -m telemetry_agent.metrics.demo_quickstart

metrics-bridge-quickstart:
	uv run python -m telemetry_agent.parser.demo_metrics_bridge

stream-processor-quickstart:
	uv run python -m telemetry_backend.services.demo_quickstart

lint:
	uv run ruff check .
	uv run mypy apps/agent/src
