"""NL LLM configuration and factory."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from telemetry_backend.config import (
    AZURE_LLM_DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_VLLM_BASE_URL,
    OSS_LLM_DEFAULT_TIMEOUT_SECONDS,
    BackendConfigError,
    LlmConfig,
    NlConfig,
    ensure_nl_llm_credentials,
    resolve_llm_config,
)
from telemetry_backend.nl.factory import build_llm_filler
from telemetry_backend.nl.llm.azure_openai import AzureOpenAiSlotFiller
from telemetry_backend.nl.llm.mock import MockLlmSlotFiller
from telemetry_backend.nl.llm.ollama_native import OllamaSlotFiller
from telemetry_backend.nl.llm.openai_compatible import OpenAiCompatibleSlotFiller


def test_resolve_ollama_default_base_url() -> None:
    resolved = resolve_llm_config(
        LlmConfig(provider="ollama", base_url=None),
        timeout_from_yaml=False,
    )
    assert resolved.base_url == DEFAULT_OLLAMA_BASE_URL
    assert resolved.timeout_seconds == OSS_LLM_DEFAULT_TIMEOUT_SECONDS


def test_resolve_vllm_default_base_url() -> None:
    resolved = resolve_llm_config(
        LlmConfig(provider="vllm", base_url=None),
        timeout_from_yaml=False,
    )
    assert resolved.base_url == DEFAULT_VLLM_BASE_URL


def test_resolve_azure_default_timeout() -> None:
    resolved = resolve_llm_config(
        LlmConfig(provider="azure-openai"),
        timeout_from_yaml=False,
    )
    assert resolved.timeout_seconds == AZURE_LLM_DEFAULT_TIMEOUT_SECONDS


def test_factory_ollama_uses_native_client() -> None:
    filler = build_llm_filler(
        NlConfig(
            enabled=True,
            llm=LlmConfig(provider="ollama", base_url="http://localhost:11434/v1"),
        )
    )
    assert isinstance(filler, OllamaSlotFiller)


def test_factory_vllm_uses_compat_client() -> None:
    filler = build_llm_filler(
        NlConfig(
            enabled=True,
            llm=LlmConfig(provider="vllm", base_url="http://localhost:8000/v1"),
        )
    )
    assert isinstance(filler, OpenAiCompatibleSlotFiller)


def test_factory_azure_uses_azure_client() -> None:
    filler = build_llm_filler(
        NlConfig(
            enabled=True,
            llm=LlmConfig(
                provider="azure-openai", endpoint="https://x.openai.azure.com"
            ),
        )
    )
    assert isinstance(filler, AzureOpenAiSlotFiller)


def test_factory_mock() -> None:
    assert isinstance(
        build_llm_filler(NlConfig(enabled=True, llm=LlmConfig(provider="mock"))),
        MockLlmSlotFiller,
    )


def test_ensure_credentials_azure_requires_key() -> None:
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(BackendConfigError, match="MAGIC_TELEMETRY_LLM_API_KEY"):
            ensure_nl_llm_credentials(
                NlConfig(
                    enabled=True,
                    llm=LlmConfig(provider="azure-openai"),
                )
            )


def test_ensure_credentials_ollama_without_key_ok() -> None:
    with patch.dict("os.environ", {}, clear=True):
        ensure_nl_llm_credentials(
            NlConfig(
                enabled=True,
                llm=LlmConfig(provider="ollama", require_api_key=False),
            )
        )


def test_ensure_credentials_compat_require_api_key() -> None:
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(BackendConfigError):
            ensure_nl_llm_credentials(
                NlConfig(
                    enabled=True,
                    llm=LlmConfig(provider="openai-compatible", require_api_key=True),
                )
            )
