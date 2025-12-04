# Actions AI Advisor — Documentation

Welcome to the comprehensive documentation for Actions AI Advisor, a GitHub Action that uses LLMs to automatically analyze failed CI/CD workflows.

---

## 📚 Documentation Index

### Getting Started

**New to Actions AI Advisor?** Start here:
- [Main README](../README.md) — Quick start, examples, and basic configuration
- [Architecture Overview](architecture.md#system-overview) — High-level system design

### For Users

**Using the action in your workflows:**
- [Configuration Guide](../README.md#configuration) — All input options explained
- [Provider Setup](../README.md#llm-providers) — OpenAI, Anthropic, OpenRouter, self-hosted
- [Cost & Token Usage](../README.md#cost--token-usage) — Pricing and optimization

### For Developers

**Contributing to the project:**
- [Development Guide](development.md) — Setup, testing, contributing
- [Architecture](architecture.md) — Component design and data flow
- [Design Decisions](design-decisions.md) — Why we chose specific approaches

### Technical Deep Dives

**Detailed technical documentation:**
- [Language Support](language-support.md) — Detection patterns for 10+ languages
- [LLM Integration](llm-integration.md) — Prompt engineering and provider details

---

## 📖 Documentation by Topic

### Architecture & Design

<table>
<tr>
<td width="200"><b>Document</b></td>
<td><b>Contents</b></td>
</tr>
<tr>
<td>

[Architecture](architecture.md)

</td>
<td>

- System overview and high-level flow
- Component architecture (8 core modules)
- Data flow and transformations
- Technology stack and rationale
- Design principles
- Performance characteristics
- Extension points for future features

</td>
</tr>
<tr>
<td>

[Design Decisions](design-decisions.md)

</td>
<td>

- Docker vs Node.js action type
- Python vs Go/Rust language choice
- uv vs pip/poetry package manager
- Unified LLM client vs per-provider SDKs
- Job Summary vs PR comments output
- Single vs split prompts
- tiktoken vs API token counting
- Hardcoded patterns vs ML extraction
- Hardcoded pricing vs API lookups
- Hardcoded preprocessing vs configurable

</td>
</tr>
</table>

### Language & File Detection

<table>
<tr>
<td width="200"><b>Document</b></td>
<td><b>Contents</b></td>
</tr>
<tr>
<td>

[Language Support](language-support.md)

</td>
<td>

- Overview of support tiers (first-class vs supported)
- **First-Class Support:** Python, JavaScript/TypeScript, Go, Rust, Java, .NET/C#
- **Supported Languages:** PHP, Ruby, C/C++, Docker
- Detection patterns reference (regex patterns for each language)
- Path normalization and working directory detection
- Library file filtering (Java JDK, Python site-packages)
- Hybrid link strategy (direct vs search links)
- How to add new language support
- Language detection statistics
- Limitations and FAQ

</td>
</tr>
</table>

### LLM & Prompt Engineering

<table>
<tr>
<td width="200"><b>Document</b></td>
<td><b>Contents</b></td>
</tr>
<tr>
<td>

[LLM Integration](llm-integration.md)

</td>
<td>

- Unified client architecture
- Supported providers (OpenAI, Anthropic, OpenRouter, self-hosted)
- Prompt engineering philosophy
- System prompt design (adaptive verbosity)
- User prompt template
- Provider-specific configuration
- Token optimization strategies
- Cost management and pricing
- Error handling
- Future enhancements

</td>
</tr>
</table>

### Development & Contributing

<table>
<tr>
<td width="200"><b>Document</b></td>
<td><b>Contents</b></td>
</tr>
<tr>
<td>

[Development Guide](development.md)

</td>
<td>

- Getting started (prerequisites, installation)
- Development workflow
- Testing (unit tests, integration tests, Docker testing)
- Code quality standards (ruff, mypy)
- Contributing process
- Adding language support
- Release process
- Debugging tips
- Tools and libraries reference
- FAQ

</td>
</tr>
</table>

---

## 🎯 Quick Navigation by Use Case

### "I want to use this action in my workflow"
1. Read [Quick Start](../README.md#quick-start) in main README
2. Configure your [LLM Provider](../README.md#llm-providers)
3. Understand [Cost & Token Usage](../README.md#cost--token-usage)

### "I want to understand how it works"
1. Start with [System Overview](architecture.md#system-overview)
2. Read [Data Flow](architecture.md#data-flow)
3. Review [Component Architecture](architecture.md#component-architecture)

### "I want to add support for a new language"
1. Read [Language Support Overview](language-support.md#overview)
2. Follow [Adding New Languages](language-support.md#adding-new-languages)
3. Reference [Detection Patterns](language-support.md#detection-patterns-reference)
4. Contribute via [Development Guide](development.md#contributing)

### "I want to understand why you made certain choices"
1. Read [Design Decisions](design-decisions.md)
2. See specific decision rationales (e.g., [Single vs Split Prompts](design-decisions.md#prompt-strategy-single-vs-split-prompts))

### "I want to optimize costs"
1. Read [Token Optimization](llm-integration.md#token-optimization)
2. Review [Cost Management](llm-integration.md#cost-management)
3. Understand [Preprocessing Optimizations](architecture.md#3-preprocessorpy--log-cleaning--optimization)

### "I want to contribute to the project"
1. Read [Development Guide](development.md)
2. Follow [Getting Started](development.md#getting-started)
3. Review [Contribution Process](development.md#contributing)
4. Check [Code Quality Standards](development.md#code-quality)

---

## 🏗️ Project Structure

```
actions-advisor/
├── .github/workflows/        # CI/CD pipelines
│   ├── ci.yml                # Lint, test, build
│   ├── release.yml           # Release automation
│   └── test-action.yml       # E2E tests
│
├── docs/                     # Documentation (you are here!)
│   ├── README.md             # This file (documentation index)
│   ├── architecture.md       # System design
│   ├── design-decisions.md   # Architectural choices
│   ├── language-support.md   # Language detection details
│   ├── llm-integration.md    # Prompt engineering
│   └── development.md        # Contributing guide
│
├── src/actions_advisor/      # Source code (8 modules)
│   ├── __init__.py
│   ├── main.py               # Orchestration
│   ├── config.py             # Configuration
│   ├── log_fetcher.py        # GitHub API
│   ├── preprocessor.py       # Log cleaning
│   ├── file_parser.py        # File extraction
│   ├── llm_client.py         # LLM integration
│   ├── formatter.py          # Markdown output
│   └── tokens.py             # Token counting
│
├── tests/                    # Test suite (65 tests)
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_file_parser.py
│   ├── test_formatter.py
│   ├── test_llm_client.py
│   ├── test_log_fetcher.py
│   ├── test_preprocessor.py
│   └── test_tokens.py
│
├── action.yml                # GitHub Action definition
├── Dockerfile                # Docker container
├── pyproject.toml            # Project configuration
├── uv.lock                   # Locked dependencies
├── README.md                 # Main README
└── LICENSE                   # MIT License
```

---

## 📊 Documentation Statistics

- **Total Pages:** 6 comprehensive documents
- **Total Content:** ~12,000+ lines of documentation
- **Topics Covered:** Architecture, design, languages, LLM, development
- **Audience:** Users, developers, AI agents

---

## 🤖 For AI Agents & LLMs

This documentation is designed to be **AI-friendly**:

- **Comprehensive context** — Full design rationale and implementation details
- **Structured information** — Clear sections, tables, code examples
- **Cross-referenced** — Links between related topics
- **Searchable** — Markdown format for easy parsing
- **Complete** — Covers WHY (design decisions) and HOW (implementation)

When working on this codebase, AI agents should:
1. Read [Architecture](architecture.md) first for system understanding
2. Review [Design Decisions](design-decisions.md) to understand rationale
3. Consult specific topic docs for detailed implementation
4. Follow [Development Guide](development.md) for contributing

---

## 🔗 External Resources

### Official Links
- **GitHub Repository:** https://github.com/ratibor78/actions-advisor
- **Issues:** https://github.com/ratibor78/actions-advisor/issues
- **Discussions:** https://github.com/ratibor78/actions-advisor/discussions
- **Releases:** https://github.com/ratibor78/actions-advisor/releases

### Related Projects
- **uv (package manager):** https://github.com/astral-sh/uv
- **httpx (HTTP client):** https://www.python-httpx.org/
- **tiktoken (tokenizer):** https://github.com/openai/tiktoken
- **ruff (linter):** https://docs.astral.sh/ruff/

### LLM Provider Docs
- **OpenAI API:** https://platform.openai.com/docs
- **Anthropic API:** https://docs.anthropic.com/
- **OpenRouter:** https://openrouter.ai/docs

---

## 📝 Document Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-05 | 1.0 | Initial comprehensive documentation created |

---

## 🤝 Contributing to Documentation

Documentation improvements are welcome! When contributing:

1. **Accuracy** — Ensure technical accuracy
2. **Clarity** — Write for both humans and AI agents
3. **Completeness** — Cover WHY and HOW, not just WHAT
4. **Examples** — Include code examples and tables
5. **Cross-reference** — Link to related sections
6. **Update index** — Keep this README.md updated

See [Development Guide](development.md#contributing) for contribution process.

---

## 📧 Questions or Feedback?

- **General questions:** Open a [Discussion](https://github.com/ratibor78/actions-advisor/discussions)
- **Bug reports:** Open an [Issue](https://github.com/ratibor78/actions-advisor/issues)
- **Feature requests:** Open an [Issue](https://github.com/ratibor78/actions-advisor/issues) with `[Feature Request]` prefix
- **Documentation issues:** Open an [Issue](https://github.com/ratibor78/actions-advisor/issues) with `[Docs]` prefix

---

*Happy coding! 🚀*
