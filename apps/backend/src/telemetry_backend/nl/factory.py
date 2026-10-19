"""Construct NL services from backend configuration."""

from __future__ import annotations

from telemetry_backend.config import NlConfig, OSS_LLM_PROVIDERS, StreamProcessorConfig
from telemetry_backend.nl.llm.azure_openai import AzureOpenAiSlotFiller
from telemetry_backend.nl.llm.mock import MockLlmSlotFiller, default_mock_responses
from telemetry_backend.nl.llm.openai_compatible import OpenAiCompatibleSlotFiller
from telemetry_backend.nl.llm.protocol import LlmSlotFiller
from telemetry_backend.nl.service import NlQueryService
from telemetry_backend.services.alert_store import AlertStore
from telemetry_backend.services.query_engine import QueryEngine


def build_llm_filler(config: NlConfig) -> LlmSlotFiller:
    llm = config.llm
    provider = llm.provider
    if provider == "mock":
        return MockLlmSlotFiller(default_mock_responses())
    if provider in OSS_LLM_PROVIDERS:
        return OpenAiCompatibleSlotFiller(llm)
    if provider == "azure-openai":
        return AzureOpenAiSlotFiller(llm)
    raise ValueError(f"unsupported nl.llm.provider {provider!r}")


def build_nl_service(
    config: NlConfig,
    *,
    query_engine: QueryEngine,
    alert_store: AlertStore,
    stream_config: StreamProcessorConfig,
    llm: LlmSlotFiller | None = None,
) -> NlQueryService:
    return NlQueryService(
        config=config,
        query_engine=query_engine,
        alert_store=alert_store,
        llm=llm or build_llm_filler(config),
        max_range_seconds=stream_config.retention_window_seconds,
    )
