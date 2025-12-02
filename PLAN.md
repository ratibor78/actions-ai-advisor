# Actions Advisor - Project Plan

> AI-powered GitHub Actions failure explainer that provides clear, actionable insights without leaving your workflow.

## 📋 Executive Summary

**Actions Advisor** is a GitHub Action that automatically analyzes failed workflow runs and provides intelligent, LLM-powered explanations directly as PR comments and job summaries.

### Design Principles

1. **Simple** — Minimal config, sensible defaults, just works
2. **Fast** — Smart log preprocessing, quick execution
3. **Cheap** — Token-efficient, displays cost per request
4. **Flexible** — OpenAI, Anthropic, OpenRouter, or self-hosted
5. **Universal** — Works with any language/toolchain

---

## 🎯 Project Name

**`actions-advisor`** — clear, professional, describes purpose.

---

## 🚀 Usage (Final Result)

```yaml
analyze-failure:
  needs: build
  if: failure()
  runs-on: ubuntu-latest
  permissions:
    actions: read
  steps:
    - name: Analyze Failure
      uses: your-org/actions-advisor@v1
      with:
        github-token: ${{ secrets.GITHUB_TOKEN }}
        api-key: ${{ secrets.OPENAI_API_KEY }}
        provider: openai
        model: gpt-4o-mini
```

**That's it.** 4 parameters. Output appears in **Job Summary** — no PR spam, no extra permissions.

---

## ⚙️ Action Configuration (action.yml)

Minimal inputs — everything else has smart defaults internally.

```yaml
name: 'Actions Advisor'
description: 'AI-powered GitHub Actions failure analysis'
author: 'Your Name'
branding:
  icon: 'alert-circle'
  color: 'orange'

inputs:
  github-token:
    description: 'GitHub token for API access'
    required: true

  api-key:
    description: 'API key for the LLM provider'
    required: true

  provider:
    description: 'LLM provider: openai, anthropic, openrouter, selfhosted'
    required: false
    default: 'openai'

  model:
    description: 'Model name (provider-specific)'
    required: false
    default: 'gpt-4o-mini'

  base-url:
    description: 'Custom API URL (only for selfhosted provider)'
    required: false

runs:
  using: 'docker'
  image: 'Dockerfile'
```

**5 inputs total.** `base-url` only needed for self-hosted LLMs.

### Provider Examples

```yaml
# OpenAI (default)
with:
  github-token: ${{ secrets.GITHUB_TOKEN }}
  api-key: ${{ secrets.OPENAI_API_KEY }}

# OpenAI with specific model
with:
  github-token: ${{ secrets.GITHUB_TOKEN }}
  api-key: ${{ secrets.OPENAI_API_KEY }}
  model: gpt-4o

# Anthropic Claude
with:
  github-token: ${{ secrets.GITHUB_TOKEN }}
  api-key: ${{ secrets.ANTHROPIC_API_KEY }}
  provider: anthropic
  model: claude-3-5-haiku-latest

# OpenRouter (any model)
with:
  github-token: ${{ secrets.GITHUB_TOKEN }}
  api-key: ${{ secrets.OPENROUTER_API_KEY }}
  provider: openrouter
  model: anthropic/claude-3.5-haiku

# Self-hosted (vLLM, Ollama, etc.)
with:
  github-token: ${{ secrets.GITHUB_TOKEN }}
  api-key: ${{ secrets.VLLM_API_KEY }}
  provider: selfhosted
  base-url: https://llm.internal.company.com/v1
  model: Qwen/Qwen2.5-Coder-32B-Instruct
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Actions Workflow                     │
├─────────────────────────────────────────────────────────────────┤
│  1. Workflow fails                                               │
│  2. actions-advisor step runs (if: failure())                   │
│  3. Fetches failed job logs via GitHub API                      │
│  4. Preprocesses logs (extracts errors, trims noise)            │
│  5. Sends to configured LLM provider                            │
│  6. Writes analysis to Job Summary (visible in workflow run)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
actions-advisor/
├── .github/
│   └── workflows/
│       ├── ci.yml                # Lint, test, type-check
│       └── release.yml           # Build & push Docker image
├── src/
│   └── actions_advisor/
│       ├── __init__.py
│       ├── main.py               # Entry point
│       ├── config.py             # Input parsing (from env)
│       ├── log_fetcher.py        # GitHub API log retrieval
│       ├── preprocessor.py       # Log cleaning & extraction
│       ├── llm_client.py         # Unified LLM client (all providers)
│       ├── formatter.py          # Markdown output formatting
│       └── tokens.py             # Token counting & cost estimation
├── tests/
│   ├── conftest.py
│   ├── test_preprocessor.py
│   ├── test_llm_client.py
│   └── fixtures/
│       └── sample_logs/          # Real-world log samples
├── action.yml                    # GitHub Action definition
├── Dockerfile                    # Container action
├── pyproject.toml                # Project config (uv)
├── uv.lock
├── README.md
├── LICENSE                       # MIT
└── CLAUDE.md                     # AI development guide
```

---

## 🔧 Technical Stack

| Component | Technology | Why |
|-----------|------------|-----|
| Language | Python 3.12+ | Great LLM libraries |
| Package Manager | uv | Fast, modern |
| HTTP Client | httpx | Async, clean API |
| Config | pydantic-settings | Validate inputs |
| Type Checking | mypy | Catch errors early |
| Linting | ruff | Fast, comprehensive |
| Testing | pytest | Standard |
| Action Type | Docker | Reproducible |

### Dependencies (pyproject.toml)

```toml
[project]
name = "actions-advisor"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "tiktoken>=0.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "mypy>=1.13",
    "ruff>=0.8",
]

[project.scripts]
actions-advisor = "actions_advisor.main:main"
```

**Note:** No `openai` or `anthropic` SDK needed — all providers use OpenAI-compatible REST API via `httpx`.

---

## 🔌 Unified LLM Client

All providers (including Anthropic) support OpenAI-compatible API format. Single client handles everything.

```python
# src/actions_advisor/llm_client.py

PROVIDER_ENDPOINTS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

class LLMClient:
    def __init__(self, provider: str, api_key: str, model: str, base_url: str | None = None):
        self.base_url = base_url or PROVIDER_ENDPOINTS.get(provider)
        self.api_key = api_key
        self.model = model
        self.provider = provider

    async def analyze(self, log_content: str) -> AnalysisResult:
        # Single implementation works for all providers
        ...
```

---

## 📊 Token & Cost Estimation

Display token usage and estimated cost in output (hardcoded internally, not configurable).

| Provider | Model | Input $/1M | Output $/1M |
|----------|-------|------------|-------------|
| OpenAI | gpt-4o-mini | $0.15 | $0.60 |
| OpenAI | gpt-4o | $2.50 | $10.00 |
| Anthropic | claude-3-5-haiku | $0.80 | $4.00 |
| Anthropic | claude-sonnet-4 | $3.00 | $15.00 |
| OpenRouter | (pass-through) | varies | varies |

### Typical Cost Per Analysis

| Log Size | Tokens (after preprocessing) | Cost (gpt-4o-mini) |
|----------|------------------------------|---------------------|
| Small | ~2,000 | ~$0.0003 |
| Medium | ~5,000 | ~$0.0008 |
| Large | ~10,000 | ~$0.0015 |

---

## 📝 Log Preprocessing

Smart preprocessing to minimize tokens (all hardcoded defaults):

```python
# src/actions_advisor/preprocessor.py

def preprocess_logs(raw_logs: str) -> str:
    """
    1. Remove ANSI color codes
    2. Remove timestamp prefixes
    3. Collapse repeated lines ("npm WARN" x100 → single line)
    4. Extract only failed steps
    5. Keep last 150 lines per failed step
    6. Remove GitHub Actions metadata noise
    """
    ...
```

---

## 🖼️ Output Format

Writes to **Job Summary** (via `$GITHUB_STEP_SUMMARY`) — visible directly in workflow run.

```markdown
## 🔍 Actions Advisor

### ❌ Failed: `build-and-test` → `Run tests`

**Exit Code:** 1 | **Duration:** 2m 34s

---

### 🎯 Root Cause

The test `test_user_authentication` failed due to a **connection timeout**
when connecting to the test database. The PostgreSQL container did not
start before tests began.

### 💡 Suggested Fixes

1. **Add health check wait** before running tests:
   ```yaml
   - name: Wait for PostgreSQL
     run: until pg_isready -h localhost; do sleep 1; done
   ```

2. **Check `services` block** has proper health check config

### 📋 Error Snippet

```
FAILED tests/test_auth.py::test_user_authentication
psycopg2.OperationalError: connection timed out
```

---

<sub>📊 3,247 input + 423 output tokens | 💰 ~$0.0005 (gpt-4o-mini)</sub>
```

