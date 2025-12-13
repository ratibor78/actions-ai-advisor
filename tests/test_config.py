"""Tests for configuration module."""

import pytest
from pydantic import ValidationError

from actions_ai_advisor.config import Config


def test_config_with_defaults(sample_github_env: dict[str, str]) -> None:
    """Test config loading with default values."""
    config = Config()
    assert config.provider == "openai"
    assert config.model == "gpt-4o-mini"
    assert config.github_token == "ghp_test_token_12345"
    assert config.api_key == "sk-test-key-67890"


def test_config_repo_properties(sample_github_env: dict[str, str]) -> None:
    """Test repository owner and name extraction."""
    config = Config()
    assert config.repo_owner == "test-owner"
    assert config.repo_name == "test-repo"


def test_config_anthropic_provider(
    sample_github_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test config with Anthropic provider."""
    monkeypatch.setenv("INPUT_PROVIDER", "anthropic")
    monkeypatch.setenv("INPUT_MODEL", "claude-3-5-haiku-latest")
    config = Config()
    assert config.provider == "anthropic"
    assert config.model == "claude-3-5-haiku-latest"


def test_config_selfhosted_requires_base_url(
    sample_github_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that selfhosted provider requires base_url."""
    monkeypatch.setenv("INPUT_PROVIDER", "selfhosted")
    with pytest.raises(ValidationError, match="base_url is required"):
        Config()


def test_config_selfhosted_with_base_url(
    sample_github_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test selfhosted provider with base_url."""
    monkeypatch.setenv("INPUT_PROVIDER", "selfhosted")
    monkeypatch.setenv("INPUT_BASE_URL", "https://llm.example.com/v1")
    monkeypatch.setenv("INPUT_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct")
    config = Config()
    assert config.provider == "selfhosted"
    assert config.base_url == "https://llm.example.com/v1"
    assert config.model == "Qwen/Qwen2.5-Coder-32B-Instruct"


def test_config_invalid_provider(
    sample_github_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that invalid provider raises error."""
    monkeypatch.setenv("INPUT_PROVIDER", "invalid")
    with pytest.raises(ValidationError, match="literal_error"):
        Config()
