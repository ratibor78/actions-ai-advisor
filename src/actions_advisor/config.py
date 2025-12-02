"""Configuration module for Actions Advisor."""

import os
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuration for Actions Advisor from GitHub Actions inputs and environment."""

    model_config = SettingsConfigDict(
        env_prefix="INPUT_",
        case_sensitive=False,
    )

    # GitHub Actions inputs (passed as INPUT_* env vars)
    github_token: str = Field(..., description="GitHub token for API access")
    api_key: str = Field(..., description="API key for the LLM provider")
    provider: Literal["openai", "anthropic", "openrouter", "selfhosted"] = Field(
        default="openai", description="LLM provider"
    )
    model: str = Field(default="gpt-4o-mini", description="Model name")
    base_url: str | None = Field(default=None, description="Custom API URL for selfhosted")

    # GitHub Actions environment variables (no INPUT_ prefix)
    github_repository: str = Field(
        default_factory=lambda: os.getenv("GITHUB_REPOSITORY", "")
    )
    github_run_id: str = Field(default_factory=lambda: os.getenv("GITHUB_RUN_ID", ""))
    github_event_name: str = Field(
        default_factory=lambda: os.getenv("GITHUB_EVENT_NAME", "")
    )
    github_step_summary: str = Field(
        default_factory=lambda: os.getenv("GITHUB_STEP_SUMMARY", "")
    )

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str | None, info: dict) -> str | None:
        """Validate base_url is provided for selfhosted provider."""
        provider = info.data.get("provider")
        if provider == "selfhosted" and not v:
            raise ValueError("base_url is required when provider is 'selfhosted'")
        return v

    @property
    def repo_owner(self) -> str:
        """Extract repository owner from GITHUB_REPOSITORY."""
        if "/" in self.github_repository:
            return self.github_repository.split("/")[0]
        return ""

    @property
    def repo_name(self) -> str:
        """Extract repository name from GITHUB_REPOSITORY."""
        if "/" in self.github_repository:
            return self.github_repository.split("/")[1]
        return ""