---

## 🗓️ Implementation Phases

### Phase 1: Core (2-3 days)
- [ ] Project setup with uv
- [ ] `config.py` — parse action inputs from env
- [ ] `log_fetcher.py` — GitHub API integration
- [ ] `preprocessor.py` — log cleaning
- [ ] `llm_client.py` — unified client (OpenAI-compatible)
- [ ] `formatter.py` — markdown output to Job Summary
- [ ] `main.py` — orchestration
- [ ] Basic tests with fixture logs
- [ ] `Dockerfile` + `action.yml`

### Phase 2: Polish (1-2 days)
- [ ] `tokens.py` — counting + cost display
- [ ] Better error extraction in preprocessor
- [ ] Handle edge cases (empty logs, API errors)
- [ ] More test coverage
- [ ] README with examples

### Phase 3: Release (1 day)
- [ ] CI workflow (lint, test, type-check)
- [ ] Release workflow (Docker build + push)
- [ ] Tag v1.0.0

### Future (Post v1.0)
- [ ] PR comment mode (optional)
- [ ] Auto-fix mode with PR creation
- [ ] Custom system prompts
- [ ] Slack/Discord notifications

---

## 📂 Key Implementation Details

### 1. config.py

```python
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    github_token: str
    api_key: str
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    base_url: str | None = None

    # Auto-populated by GitHub Actions
    github_repository: str
    github_run_id: str
    github_event_name: str
    github_event_path: str

    class Config:
        env_prefix = "INPUT_"  # GitHub Actions passes inputs as INPUT_*
```

### 2. Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source
COPY src/ ./src/

ENTRYPOINT ["uv", "run", "actions-advisor"]
```

### 3. LLM Prompt (hardcoded in llm_client.py)

```python
SYSTEM_PROMPT = """You are an expert CI/CD debugger. Analyze the GitHub Actions failure and provide:

1. **Root Cause** — Clear explanation of why the build failed
2. **Suggested Fixes** — Actionable steps to resolve the issue
3. **Error Snippet** — The most relevant error lines

Be concise. Use markdown. Focus on actionable advice."""

USER_PROMPT_TEMPLATE = """Analyze this failed GitHub Actions log:

**Job:** {job_name}
**Step:** {step_name}

```
{log_content}
```"""
```

### 4. Job Summary Output

```python
# Writing to Job Summary is simple - just append to $GITHUB_STEP_SUMMARY
import os

def write_summary(markdown: str) -> None:
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(markdown)
```

### 5. GitHub API Log Fetching

```python
# Key endpoints used:
# GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs
# GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs

async def fetch_failed_job_logs(github_token: str, repo: str, run_id: str) -> list[JobLog]:
    # 1. Get all jobs for the run
    # 2. Filter to failed jobs
    # 3. For each failed job, fetch logs (follows 302 redirect)
    # 4. Return structured JobLog objects
    ...
```

---

## 🔒 Security Notes

- API keys passed as secrets, never logged
- Logs may contain sensitive data — action only reads, never stores
- Minimal permission: `actions: read` only

---

## 📈 Success Criteria

| Metric | Target |
|--------|--------|
| Execution time | < 30 seconds |
| Token reduction (preprocessing) | 70%+ |
| Useful root cause identification | 80%+ |
| Cost per analysis | < $0.01 |

---

## 📝 Full Workflow Example

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test
      - run: npm run build

  analyze-failure:
    needs: build
    if: failure()
    runs-on: ubuntu-latest
    permissions:
      actions: read
    steps:
      - name: Analyze Failure
        uses: your-org/actions-advisor@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          api-key: ${{ secrets.OPENAI_API_KEY }}
          provider: openai
          model: gpt-4o-mini
```

---

## 🏁 Getting Started (For Claude Code)

**Priority order:**

1. `uv init actions-advisor && cd actions-advisor`
2. Create `src/actions_advisor/` structure
3. Implement `config.py` (pydantic-settings)
4. Implement `log_fetcher.py` (GitHub API)
5. Implement `preprocessor.py` with test fixtures
6. Implement `llm_client.py` (unified, OpenAI-compatible)
7. Implement `formatter.py` (markdown → Job Summary)
8. Wire up `main.py`
9. Create `Dockerfile` + `action.yml`
10. Test with real failed workflow

**Estimated time:** 1 day for working v1.

---

