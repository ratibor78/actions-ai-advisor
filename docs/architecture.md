# Architecture

This document provides a comprehensive overview of Actions AI Advisor's system architecture, component design, and technical implementation.

---

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Design Principles](#design-principles)

---

## System Overview

Actions AI Advisor is a **Docker-based GitHub Action** that automatically analyzes failed CI/CD workflows using Large Language Models (LLMs). When a workflow fails, it:

1. Fetches failure logs from GitHub Actions API
2. Preprocesses logs to reduce noise and cost (~70% token reduction)
3. Extracts file paths from error messages (10+ languages supported)
4. Sends preprocessed context to an LLM for analysis
5. Generates a formatted markdown report in the GitHub Job Summary

**Key Characteristics:**
- **Zero-config** — Works out of the box with minimal inputs
- **Provider-agnostic** — Supports OpenAI, Anthropic, OpenRouter, self-hosted
- **Cost-efficient** — ~$0.0003-0.0008 per analysis via smart preprocessing
- **Language-aware** — Context-aware parsing for 6 languages, regex for 4 more
- **Read-only** — No write access to repository, only `actions:read` permission

---

## Component Architecture

The system is organized into 8 core modules:

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Actions Workflow                     │
│                     (triggers on: if: failure())                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│                  (orchestration & entry point)                   │
└──┬───────┬────────┬────────┬─────────┬─────────┬────────────┬───┘
   │       │        │        │         │         │            │
   │       │        │        │         │         │            │
   ▼       ▼        ▼        ▼         ▼         ▼            ▼
┌────┐ ┌─────┐ ┌──────┐ ┌─────┐ ┌─────────┐ ┌────────┐ ┌─────────┐
│cfg │ │logs │ │prep  │ │parse│ │tokens   │ │llm     │ │formatter│
│.py │ │.py  │ │.py   │ │.py  │ │.py      │ │_client │ │.py      │
└────┘ └─────┘ └──────┘ └─────┘ └─────────┘ └────────┘ └─────────┘
  ↓       ↓        ↓        ↓         ↓          ↓           ↓
Config  Fetch   Clean   Extract   Count     Analyze    Format &
Load    Logs    Logs    Files     Tokens    w/ LLM     Write
```

### Module Descriptions

#### 1. **config.py** — Configuration Management
- Loads inputs from environment variables (`INPUT_*` prefix)
- Validates required fields (GitHub token, API key)
- Parses repository owner/name from `GITHUB_REPOSITORY`
- Uses `pydantic-settings` for type-safe configuration

**Key Classes:**
- `Config` — Main configuration dataclass with validation

#### 2. **log_fetcher.py** — GitHub API Integration
- Fetches failed job metadata from GitHub Actions API
- Downloads raw logs (follows HTTP 302 redirects)
- Filters jobs by conclusion status (`failure`, `cancelled`)
- **Handles pagination** for workflows with 100+ jobs (matrix builds)
- Rate-limited and authenticated via GitHub token

**Key Classes:**
- `JobLog` — Dataclass holding job metadata and raw logs
- `LogFetcher` — Async client for GitHub API

**API Endpoints:**
- `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs?page={N}&per_page=100` — List jobs (paginated)
- `GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs` — Download logs

**Pagination:**
- Fetches 100 jobs per page (GitHub's max)
- Iterates until `total_count` reached
- Prevents missing failures in large matrix builds (>30 jobs)

#### 3. **preprocessor.py** — Log Cleaning & Optimization
- Removes ANSI escape codes (color formatting)
- Strips ISO 8601 timestamps from each line
- Filters GitHub Actions metadata (`##[group]`, `::set-output`)
- Collapses repeated warnings (e.g., "npm WARN" × 50 → single line)
- Extracts failed step sections with context
- Trims to last 150 lines per failed step

**Key Functions:**
- `preprocess_logs(raw_logs: str) -> str` — Main entry point
- `_remove_ansi_codes()` — Regex-based ANSI removal
- `_collapse_repeated_lines()` — Deduplication logic
- `_extract_failed_sections()` — Failed step isolation

**Performance:**
- Typical reduction: 30,000 chars → 10,000 chars (~70% reduction)
- Cost impact: $0.0015 → $0.0005 per analysis

#### 4. **file_parser.py** — File Path Extraction
- Parses error logs for file paths (10+ language patterns)
- **Cross-platform support** — Handles both Unix (`/path/file`) and Windows (`C:\path\file`) paths
- Resolves relative paths using working directory context
- Filters out library/system files (JDK, site-packages)
- Generates clickable GitHub links with line numbers

**Key Classes:**
- `AffectedFile` — Dataclass with file path and line number
- `PATH_PATTERN` — Cross-platform regex component for both `/` and `\` paths
- Language-specific regex patterns (Python, JS/TS, Go, Rust, Java, .NET, PHP, Ruby, C/C++, Docker)

**Smart Features:**
- **Cross-platform paths** — Normalizes Windows backslashes to forward slashes, handles drive letters
- **Context-aware resolution** — Uses Cargo workspace, Go module paths, Windows GitHub Actions workspace
- **Library filtering** — Excludes `java.lang.*`, `site-packages/*`
- **Hybrid linking** — Direct line links or search fallback

#### 5. **tokens.py** — Token Counting & Cost Estimation
- Counts tokens using `tiktoken` (OpenAI's tokenizer)
- Estimates cost based on hardcoded pricing table
- Supports multiple models (gpt-4o-mini, claude-3-5-haiku, etc.)

**Key Classes:**
- `TokenCounter` — Token counting and cost calculation

**Pricing Table:**
```python
PRICING = {
    "openai": {
        "gpt-4o-mini": (0.15, 0.60),  # per 1M tokens (input, output)
        "gpt-4o": (2.50, 10.00),
    },
    "anthropic": {
        "claude-3-5-haiku-latest": (0.80, 4.00),
        "claude-sonnet-4-latest": (3.00, 15.00),
    }
}
```

#### 6. **llm_client.py** — LLM Integration
- Unified client for multiple LLM providers (OpenAI-compatible API)
- Sends preprocessed logs with structured prompt
- Extracts analysis and token usage from response
- Handles provider-specific headers (Anthropic, OpenRouter)

**Key Classes:**
- `LLMClient` — Main client with `analyze()` method
- `AnalysisResult` — Response dataclass (analysis text + tokens)

**Supported Providers:**
- **OpenAI** — `https://api.openai.com/v1`
- **Anthropic** — `https://api.anthropic.com/v1` (custom headers)
- **OpenRouter** — `https://openrouter.ai/api/v1`
- **Self-hosted** — Custom base URL (vLLM, Ollama, etc.)

**Request Format:**
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "[CI/CD debugging prompt]"},
    {"role": "user", "content": "[preprocessed logs + metadata]"}
  ],
  "temperature": 0.3,
  "max_tokens": 1500
}
```

#### 7. **formatter.py** — Output Generation
- Wraps LLM analysis with metadata (job name, exit code, duration)
- Formats affected files as clickable GitHub links
- Adds token usage and cost transparency
- Writes to `$GITHUB_STEP_SUMMARY` (Job Summary tab)

**Output Structure:**
```markdown
# Actions AI Advisor

**Failed:** `job-name` → `step-name`
**Exit Code:** `1` | **Duration:** 2m 34s

### Affected Files
- [src/file.py:42](GitHub link)

---

[LLM ANALYSIS: Root Cause, Recommended Actions, Error Context]

---

### Analysis Details
**Model:** `gpt-4o-mini` | **Tokens:** 3,247 in + 423 out | **Cost:** ~$0.0005
```

#### 8. **main.py** — Orchestration
- Entry point for the GitHub Action
- Coordinates all modules in sequence
- Error handling and logging
- Exits with appropriate status codes

**Flow:**
1. Load configuration → `Config`
2. Fetch failed job logs → `LogFetcher`
3. Preprocess logs → `preprocessor`
4. Extract file paths → `file_parser`
5. Count tokens → `TokenCounter`
6. Analyze with LLM → `LLMClient`
7. Format output → `formatter`
8. Write to Job Summary → `write_job_summary()`

---

## Data Flow

### High-Level Pipeline

```
GitHub Actions Workflow (failed)
    │
    ├─→ Trigger: if: failure()
    │
    ▼
[1] Fetch Logs (log_fetcher.py)
    │
    ├─→ GitHub API: GET /actions/runs/{id}/jobs
    ├─→ Filter: conclusion == "failure"
    ├─→ GitHub API: GET /actions/jobs/{id}/logs
    │
    ▼
[2] Preprocess (preprocessor.py)
    │
    ├─→ Remove ANSI codes, timestamps, metadata
    ├─→ Collapse repeated lines
    ├─→ Extract failed step sections
    ├─→ Result: 70% token reduction
    │
    ▼
[3] Extract Files (file_parser.py)
    │
    ├─→ Regex patterns for 10+ languages
    ├─→ Context-aware path resolution
    ├─→ Filter library files
    ├─→ Generate GitHub links
    │
    ▼
[4] Count Tokens (tokens.py)
    │
    ├─→ tiktoken encoding
    ├─→ Estimate cost
    │
    ▼
[5] Analyze (llm_client.py)
    │
    ├─→ Build request: system prompt + user logs
    ├─→ POST /chat/completions (OpenAI-compatible)
    ├─→ Parse response: analysis + token usage
    │
    ▼
[6] Format Output (formatter.py)
    │
    ├─→ Wrap with metadata (job name, exit code, duration)
    ├─→ Add affected files section
    ├─→ Add analysis details (tokens, cost)
    │
    ▼
[7] Write Job Summary
    │
    └─→ $GITHUB_STEP_SUMMARY (visible in Actions UI)
```

### Data Transformations

| Stage | Input | Output | Size Change |
|-------|-------|--------|-------------|
| **Fetch** | GitHub API | Raw logs (30KB) | - |
| **Preprocess** | Raw logs (30KB) | Clean logs (10KB) | -70% |
| **Extract Files** | Clean logs | List of file paths | N/A |
| **Count Tokens** | Clean logs | Token count (3,247) | N/A |
| **LLM Analysis** | Clean logs | Analysis text (423 tokens) | N/A |
| **Format** | Analysis + metadata | Final markdown | +500 bytes |

---

## Technology Stack

### Core Technologies

- **Language:** Python 3.12+
- **Package Manager:** [uv](https://github.com/astral-sh/uv) — Fast, reliable Python package installer
- **Runtime:** Docker (`python:3.12-slim`)
- **HTTP Client:** [httpx](https://www.python-httpx.org/) — Async HTTP client
- **Configuration:** [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — Type-safe env var parsing
- **Token Counting:** [tiktoken](https://github.com/openai/tiktoken) — OpenAI's tokenizer

### Why These Choices?

**Python 3.12+**
- Mature ecosystem for LLM integration
- Excellent async support (`httpx`, `asyncio`)
- Strong typing with type hints
- Fast development iteration

**uv Package Manager**
- 10-100x faster than pip
- Reliable lock files (`uv.lock`)
- Better dependency resolution
- Single binary, no separate virtualenv management

**Docker Action (not Node.js Composite)**
- More control over environment (Python version, system deps)
- Consistent across all runners (Linux, macOS, Windows via containers)
- Easier to test locally
- No Node.js version compatibility issues

**httpx (not official SDKs)**
- Single client works for all providers (OpenAI-compatible API)
- Smaller dependency footprint
- Full control over request/response handling
- No SDK version conflicts

---

## Design Principles

### 1. **Simplicity Over Features**
- Minimal configuration (just 2 required inputs: token + API key)
- No custom prompts in v1 (reduces complexity)
- Single unified LLM client (not per-provider SDKs)
- Hardcoded pricing table (vs API calls for real-time pricing)

### 2. **Cost Transparency**
- Always show token counts (input + output)
- Display estimated cost (when available)
- Preprocessing reduces costs by 70%
- Users know exactly what they're paying

### 3. **Read-Only Security**
- Only requires `actions: read` permission
- Never writes to repository
- No secret exposure (GitHub auto-redacts in logs)
- API keys in GitHub Secrets (never logged)

### 4. **Developer Experience**
- Zero-config setup (works with defaults)
- Clickable file links (jump to exact error line)
- Fast execution (10-30 seconds end-to-end)
- Clear, actionable recommendations

### 5. **Maintainability**
- Clean module separation (8 focused modules)
- Comprehensive type hints (mypy strict mode)
- Automated testing (pytest with >80% coverage)
- Linting (ruff) and formatting enforcement

---

## Performance Characteristics

### Execution Time
- **Typical:** 10-30 seconds end-to-end
- **Breakdown:**
  - Fetch logs: 2-5s
  - Preprocess: <1s
  - Extract files: <1s
  - LLM analysis: 5-20s (depends on model/provider)
  - Format + write: <1s

### Cost
- **gpt-4o-mini:** ~$0.0005 per analysis (recommended)
- **claude-3-5-haiku:** ~$0.0016 per analysis
- **gpt-4o:** ~$0.0080 per analysis (premium)

### Token Usage
- **Input:** 2,000-4,000 tokens (after 70% reduction)
- **Output:** 300-600 tokens (analysis text)
- **Total:** ~3,000 tokens per analysis (typical)

---

## Extension Points

The architecture supports future extensions:

### 1. **Additional Providers**
- Add endpoint to `PROVIDER_ENDPOINTS` dict
- Add header logic to `_build_headers()` method
- No other changes needed (OpenAI-compatible API)

### 2. **Custom Prompts**
- Expose `SYSTEM_PROMPT` as configurable input
- Or load from `.github/advisor-prompts/system.txt`
- Planned for v1.1.0

### 3. **PR Comment Mode**
- Add GitHub API client for creating comments
- Modify `formatter.py` to generate PR-friendly format
- Add permission check for `pull-requests: write`
- Planned for v1.1.0

### 4. **Analysis Caching**
- Hash preprocessed logs
- Store analysis in GitHub Actions cache
- Skip LLM call if same failure seen before
- Planned for v1.1.0

### 5. **Matrix Job Support**
- Detect matrix strategy from workflow config
- Group failures by matrix combination
- Single analysis covering all matrix failures
- Planned for v1.1.0

---

## Security Considerations

### Permissions
- **Required:** `actions: read` (fetch logs)
- **Never requires:** `contents: write`, `pull-requests: write`

### Secret Handling
- API keys stored in GitHub Secrets
- GitHub automatically redacts secrets in logs (replaced with `***`)
- We fetch logs AFTER GitHub's redaction
- No secret detection logic needed (GitHub handles it)

### Network Access
- Outbound HTTPS to:
  - `api.github.com` (log fetching)
  - LLM provider APIs (analysis)
- No inbound connections
- No third-party analytics or telemetry

### Dependencies
- Minimal dependency surface (5 production dependencies)
- All from trusted sources (PyPI with verification)
- Lockfile ensures reproducible builds (`uv.lock`)

---

## Observability

### Logging
- Action logs visible in GitHub Actions UI
- Error messages include context (job name, step name)
- Token counts logged for transparency
- No sensitive data logged (secrets auto-redacted)

### Debugging
- Set `ACTIONS_STEP_DEBUG=true` for verbose logs
- View full request/response in action logs
- Test locally with real GitHub tokens and run IDs

### Monitoring
- GitHub Actions provides:
  - Execution time per run
  - Success/failure rate
  - Workflow insights
- No custom metrics (uses GitHub's built-in observability)

---

## Comparison with Alternatives

| Feature | Actions AI Advisor | Manual Debugging | GitHub Copilot | Commercial CI Tools |
|---------|-------------------|------------------|----------------|---------------------|
| **Setup** | 5 lines of YAML | N/A | IDE plugin | Complex integration |
| **Cost** | ~$0.0005/analysis | Free (time cost) | $10/mo per user | $$$$ |
| **Speed** | 10-30s | Minutes to hours | Instant (but manual) | Varies |
| **Accuracy** | Good (LLM-based) | Depends on developer | Good | Excellent |
| **Multi-language** | 10+ languages | Universal | Universal | Limited |
| **File Links** | Yes (clickable) | Manual search | N/A | Some tools |
| **Privacy** | Logs sent to LLM | Fully private | Code sent to GitHub | Varies |

---

## Future Architecture Evolution

### Planned for v1.1.0
- **PR Comment Mode** — Post analysis as PR comments
- **Custom Prompts** — User-configurable system prompts
- **Analysis Caching** — Avoid re-analyzing identical failures
- **Matrix Job Support** — Single analysis for matrix failures

### Planned for v1.2.0
- **Web UI** — Standalone dashboard for viewing past analyses
- **Metrics Dashboard** — Track failure patterns over time
- **Slack/Discord Integration** — Post analyses to chat
- **GitHub Enterprise Support** — Private instance compatibility

### Research Ideas
- **Local LLM Support** — Run Ollama/llama.cpp locally (no API costs)
- **Multi-agent Analysis** — Specialized agents per language
- **Failure Prediction** — ML model to predict likely failures
- **Auto-fix PRs** — Generate fix PRs automatically (with approval)

---

## Conclusion

Actions AI Advisor is designed as a **simple, cost-efficient, and maintainable** tool for automated CI/CD debugging. The architecture prioritizes:

- **Developer experience** (zero-config, clickable links, fast)
- **Cost efficiency** (70% token reduction, cheap models)
- **Security** (read-only, no secret exposure)
- **Extensibility** (clean modules, OpenAI-compatible API)

For implementation details, see:
- [Design Decisions](design-decisions.md) — Why we chose specific approaches
- [LLM Integration](llm-integration.md) — Prompt engineering and provider details
- [Development Guide](development.md) — Contributing and testing
