.PHONY: sync parser-test pipeline-test pipeline-demo parser-demo metrics-demo metrics-quickstart metrics-bridge-quickstart rules-test rules-quickstart rules-reload-demo stream-processor-quickstart callback-test callback-demo publish-test publish-demo nl-eval mcp-run mcp-test lint \
	ollama-check ollama-setup backend-run simulator-run agent-run teams-run playground mcp-inspector

# Local LLM for the NL query path (spec 008). Keep OLLAMA_MODEL in step with
# nl.llm.model in config/backend.yaml.
OLLAMA_HOST ?= http://127.0.0.1:11434
OLLAMA_MODEL ?= llama3.2
BACKEND_CONFIG ?= config/backend.yaml

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

publish-test: sync
	uv run pytest tests/unit/agent/publishing/ tests/unit/agent/common/ \
	  tests/unit/agent/health/test_buffer_bytes_and_drops.py -v
	uv run pytest tests/integration/agent/ -k "FR_PUB or UBS_103 or UBS_104" -v

publish-demo:
	uv run python -m telemetry_agent.publishing.demo_quickstart

metrics-demo:
	uv run python -m telemetry_agent.metrics.demo

metrics-quickstart:
	uv run python -m telemetry_agent.metrics.demo_quickstart

metrics-bridge-quickstart:
	uv run python -m telemetry_agent.parser.demo_metrics_bridge

rules-test: sync
	uv run pytest tests/unit/agent/rules/ tests/integration/agent/ -k "rules or RE_" -v

rules-quickstart:
	uv run python -m telemetry_agent.rules.demo_quickstart

rules-reload-demo:
	uv run python -m telemetry_agent.rules.demo_reload

stream-processor-quickstart:
	uv run python -m telemetry_backend.services.demo_quickstart

nl-eval: sync
	uv run pytest tests/unit/backend/nl/test_nl_eval_fixtures.py -v

ollama-check:
	@command -v ollama >/dev/null || { echo "Ollama is not installed. See README.md > Prerequisites."; exit 1; }
	@curl -sf $(OLLAMA_HOST)/api/tags >/dev/null || { echo "Ollama is not running at $(OLLAMA_HOST). Start the Ollama app or run: ollama serve"; exit 1; }
	@curl -sf $(OLLAMA_HOST)/api/tags | grep -q '"name":"$(OLLAMA_MODEL)' || { echo "Model $(OLLAMA_MODEL) is not pulled. Run: make ollama-setup"; exit 1; }
	@echo "Ollama OK: $(OLLAMA_MODEL) at $(OLLAMA_HOST)"

ollama-setup:
	@command -v ollama >/dev/null || { echo "Ollama is not installed. See README.md > Prerequisites."; exit 1; }
	ollama pull $(OLLAMA_MODEL)

backend-run: sync ollama-check
	uv run telemetry-backend --config $(BACKEND_CONFIG)

simulator-run:
	uv run python apps/simulator/src/simulator/mock_logger.py

agent-run:
	uv run telemetry-agent --config config/agent.yaml

# Dev only: dummy Azure credentials with anonymous access. Never use on a deployed bot.
teams-run:
	CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=00000000-0000-0000-0000-000000000000 \
	CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=dummy \
	CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=00000000-0000-0000-0000-000000000000 \
	CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED=true \
	uv run telemetry-teams

playground:
	npx @microsoft/teams-app-test-tool start -e http://localhost:3978/api/messages -c msteams

mcp-inspector:
	npx @modelcontextprotocol/inspector

mcp-run: sync
	uv run telemetry-mcp

mcp-test: sync
	uv run pytest tests/unit/mcp -v

lint:
	uv run ruff check .
	uv run mypy apps/agent/src
