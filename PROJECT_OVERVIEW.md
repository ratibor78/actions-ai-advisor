# Actions AI Advisor - Project Overview

## What This Project Is

**Actions AI Advisor** is a GitHub Action that uses Large Language Models (LLMs) to automatically analyze failed GitHub Actions workflow runs and provide intelligent, actionable explanations directly in the Job Summary.

### The Problem It Solves

When a GitHub Actions workflow fails, developers often face:
- Hundreds or thousands of lines of logs to sift through
- Cryptic error messages buried in verbose output
- Time wasted identifying the actual root cause
- Repeated failures due to unclear fix instructions

### The Solution

Actions AI Advisor:
1. **Automatically detects** failed jobs in your workflow
2. **Fetches and preprocesses** the logs (removes noise, ANSI codes, timestamps)
3. **Sends to an LLM** (OpenAI, Anthropic, OpenRouter, or self-hosted)
4. **Generates analysis** with:
   - Root cause explanation
   - Suggested fixes
   - Relevant error snippets
5. **Displays results** in the GitHub Actions Job Summary (visible in the UI)

---

## Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                   │
│                    (workflow fails)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Actions AI Advisor (Docker Container)           │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Log Fetcher  │───▶│ Preprocessor │───▶│  LLM Client  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │         │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  Fetch from GitHub    Remove noise       Send to API       │
│  API (failed jobs)    Collapse repeats   (OpenAI, etc)     │
│                       Trim to 150 lines                     │
│                                                              │
│                       ┌──────────────┐                      │
│                       │  Formatter   │                      │
│                       └──────────────┘                      │
│                              │                               │
└──────────────────────────────┼───────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ GitHub Job Summary  │
                    │ (Markdown output)   │
                    └─────────────────────┘
```

### Tech Stack

- **Language:** Python 3.12+
- **Package Manager:** uv (modern, fast Python package manager)
- **HTTP Client:** httpx (async HTTP requests)
- **Config:** pydantic-settings (environment variable validation)
- **Token Counting:** tiktoken (accurate token estimation)
- **Testing:** pytest, pytest-asyncio, respx (HTTP mocking)
- **Type Checking:** mypy (strict mode)
- **Linting:** ruff (fast Python linter)
- **Containerization:** Docker (for GitHub Actions)

### Key Modules

1. **`config.py`** - Configuration loading from environment variables
2. **`log_fetcher.py`** - Fetches failed job logs via GitHub API
3. **`preprocessor.py`** - Cleans logs (removes ANSI, timestamps, collapses repeats)
4. **`tokens.py`** - Token counting and cost estimation
5. **`llm_client.py`** - Unified LLM client (supports 4 providers)
6. **`file_parser.py`** - Parses affected files from logs, creates GitHub links
7. **`formatter.py`** - Formats analysis as markdown for Job Summary
8. **`main.py`** - Orchestrates the entire pipeline

---

## Key Features

### 1. Multi-Provider LLM Support

Supports 4 different LLM providers with a unified interface:

- **OpenAI** (`gpt-4o-mini`, `gpt-4o`)
- **Anthropic** (`claude-3-5-haiku-latest`, `claude-sonnet-4-latest`)
- **OpenRouter** (any model via OpenRouter)
- **Self-hosted** (custom API endpoint)

All use OpenAI-compatible API format.

### 2. Intelligent Log Preprocessing

Reduces log size by ~70% while preserving critical information:

- ✅ Removes ANSI escape codes
- ✅ Removes timestamps
- ✅ Removes GitHub Actions metadata (`##[group]`, `::set-output`, etc.)
- ✅ Collapses repeated lines (e.g., "npm WARN..." × 50 → single line + count)
- ✅ Extracts failed step sections
- ✅ Trims to last 150 lines per step
- ✅ Removes excessive empty lines

### 3. Token Counting & Cost Estimation

