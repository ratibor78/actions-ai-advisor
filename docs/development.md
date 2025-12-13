# Development Guide

This guide covers how to contribute to Actions AI Advisor, including setup, testing, and development workflows.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Contributing](#contributing)
- [Release Process](#release-process)

---

## Getting Started

### Prerequisites

- **Python 3.12+** — Required for development
- **uv** — Fast Python package manager ([install guide](https://github.com/astral-sh/uv))
- **Docker** — For building and testing the action locally
- **Git** — Version control

### Installation

**Using uv (recommended):**
```bash
# Clone repository
git clone https://github.com/ratibor78/actions-ai-advisor.git
cd actions-ai-advisor

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Verify installation
uv run pytest --version
uv run ruff --version
uv run mypy --version
```

**Using pip:**
```bash
# Clone repository
git clone https://github.com/ratibor78/actions-ai-advisor.git
cd actions-ai-advisor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e .[dev]

# Verify installation
pytest --version
ruff --version
mypy --version
```

**Note:** All development dependencies (including `respx` for HTTP mocking) are now properly included in `[project.optional-dependencies.dev]`, making the project compatible with both `uv` and standard `pip` workflows.

---

## Development Workflow

### Project Structure

```
actions-ai-advisor/
├── .github/workflows/     # CI/CD pipelines
├── docs/                  # Documentation (you are here!)
├── src/actions_ai_advisor/   # Source code
├── tests/                 # Test suite
├── action.yml             # GitHub Action definition
├── Dockerfile             # Docker container
├── pyproject.toml         # Project configuration
└── uv.lock                # Locked dependencies
```

### Running Tests

**All tests:**
```bash
uv run pytest
```

**With coverage:**
```bash
uv run pytest --cov=src/actions_ai_advisor --cov-report=term-missing
```

**Specific test file:**
```bash
uv run pytest tests/test_file_parser.py -v
```

**Specific test:**
```bash
uv run pytest tests/test_file_parser.py::test_parse_python_traceback -v
```

**Watch mode (requires pytest-watch):**
```bash
uv run ptw tests/
```

### Linting and Type Checking

**Run ruff (linter + formatter):**
```bash
# Check for issues
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/
```

**Run mypy (type checker):**
```bash
uv run mypy src/
```

**Run all checks (pre-commit):**
```bash
# Recommended before committing
uv run ruff check src/ tests/ && uv run mypy src/ && uv run pytest
```

### Local Development with Real Workflows

To test the action with actual GitHub workflows:

#### 1. Find a Failed Run

Go to your repository's Actions tab and note a failed run ID:
```
https://github.com/owner/repo/actions/runs/12345678
                                                 ↑ this number
```

#### 2. Set Environment Variables

```bash
export GITHUB_TOKEN="ghp_..."              # Your GitHub PAT
export INPUT_API_KEY="sk-..."              # Your LLM API key
export INPUT_PROVIDER="openai"             # or anthropic, openrouter
export INPUT_MODEL="gpt-4o-mini"
export GITHUB_REPOSITORY="owner/repo"     # Your repository
export GITHUB_RUN_ID="12345678"            # Real failed run ID
export GITHUB_SHA="abc123def456"           # Real commit SHA
export GITHUB_STEP_SUMMARY="output.md"    # Local file for summary
```

#### 3. Run Locally

```bash
uv run actions-ai-advisor
```

**⚠️ Warning:** This makes **real API calls** and costs money (~$0.0003-0.0008 per run).

#### 4. View Output

```bash
cat output.md
```

---

## Testing

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_config.py           # Config loading
├── test_file_parser.py      # File path extraction (23 tests)
├── test_formatter.py        # Markdown formatting
├── test_llm_client.py       # LLM integration
├── test_log_fetcher.py      # GitHub API
├── test_preprocessor.py     # Log cleaning
└── test_tokens.py           # Token counting
```

### Writing Tests

**Example test:**

```python
import pytest
from actions_ai_advisor.file_parser import extract_affected_files, AffectedFile

def test_python_traceback_extraction():
    """Test extracting file paths from Python tracebacks."""
    logs = '''
    Traceback (most recent call last):
      File "src/main.py", line 42, in main
        result = calculate(10, 0)
      File "src/calc.py", line 15, in calculate
        return a / b
    ZeroDivisionError: division by zero
    '''

    files = extract_affected_files(logs, repo_owner="", repo_name="", commit_sha="")

    assert len(files) == 2
    assert any(f.file_path == "src/main.py" and f.line_number == 42 for f in files)
    assert any(f.file_path == "src/calc.py" and f.line_number == 15 for f in files)
```

**Testing async functions:**

```python
import pytest
from actions_ai_advisor.llm_client import LLMClient

@pytest.mark.asyncio
async def test_llm_client_analyze(mock_llm_response):
    """Test LLM analysis with mocked response."""
    client = LLMClient(provider="openai", api_key="test-key", model="gpt-4o-mini")

    # Mock HTTP response (use respx or httpx_mock)
    # ... setup mock ...

    result = await client.analyze(job_log, preprocessed_logs)

    assert result.analysis.startswith("## Root Cause")
    assert result.input_tokens > 0
    assert result.output_tokens > 0
```

### Testing with Docker

```bash
# Build local image
docker build -t actions-ai-advisor:test .

# Run with environment variables
docker run --rm \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  -e INPUT_API_KEY="$INPUT_API_KEY" \
  -e INPUT_PROVIDER="openai" \
  -e INPUT_MODEL="gpt-4o-mini" \
  -e GITHUB_REPOSITORY="owner/repo" \
  -e GITHUB_RUN_ID="12345678" \
  -e GITHUB_SHA="abc123" \
  actions-ai-advisor:test
```

### Coverage Requirements

- **Target:** >80% coverage
- **Current:** ~90%+ coverage

View coverage report:
```bash
uv run pytest --cov=src/actions_advisor --cov-report=html
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

---

## Code Quality

### Standards

- **Line length:** 100 characters
- **Docstrings:** Required for all public functions
- **Type hints:** Required for all functions (strict mypy)
- **Tests:** Required for all new features

### Ruff Configuration

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
```

**Rules:**
- `E` — PEP 8 errors
- `F` — Pyflakes (undefined names, unused imports)
- `I` — isort (import sorting)
- `N` — PEP 8 naming conventions
- `W` — PEP 8 warnings

### Mypy Configuration

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Strict mode enabled** — All functions must be fully typed.

### Pre-Commit Checklist

Before committing:
- [ ] All tests pass (`uv run pytest`)
- [ ] Linting clean (`uv run ruff check .`)
- [ ] Type checking clean (`uv run mypy src/`)
- [ ] Code formatted (`uv run ruff format .`)
- [ ] New tests added for new features
- [ ] Documentation updated if needed

---

## Contributing

### Contribution Process

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Add tests for new functionality**
5. **Run pre-commit checks:**
   ```bash
   uv run ruff check --fix src/ tests/
   uv run mypy src/
   uv run pytest --cov
   ```
6. **Commit with clear message:**
   ```bash
   git commit -m "Add support for Elixir error detection"
   ```
7. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Create pull request**

### Commit Message Guidelines

**Format:**
```
<type>: <short description>

<optional longer description>

<optional footer>
```

**Types:**
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `test:` — Test additions/changes
- `refactor:` — Code refactoring
- `chore:` — Maintenance tasks

**Examples:**
```
feat: Add Julia language support for error detection

fix: Correct path normalization for Windows paths

docs: Update language-support.md with Elixir patterns

test: Add coverage for Rust Cargo workspace detection
```

### Adding Language Support

See [Language Support Documentation](language-support.md#adding-new-languages) for detailed instructions.

**Quick steps:**
1. Add regex pattern to `src/actions_ai_advisor/file_parser.py`
2. Add to `LANGUAGE_PATTERNS` list
3. Create test fixture in `tests/fixtures/sample_logs/`
4. Add test case to `tests/test_file_parser.py`
5. Update documentation

### Code Review Process

Pull requests are reviewed for:
- **Correctness** — Does it work as intended?
- **Tests** — Are there comprehensive tests?
- **Code quality** — Does it follow project standards?
- **Documentation** — Is it documented?
- **Design** — Does it fit the architecture?

---

## Release Process

### Version Management

The project uses **semantic versioning** (semver):
- **v1.0.0** — Major version (breaking changes)
- **v1.1.0** — Minor version (new features, backwards compatible)
- **v1.0.1** — Patch version (bug fixes)

### Creating a Release

#### 1. Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "1.0.0"
```

#### 2. Run Pre-Release Checks

```bash
# All tests must pass
uv run pytest

# Linting must be clean
uv run ruff check .

# Type checking must pass
uv run mypy src/

# Docker must build
docker build -t actions-ai-advisor:v1.0.0 .

# Test with real workflow
export GITHUB_TOKEN="..." && export INPUT_API_KEY="..." && ...
uv run actions-ai-advisor
```

#### 3. Commit and Tag

```bash
# Commit version bump
git add pyproject.toml
git commit -m "Bump version to v1.0.0"
git push origin main

# Create tag
git tag v1.0.0
git push origin v1.0.0
```

#### 4. Release Workflow

Pushing the tag triggers `.github/workflows/release.yml`:
- Builds Docker image
- Pushes to GitHub Container Registry (`ghcr.io/ratibor78/actions-ai-advisor:v1.0.0`)
- Updates `latest` tag
- Creates GitHub Release with auto-generated notes

#### 5. Verify Release

1. Check workflow succeeded: https://github.com/ratibor78/actions-ai-advisor/actions
2. Verify Docker image: `docker pull ghcr.io/ratibor78/actions-ai-advisor:v1.0.0`
3. Check GitHub Releases: https://github.com/ratibor78/actions-ai-advisor/releases

### Updating an Existing Tag (Not Recommended)

**⚠️ Only do this for beta versions, never for stable releases:**

```bash
# Delete local tag
git tag -d v0.1.0-beta

# Delete remote tag
git push origin --delete v0.1.0-beta

# Create new tag
git tag v0.1.0-beta

# Push new tag
git push origin v0.1.0-beta
```

---

## Debugging

### Common Issues

**Issue: Tests fail with `ModuleNotFoundError`**
```bash
# Solution: Reinstall dependencies
uv sync --refresh
```

**Issue: Docker build fails**
```bash
# Solution: Check Dockerfile syntax and dependencies
docker build --no-cache -t actions-advisor:test .
```

**Issue: LLM API returns 401 Unauthorized**
```bash
# Solution: Check API key is valid
echo $INPUT_API_KEY  # Should not be empty
```

**Issue: File path extraction not working**
```bash
# Solution: Add debug logging
# In file_parser.py, add:
print(f"Testing pattern: {pattern.pattern}")
print(f"Matches: {pattern.findall(logs)}")
```

### Logging

**Enable verbose output:**
```bash
export ACTIONS_STEP_DEBUG=true
uv run actions-ai-advisor
```

**View GitHub Actions logs:**
1. Go to workflow run
2. Click on failed job
3. Expand "Actions AI Advisor" step
4. View full output

---

## Tools and Libraries

### Core Dependencies

| Library | Purpose | Documentation |
|---------|---------|---------------|
| **httpx** | Async HTTP client | https://www.python-httpx.org/ |
| **pydantic** | Data validation | https://docs.pydantic.dev/ |
| **tiktoken** | Token counting | https://github.com/openai/tiktoken |

### Development Dependencies

| Library | Purpose | Documentation |
|---------|---------|---------------|
| **pytest** | Testing framework | https://docs.pytest.org/ |
| **pytest-asyncio** | Async test support | https://pytest-asyncio.readthedocs.io/ |
| **pytest-cov** | Coverage reporting | https://pytest-cov.readthedocs.io/ |
| **respx** | HTTP mocking | https://lundberg.github.io/respx/ |
| **ruff** | Linter + formatter | https://docs.astral.sh/ruff/ |
| **mypy** | Type checking | https://mypy.readthedocs.io/ |

---

## FAQ

**Q: How do I add a new LLM provider?**
A: Add the endpoint to `PROVIDER_ENDPOINTS` in `llm_client.py` and handle provider-specific headers in `_build_headers()`. See [LLM Integration](llm-integration.md).

**Q: How do I test without making real API calls?**
A: Use the unit tests which mock HTTP responses with `respx`. Run `uv run pytest`.

**Q: Can I use a different Python version?**
A: Python 3.12+ is required. The project uses modern type hints and features.

**Q: How do I update dependencies?**
A: Edit `pyproject.toml`, then run `uv sync` to update `uv.lock`.

**Q: Where can I ask questions?**
A: Open an issue or discussion on GitHub: https://github.com/ratibor78/actions-ai-advisor/issues

---

## See Also

- [Architecture](architecture.md) — System design and component overview
- [Language Support](language-support.md) — Adding new language detection patterns
- [LLM Integration](llm-integration.md) — Prompt engineering and provider configuration
- [Design Decisions](design-decisions.md) — Why we made specific choices
