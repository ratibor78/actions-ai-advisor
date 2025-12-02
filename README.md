# Actions Advisor

> AI-powered GitHub Actions failure analysis that provides clear, actionable insights without leaving your workflow.

## Quick Start

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

## Features

- **Simple** — Minimal config, sensible defaults, just works
- **Fast** — Smart log preprocessing, quick execution
- **Cheap** — Token-efficient, displays cost per request
- **Flexible** — OpenAI, Anthropic, OpenRouter, or self-hosted
- **Universal** — Works with any language/toolchain

## Configuration

### Inputs

- `github-token` (required): GitHub token for API access
- `api-key` (required): API key for the LLM provider
- `provider` (optional, default: `openai`): LLM provider (`openai`, `anthropic`, `openrouter`, `selfhosted`)
- `model` (optional, default: `gpt-4o-mini`): Model name (provider-specific)
- `base-url` (optional): Custom API URL (only for `selfhosted` provider)

### Provider Examples

#### OpenAI (Default)

```yaml
- uses: your-org/actions-advisor@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    api-key: ${{ secrets.OPENAI_API_KEY }}
    # provider: openai  # default
    # model: gpt-4o-mini  # default
```

#### OpenAI with GPT-4

```yaml
- uses: your-org/actions-advisor@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    api-key: ${{ secrets.OPENAI_API_KEY }}
    model: gpt-4o
```

#### Anthropic Claude

```yaml
- uses: your-org/actions-advisor@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    provider: anthropic
    model: claude-3-5-haiku-latest
```

#### OpenRouter (Any Model)

```yaml
- uses: your-org/actions-advisor@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    api-key: ${{ secrets.OPENROUTER_API_KEY }}
    provider: openrouter
    model: anthropic/claude-3.5-haiku
```

#### Self-Hosted (vLLM, Ollama, etc.)

```yaml
- uses: your-org/actions-advisor@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    api-key: ${{ secrets.VLLM_API_KEY }}
    provider: selfhosted
    base-url: https://llm.internal.company.com/v1
    model: Qwen/Qwen2.5-Coder-32B-Instruct
```

## Output Example

Actions Advisor writes the analysis to the **Job Summary**, visible directly in the GitHub Actions workflow run. Example output:

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

## Cost & Token Usage

Actions Advisor uses smart log preprocessing to minimize token usage (~70% reduction). Typical costs per analysis:

| Log Size | Tokens (preprocessed) | Cost (gpt-4o-mini) |
|----------|----------------------|-------------------|
| Small    | ~2,000               | ~$0.0003          |
| Medium   | ~5,000               | ~$0.0008          |
| Large    | ~10,000              | ~$0.0015          |

### Model Pricing (per 1M tokens)

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| OpenAI | gpt-4o-mini | $0.15 | $0.60 |
| OpenAI | gpt-4o | $2.50 | $10.00 |
| Anthropic | claude-3-5-haiku | $0.80 | $4.00 |
| Anthropic | claude-sonnet-4 | $3.00 | $15.00 |

## How It Works

1. Workflow fails
2. `actions-advisor` step runs (if: failure())
3. Fetches failed job logs via GitHub API
4. Preprocesses logs (extracts errors, trims noise)
5. Sends to configured LLM provider
6. Writes analysis to Job Summary (visible in workflow run)

## Development

### Setup

```bash
# Install uv
pip install uv

# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

## License

MIT