- Accurate token counting using `tiktoken`
- Displays input/output token counts in Job Summary
- Shows estimated cost for OpenAI and Anthropic models
- Hardcoded pricing table (updated as of Jan 2025)

### 4. Affected Files Detection

Parses log output to identify files mentioned in errors and creates direct GitHub links to them (with line numbers when available).

### 5. Rich Job Summary Output

Generates markdown-formatted analysis with:
- Failure header (job name, step name, exit code, duration)
- Affected files section with clickable GitHub links
- LLM analysis (root cause, suggested fixes)
- Analysis details (model used, tokens, cost)
- Footer with branding

---

## Development History

### Phase 1: Initial Planning (from PLAN.md)
- Designed architecture based on user requirements
- Chose Docker-based action (not Node.js)
- Decided on Job Summary output (not PR comments)
- Selected unified LLM client approach
- Chose Python 3.12+ with uv package manager

### Phase 2: Core Implementation
Implemented all core modules:
- ✅ Configuration system with pydantic-settings
- ✅ GitHub API log fetcher (async with httpx)
- ✅ Log preprocessor (70%+ token reduction)
- ✅ Token counter with cost estimation
- ✅ Unified LLM client (4 providers)
- ✅ File parser with GitHub link generation
- ✅ Markdown formatter
- ✅ Main orchestration pipeline

### Phase 3: Testing Infrastructure
- ✅ Comprehensive unit tests (68 tests total)
- ✅ Test fixtures with sample logs
- ✅ HTTP mocking with respx
- ✅ Async test support with pytest-asyncio
- ✅ Type checking with mypy (strict mode)
- ✅ Linting with ruff

### Phase 4: Docker & GitHub Action
- ✅ Dockerfile (Python 3.12-slim, uv installation)
- ✅ action.yml (input definitions, branding)
- ✅ CI workflow (lint, test, type-check)
- ✅ Release workflow (Docker image publishing)

### Phase 5: Project Rename (Just Completed)
- ✅ Renamed repository: `actions-advisor` → `actions-ai-advisor`
- ✅ Renamed Python package: `actions-advisor` → `actions-ai-advisor`
- ✅ Renamed Python module: `actions_advisor` → `actions_ai_advisor`
- ✅ Updated 23+ import statements across 14 files
- ✅ Updated Docker image name
- ✅ Updated all documentation
- ✅ All 68 tests passing
- ✅ Type checking passing

---

## Current State

### Test Coverage
```
68 tests collected and passed
- test_config.py: 5 tests
- test_file_parser.py: 10 tests
- test_formatter.py: 9 tests
- test_llm_client.py: 9 tests
- test_log_fetcher.py: 3 tests
- test_preprocessor.py: 8 tests
- test_tokens.py: 3 tests
- test_integration.py: 21 tests
```

### Type Safety
```
mypy --strict: Success (no issues in 9 source files)
```

### Code Quality
```
ruff: 4 minor import ordering issues (auto-fixable)
```

### Version
- **Current:** v0.1.0-beta
- **Planned next:** v0.2.0 (after rename is committed)

---

## File Structure

```
actions-ai-advisor/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Lint, test, type-check
│       └── release.yml         # Build & publish Docker image
├── src/
│   └── actions_ai_advisor/
│       ├── __init__.py
│       ├── main.py             # Entry point & orchestration
│       ├── config.py           # Environment config loading
│       ├── log_fetcher.py      # Fetch logs from GitHub API
│       ├── preprocessor.py     # Clean & reduce log size
│       ├── tokens.py           # Token counting & cost estimation
│       ├── llm_client.py       # Unified LLM client (4 providers)
│       ├── file_parser.py      # Parse affected files from logs
│       └── formatter.py        # Format analysis as markdown
├── tests/
│   ├── conftest.py             # pytest configuration
│   ├── fixtures/
│   │   └── sample_logs/        # Test log samples
│   ├── test_config.py
│   ├── test_file_parser.py
│   ├── test_formatter.py
│   ├── test_llm_client.py
│   ├── test_log_fetcher.py
│   ├── test_preprocessor.py
│   ├── test_tokens.py
│   └── test_integration.py
├── pyproject.toml              # Package config, dependencies
├── uv.lock                     # Locked dependencies
├── Dockerfile                  # Docker image definition
├── action.yml                  # GitHub Action metadata
├── README.md                   # User documentation
├── LICENSE                     # MIT License
├── PLAN.md                     # Original implementation plan
├── RENAME_SUMMARY.md           # Rename process documentation
└── PROJECT_OVERVIEW.md         # This file
```

---

## Usage Example

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: npm test

      # If tests fail, analyze with AI
      - name: Analyze failure
        if: failure()
        uses: ratibor78/actions-ai-advisor@v0.2.0
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          api-key: ${{ secrets.OPENAI_API_KEY }}
          provider: 'openai'
          model: 'gpt-4o-mini'
```

When the test step fails, Actions AI Advisor will:
1. Fetch the failure logs
2. Preprocess them (remove noise)
3. Send to OpenAI GPT-4o-mini
4. Display analysis in the Job Summary tab

---

## Typical Cost

With `gpt-4o-mini` (default):
- Input: ~$0.15 per 1M tokens
- Output: ~$0.60 per 1M tokens
- **Average analysis: ~$0.0005-0.002 per failure** (very cheap!)

With `claude-3-5-haiku-latest`:
- Input: ~$0.80 per 1M tokens
- Output: ~$4.00 per 1M tokens
- **Average analysis: ~$0.003-0.008 per failure** (still cheap!)

---

## Design Decisions

### Why Docker-based Action?
- No Node.js overhead
- Full Python ecosystem available
- Easier to manage dependencies
- Better for ML/AI libraries

### Why Job Summary instead of PR Comments?
- Works for all events (push, PR, schedule, etc.)
- No extra permissions needed
- Cleaner UX (one place to look)
- PR comments can be added later as optional feature

### Why Unified LLM Client?
- Single codebase for 4 providers
- OpenAI-compatible API is becoming standard
- Easy to add new providers
- Minimal provider-specific code

### Why Hardcoded Preprocessing Rules?
- Simplicity (no complex config)
- Proven effective (70%+ reduction)
- Fast to execute
- Easy to understand and debug

### Why uv instead of pip/poetry?
- 10-100x faster than pip
- Built-in lockfile support
- Modern dependency resolution
- Growing adoption in Python community

---

## Next Steps (Planned Features)

### v0.3.0 - Enhanced Analysis
- [ ] Add file context fetching (show relevant code in prompt)
- [ ] Add git diff analysis (show what changed)
- [ ] Add historical failure tracking (is this recurring?)

### v0.4.0 - PR Integration
- [ ] Optional PR comment mode
- [ ] Inline code suggestions
- [ ] Link to related issues/PRs

### v0.5.0 - Advanced Features
- [ ] Custom prompt templates (user-configurable)
- [ ] Multi-job aggregation (analyze all failures together)
- [ ] Retry suggestions (auto-detect flaky tests)

---

## Contributing

This project follows:
- **Type safety:** mypy strict mode
- **Code quality:** ruff linting
- **Test coverage:** >80% target
- **Testing:** pytest with async support
- **Conventional commits:** For changelog generation

---

## License

MIT License - See LICENSE file

---

## Links

- **Repository:** https://github.com/ratibor78/actions-ai-advisor
- **Docker Image:** ghcr.io/ratibor78/actions-ai-advisor
- **Issues:** https://github.com/ratibor78/actions-ai-advisor/issues
- **Marketplace:** (not yet published)

---

## Status

**Current Status:** ✅ Fully functional, tested, ready for v0.2.0 release

**Last Updated:** 2025-12-13 (after project rename)
