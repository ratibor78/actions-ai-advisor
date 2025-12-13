<div align="center">

<!-- Logo -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/assets/logos/logo-dark.png">
  <source media="(prefers-color-scheme: light)" srcset=".github/assets/logos/logo-main.png">
  <img alt="Actions AI Advisor" src=".github/assets/logos/logo-main.png" height="200" width="600">
</picture>

**Stop digging through CI logs manually. Let AI explain failures for you.**

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Actions%20AI%20Advisor-blue?style=flat-square&logo=github)](https://github.com/marketplace/actions/actions-ai-advisor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![CI Status](https://img.shields.io/github/actions/workflow/status/ratibor78/actions-ai-advisor/ci.yml?branch=main&label=tests&style=flat-square)](https://github.com/ratibor78/actions-ai-advisor/actions)
[![Latest Release](https://img.shields.io/github/v/release/ratibor78/actions-ai-advisor?style=flat-square&color=orange)](https://github.com/ratibor78/actions-ai-advisor/releases)

<p align="center">
  <a href="#features">Key Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#language-support">Language Support</a>
</p>

</div>

---

## <a name="features"></a>Features

- **Intelligent analysis** — AI-powered root cause analysis directly in workflow summaries
- **Affected files detection** — Automatically extracts and links to files mentioned in errors
- **Multi-language support** — 10+ languages: Python, JS/TS, Go, Rust, Java, C#, PHP, Ruby, C/C++
- **Cross-platform paths** — Works with both Linux (`/path/file`) and Windows (`C:\path\file`) runners
- **Matrix build support** — Handles workflows with 100+ jobs via automatic pagination
- **Smart preprocessing** — Reduces logs by 70%+ to minimize token costs
- **Clickable file links** — Direct navigation to error locations with line numbers
- **Working directory detection** — Resolves paths correctly for monorepos (Rust Cargo, Go modules)
- **Library filtering** — Excludes JDK/system files from stack traces (Java, Python)
- **Cost transparency** — Shows token usage and estimated cost per analysis
- **Provider flexibility** — OpenAI, Anthropic, OpenRouter, or self-hosted LLMs
- **Zero config** — Works out of the box with minimal inputs

---

## <a name="language-support"></a>Language Support

Supports **10+ languages** with automatic file path extraction and clickable GitHub links to exact error locations:

**Python** • **JavaScript/TypeScript** • **Go** • **Rust** • **Java** • **.NET/C#** • **PHP** • **Ruby** • **C/C++** • **Docker**

**Features:** Cross-platform paths (Linux + Windows) • Context-aware path resolution • Library file filtering • Monorepo support • 70% token reduction

[See detailed language support →](docs/language-support.md)

---

## <a name="how-it-works"></a>How It Works

Actions AI Advisor automatically analyzes failed workflows in 5 steps:

1. **Fetches logs** from GitHub Actions API when a job fails (with pagination for matrix builds)
2. **Preprocesses** to remove noise and reduce tokens by ~70%
3. **Extracts file paths** from error messages (10+ languages, Linux + Windows paths)
4. **Sends to LLM** for intelligent root cause analysis
5. **Outputs** formatted markdown to GitHub Job Summary with clickable file links

**End-to-end:** 10-30 seconds • **Cost:** ~$0.0005 per analysis

[See detailed architecture →](docs/architecture.md)

---

## <a name="quick-start"></a>Quick Start

### Basic Setup

Add this to your workflow — when CI fails, you'll get AI analysis in the job summary:

```yaml
name: CI with AI Advisor

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: npm test  # or pytest, go test, cargo test, etc.

  ai-advisor:
    runs-on: ubuntu-latest
    if: failure()
    needs: test
    permissions:
      actions: read
    steps:
      - uses: ratibor78/actions-ai-advisor@v1
        with:
          github-token: ${{ github.token }}
          api-key: ${{ secrets.OPENAI_API_KEY }}
          provider: openai
          model: gpt-4o-mini
```

**Cost:** ~$0.0003-0.0008 per analysis (≈1000-3000 analyses per $1)

### Universal Gateway Pattern

Catch failures from **ANY** job in your workflow:

```yaml
name: CI Pipeline

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run lint

  # Universal Gateway - catches failures from ANY job above
  ai-advisor:
    runs-on: ubuntu-latest
    if: failure()
    needs: [build, test, lint]  # List ALL jobs here
    permissions:
      actions: read
    steps:
      - uses: ratibor78/actions-ai-advisor@v1
        with:
          github-token: ${{ github.token }}
          api-key: ${{ secrets.OPENAI_API_KEY }}
          provider: openai
          model: gpt-4o-mini
```

**How it works:**
- ✅ `needs: [build, test, lint]` — waits for all jobs to complete
- ✅ `if: failure()` — only runs if **any** needed job failed
- ✅ AI Advisor analyzes logs from the failed job(s)
- ✅ Provides root cause analysis in workflow summary

---

## <a name="configuration"></a>Configuration

### Common Options

```yaml
- uses: ratibor78/actions-ai-advisor@v1
  with:
    # Required
    github-token: ${{ github.token }}
    api-key: ${{ secrets.OPENAI_API_KEY }}

    # Optional
    provider: openai              # openai, anthropic, openrouter, selfhosted
    model: gpt-4o-mini            # Provider-specific model name
    base-url: ""                  # Custom API URL (self-hosted only)
```

### LLM Providers

**OpenAI (Recommended)**
```yaml
- uses: ratibor78/actions-ai-advisor@v1
  with:
    github-token: ${{ github.token }}
    api-key: ${{ secrets.OPENAI_API_KEY }}
    provider: openai
    model: gpt-4o-mini  # or gpt-4o
```
[Get API key](https://platform.openai.com/api-keys) • **Cost:** ~$0.0005/analysis • **Best for:** Fast, reliable, cheap

<details>
<summary><b>Other Providers (click to expand)</b></summary>

**Anthropic Claude**
```yaml
- uses: ratibor78/actions-ai-advisor@v1
  with:
    github-token: ${{ github.token }}
    api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    provider: anthropic
    model: claude-3-5-haiku-latest
```
[Get API key](https://console.anthropic.com) • **Cost:** ~$0.0016/analysis • **Best for:** Complex logs, large context

**OpenRouter**
```yaml
- uses: ratibor78/actions-ai-advisor@v1
  with:
    github-token: ${{ github.token }}
    api-key: ${{ secrets.OPENROUTER_API_KEY }}
    provider: openrouter
    model: openai/gpt-4o-mini
```
[Get API key](https://openrouter.ai/keys) • **Cost:** Varies by model • **Best for:** Multi-model routing

**Self-Hosted**
```yaml
- uses: ratibor78/actions-ai-advisor@v1
  with:
    github-token: ${{ github.token }}
    api-key: ${{ secrets.VLLM_API_KEY }}
    provider: selfhosted
    base-url: https://llm.internal.company.com/v1
    model: Qwen/Qwen2.5-Coder-32B-Instruct
```
**Requirements:** OpenAI-compatible API • 7B+ parameter models recommended

</details>

---

## Cost & Token Usage

**Typical costs:** ~$0.0003-0.0008 per analysis • **70% token reduction** via preprocessing (ANSI removal, timestamp stripping, metadata filtering)

| Model | Provider | Cost per Analysis |
|-------|----------|-------------------|
| **gpt-4o-mini** ⭐ | OpenAI | ~$0.0005 (recommended) |
| gpt-4o | OpenAI | ~$0.0080 |
| claude-3-5-haiku | Anthropic | ~$0.0016 |
| claude-3-5-sonnet | Anthropic | ~$0.0090 |
| gemini-flash-1.5 | OpenRouter | ~$0.0002 (cheapest) |

---

## Output Example

When a workflow fails, Actions AI Advisor writes analysis to the **Job Summary** tab:

```
# Actions AI Advisor

**Failed:** `build` → `Run tests`
**Exit Code:** `1` | **Duration:** 2m 34s

### Affected Files
- [`src/calculator.py:42`](link) ← Click to jump to line 42

---

## Root Cause
The `multiply()` function uses addition instead of multiplication.

## Recommended Actions
1. Change operator in `src/calculator.py:42`:
   - return a + b
   + return a * b

## Error Context
FAILED tests/test_calculator.py::test_multiply
  AssertionError: assert 8 == 20
    Expected: 20 (5 * 4)
    Got: 8 (5 + 4)

---

**Model:** `gpt-4o-mini` | **Tokens:** 3,247 in + 423 out | **Cost:** ~$0.0005
```

[See full output format details →](docs/llm-integration.md#5-rich-markdown-output-to-job-summary)

---

## Versioning

Actions AI Advisor follows semantic versioning with recommended usage patterns:

### Recommended: Major Version (`@v1`)
```yaml
- uses: ratibor78/actions-ai-advisor@v1
```
**Best for:** Most users who want automatic updates within v1.x.x
- ✅ Gets latest features and bug fixes automatically
- ✅ No breaking changes within major version
- ✅ Recommended for production workflows

### Pinned: Exact Version (`@v1.0.0`)
```yaml
- uses: ratibor78/actions-ai-advisor@v1.0.0
```
**Best for:** Enterprise/regulated environments requiring version pinning
- ✅ Guaranteed reproducibility
- ✅ No surprises from updates
- ⚠️ Manual version bumps required

---

## Troubleshooting

### Common Issues

**Issue:** "Failed to fetch logs from GitHub API"
- **Cause:** Insufficient permissions
- **Fix:** Ensure `permissions: actions: read` in workflow

**Issue:** "API key not found"
- **Cause:** Secret not configured
- **Fix:** Add secret in repository Settings → Secrets and variables → Actions

**Issue:** "Affected Files section is empty"
- **Cause:** No file paths detected in logs
- **Explanation:** This is normal for some error types (e.g., network timeouts, configuration errors)

**Issue:** "Cost showing as N/A"
- **Cause:** Model not in pricing table
- **Fix:** Self-hosted/unknown models don't have cost estimation

---

## Development

**Contributing to Actions AI Advisor?**

```bash
# Quick start
git clone https://github.com/ratibor78/actions-advisor.git
cd actions-advisor
pip install uv
uv sync
uv run pytest  # Run tests (all mocked, no API calls)
```

[See comprehensive development guide →](docs/development.md)

---

## Contributing

Contributions welcome! **Report bugs** • **Suggest features** • **Improve docs** • **Add tests** • **Submit PRs** • **Star the repo**

When reporting issues, include: workflow config, error logs (redacted), expected vs actual behavior, and LLM provider/model used.

---

## Security

**Design:** Read-only (`actions:read` only) • No data retention (memory only) • Secret-aware (GitHub auto-redacts) • API keys in Secrets • Open source

**Sent to LLM:** Preprocessed logs, error messages, job metadata
**Never sent:** GitHub tokens, API keys, secrets (GitHub replaces with `***` before we fetch)

**Recommendations:** Use separate CI/CD API keys • Review LLM provider policies • Consider self-hosted for sensitive code

---

## Roadmap

**v1.0.0 (Current)**
- ✅ Multi-language support (10+ languages) • Affected files with clickable links • Smart preprocessing (70% tokens) • Multi-provider (OpenAI, Anthropic, OpenRouter, self-hosted) • Cost transparency

**v1.1.0 (Next Release)**
- 🔄 PR comment mode • Analysis caching • Matrix job support • Custom prompts • More languages (Julia, Elixir, Haskell)

**Future**
- 💭 Web UI • Metrics dashboard • Slack/Discord integration • GitHub Enterprise support

---

## Author

**Oleksii Nizhegolenko**

- Email: ratibor78@gmail.com
- LinkedIn: [linkedin.com/in/nizhegolenko](https://www.linkedin.com/in/nizhegolenko/)
- GitHub: [@ratibor78](https://github.com/ratibor78)

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built with:
- [OpenAI](https://openai.com) — GPT models for intelligent analysis
- [Anthropic](https://anthropic.com) — Claude models for complex reasoning
- [OpenRouter](https://openrouter.ai) — Multi-model API gateway
- [GitHub Actions](https://github.com/features/actions) — CI/CD platform
- [tiktoken](https://github.com/openai/tiktoken) — Fast token counting
- [httpx](https://www.python-httpx.org/) — Modern async HTTP client
- [pydantic](https://docs.pydantic.dev/) — Data validation and settings

Special thanks to the open-source community for feedback and contributions!

---

<div align="center">

**[⬆ back to top](#-actions-ai-advisor)**

Made with ❤️ by [Oleksii Nizhegolenko](https://www.linkedin.com/in/nizhegolenko/)

[Report Bug](https://github.com/ratibor78/actions-advisor/issues) • [Request Feature](https://github.com/ratibor78/actions-advisor/issues) • [Discussions](https://github.com/ratibor78/actions-advisor/discussions)

</div>
