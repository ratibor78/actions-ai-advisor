"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_github_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Provide sample GitHub Actions environment variables."""
    env_vars = {
        "INPUT_GITHUB_TOKEN": "ghp_test_token_12345",
        "INPUT_API_KEY": "sk-test-key-67890",
        "INPUT_PROVIDER": "openai",
        "INPUT_MODEL": "gpt-4o-mini",
        "GITHUB_REPOSITORY": "test-owner/test-repo",
        "GITHUB_RUN_ID": "123456789",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_STEP_SUMMARY": "/tmp/step_summary.md",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars
