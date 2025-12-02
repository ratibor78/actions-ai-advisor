"""Tests for LLM client module."""

import httpx
import pytest

from actions_advisor.llm_client import AnalysisResult, LLMClient
from actions_advisor.log_fetcher import JobLog


@pytest.fixture
def sample_job_log() -> JobLog:
    """Sample job log for testing."""
    return JobLog(
        job_name="build",
        step_name="Run tests",
        conclusion="failure",
        raw_logs="Test failed with error",
        exit_code=1,
        duration_seconds=120,
    )


@pytest.mark.asyncio
async def test_analyze_with_openai(respx_mock, sample_job_log):
    """Test analysis with OpenAI provider."""
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": (
                        "## Root Cause\nTest failed due to assertion error\n\n"
                        "## Suggested Fixes\n1. Check test assertions"
                    )
                }
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }

    respx_mock.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    client = LLMClient(
        provider="openai", api_key="test-key", model="gpt-4o-mini"
    )
    result = await client.analyze(sample_job_log, "preprocessed logs")

    assert isinstance(result, AnalysisResult)
    assert "Root Cause" in result.analysis
    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.model_used == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_analyze_with_anthropic(respx_mock, sample_job_log):
    """Test analysis with Anthropic provider."""
    mock_response = {
        "choices": [
            {"message": {"content": "## Root Cause\nDatabase connection failed"}}
        ],
        "usage": {"prompt_tokens": 200, "completion_tokens": 75},
    }

    respx_mock.post("https://api.anthropic.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    client = LLMClient(
        provider="anthropic",
        api_key="test-key",
        model="claude-3-5-haiku-latest",
    )
    result = await client.analyze(sample_job_log, "preprocessed logs")

    assert isinstance(result, AnalysisResult)
    assert "Root Cause" in result.analysis
    assert result.input_tokens == 200
    assert result.output_tokens == 75


@pytest.mark.asyncio
async def test_analyze_with_openrouter(respx_mock, sample_job_log):
    """Test analysis with OpenRouter provider."""
    mock_response = {
        "choices": [{"message": {"content": "Build failed due to missing dependency"}}],
        "usage": {"prompt_tokens": 150, "completion_tokens": 60},
    }

    respx_mock.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    client = LLMClient(
        provider="openrouter",
        api_key="test-key",
        model="anthropic/claude-3.5-haiku",
    )
    result = await client.analyze(sample_job_log, "preprocessed logs")

    assert isinstance(result, AnalysisResult)
    assert "Build failed" in result.analysis


@pytest.mark.asyncio
async def test_analyze_with_selfhosted(respx_mock, sample_job_log):
    """Test analysis with selfhosted provider."""
    mock_response = {
        "choices": [{"message": {"content": "Custom model analysis"}}],
        "usage": {"prompt_tokens": 180, "completion_tokens": 70},
    }

    respx_mock.post("https://custom.llm.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    client = LLMClient(
        provider="selfhosted",
        api_key="test-key",
        model="custom-model",
        base_url="https://custom.llm.com/v1",
    )
    result = await client.analyze(sample_job_log, "preprocessed logs")

    assert isinstance(result, AnalysisResult)
    assert "Custom model" in result.analysis


def test_build_headers_openai():
    """Test header building for OpenAI."""
    client = LLMClient(provider="openai", api_key="test-key", model="gpt-4o-mini")
    headers = client._build_headers()

    assert headers["Authorization"] == "Bearer test-key"
    assert headers["Content-Type"] == "application/json"


def test_build_headers_anthropic():
    """Test header building for Anthropic."""
    client = LLMClient(
        provider="anthropic", api_key="test-key", model="claude-3-5-haiku-latest"
    )
    headers = client._build_headers()

    assert headers["x-api-key"] == "test-key"
    assert headers["anthropic-version"] == "2023-06-01"
    assert headers["content-type"] == "application/json"


def test_build_headers_openrouter():
    """Test header building for OpenRouter."""
    client = LLMClient(
        provider="openrouter", api_key="test-key", model="anthropic/claude-3.5-haiku"
    )
    headers = client._build_headers()

    assert headers["Authorization"] == "Bearer test-key"
    assert headers["HTTP-Referer"] == "https://github.com/actions-advisor"
    assert headers["X-Title"] == "Actions Advisor"
