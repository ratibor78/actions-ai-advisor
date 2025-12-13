"""Unified LLM client for multiple providers."""

from dataclasses import dataclass

import httpx

from actions_ai_advisor.log_fetcher import JobLog

# Provider API endpoints
PROVIDER_ENDPOINTS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

# System prompt for analysis
SYSTEM_PROMPT = """You are an expert CI/CD debugger. Analyze GitHub Actions failures and \
provide clear, actionable guidance.

**Output Format:**

## Root Cause
[1-3 sentences explaining why it failed]

## Recommended Actions
[Numbered list with code examples - be concise for simple issues, detailed for complex ones]

## Error Context
[Key error lines - include stack trace if relevant]

**Style Guidelines:**
- Number your recommendations (1. 2. 3.)
- Include code snippets for fixes when applicable
- Be concise for obvious errors (syntax errors, missing dependencies, simple config issues)
- Be thorough for complex issues (race conditions, integration failures, logic bugs)
- No emojis
- Focus on actionable fixes that developers can implement immediately"""

# User prompt template
USER_PROMPT_TEMPLATE = """Analyze this failed GitHub Actions log:

**Job:** {job_name}
**Step:** {step_name}
**Exit Code:** {exit_code}

```
{log_content}
```"""


@dataclass
class AnalysisResult:
    """Result from LLM analysis."""

    analysis: str
    input_tokens: int
    output_tokens: int
    model_used: str


class LLMClient:
    """Unified client for LLM providers."""

    def __init__(
        self, provider: str, api_key: str, model: str, base_url: str | None = None
    ) -> None:
        """Initialize LLM client.

        Args:
            provider: Provider name (openai, anthropic, openrouter, selfhosted)
            api_key: API key for authentication
            model: Model name
            base_url: Custom base URL (for selfhosted provider)
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or PROVIDER_ENDPOINTS.get(provider, "")

    async def analyze(self, job_log: JobLog, preprocessed_logs: str) -> AnalysisResult:
        """Analyze failed job logs using LLM.

        Args:
            job_log: Job log metadata
            preprocessed_logs: Cleaned log content

        Returns:
            Analysis result with tokens and analysis text
        """
        # Build request
        user_prompt = USER_PROMPT_TEMPLATE.format(
            job_name=job_log.job_name,
            step_name=job_log.step_name,
            exit_code=job_log.exit_code or "N/A",
            log_content=preprocessed_logs,
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 1500,
        }

        # Build headers
        headers = self._build_headers()

        # Send request
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        # Extract response
        analysis = data["choices"][0]["message"]["content"]
        input_tokens = data["usage"]["prompt_tokens"]
        output_tokens = data["usage"]["completion_tokens"]

        return AnalysisResult(
            analysis=analysis,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_used=self.model,
        )

    def _build_headers(self) -> dict[str, str]:
        """Build provider-specific headers.

        Returns:
            Headers dict for the request
        """
        if self.provider == "anthropic":
            return {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
        elif self.provider == "openrouter":
            return {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/actions-advisor",
                "X-Title": "Actions Advisor",
                "Content-Type": "application/json",
            }
        else:
            # OpenAI and selfhosted use standard Bearer auth
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
