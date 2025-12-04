# Design Decisions

This document explains the key architectural and technical decisions made in Actions AI Advisor, including the rationale, trade-offs, and alternatives considered.

---

## Table of Contents

- [Action Type: Docker vs Node.js](#action-type-docker-vs-nodejs)
- [Language: Python vs Go/Rust](#language-python-vs-gorust)
- [Package Manager: uv vs pip/poetry](#package-manager-uv-vs-pippoetry)
- [LLM Client: Unified vs Per-Provider SDKs](#llm-client-unified-vs-per-provider-sdks)
- [Output: Job Summary vs PR Comments](#output-job-summary-vs-pr-comments)
- [Prompt Strategy: Single vs Split Prompts](#prompt-strategy-single-vs-split-prompts)
- [Token Counting: tiktoken vs API Estimates](#token-counting-tiktoken-vs-api-estimates)
- [File Path Extraction: Hardcoded Patterns vs ML](#file-path-extraction-hardcoded-patterns-vs-ml)
- [Cost Calculation: Hardcoded Pricing vs API](#cost-calculation-hardcoded-pricing-vs-api)
- [Log Preprocessing: Hardcoded Rules vs Configurable](#log-preprocessing-hardcoded-rules-vs-configurable)

---

## Action Type: Docker vs Node.js

### Decision
Use **Docker-based action** (not Node.js composite action)

### Rationale

**Pros of Docker:**
- ✅ Full control over Python version (3.12+)
- ✅ Consistent environment across all runners
- ✅ No Node.js version compatibility issues
- ✅ Easier to test locally (`docker build && docker run`)
- ✅ Can install system dependencies if needed

**Cons of Docker:**
- ❌ Slightly slower startup (~5-10s container pull)
- ❌ Larger action artifact (~200MB vs ~50MB for Node)

**Alternatives Considered:**

**Node.js Composite Action:**
- Would require Python installation in action
- Node.js version compatibility issues (v16 vs v18 vs v20)
- More complex setup for users
- **Rejected:** Too much variability in Python setup

**Native Node.js Implementation:**
- Would need to rewrite in TypeScript/JavaScript
- Less mature LLM ecosystem in Node.js
- No tiktoken equivalent (would need WASM or estimation)
- **Rejected:** Python has better LLM tooling

### Trade-offs Accepted
- Slower startup (5-10s) in exchange for reliability and consistency
- Larger artifact size for simpler maintenance

---

## Language: Python vs Go/Rust

### Decision
Use **Python 3.12+**

### Rationale

**Pros of Python:**
- ✅ Best LLM ecosystem (tiktoken, langchain, openai SDK)
- ✅ Fast development iteration
- ✅ Excellent async support (`httpx`, `asyncio`)
- ✅ Strong typing with type hints + mypy
- ✅ Team familiarity

**Cons of Python:**
- ❌ Slower than compiled languages
- ❌ Larger Docker image (~200MB vs ~20MB for Go)

**Alternatives Considered:**

**Go:**
- Pros: Fast, small binaries, good concurrency
- Cons: No tiktoken library, weaker LLM ecosystem, longer development time
- **Rejected:** LLM tooling not mature enough

**Rust:**
- Pros: Fast, memory-safe, small binaries
- Cons: Steep learning curve, slow compilation, limited LLM libraries
- **Rejected:** Development speed more important than runtime speed

**TypeScript/Node.js:**
- Pros: GitHub Actions native language, good async
- Cons: No tiktoken equivalent, weaker LLM tooling
- **Rejected:** (see "Action Type" decision above)

### Trade-offs Accepted
- Slower execution (~2-3s vs <1s for Go) in exchange for faster development
- Larger Docker image in exchange for better LLM tooling

---

## Package Manager: uv vs pip/poetry

### Decision
Use **uv** for package management

### Rationale

**Pros of uv:**
- ✅ 10-100x faster than pip
- ✅ Reliable lock files (`uv.lock`)
- ✅ Better dependency resolution
- ✅ Single binary (no separate virtualenv tools)
- ✅ Drop-in replacement for pip/poetry commands

**Cons of uv:**
- ❌ Relatively new (less battle-tested than pip)
- ❌ Smaller community than pip/poetry

**Alternatives Considered:**

**pip:**
- Pros: Mature, universal, well-documented
- Cons: Slow, no lock files, poor dependency resolution
- **Rejected:** uv is 100% compatible, just faster

**poetry:**
- Pros: Good dependency management, lock files
- Cons: Slow, complex configuration, large overhead
- **Rejected:** uv provides same benefits with better performance

### Trade-offs Accepted
- Smaller community in exchange for 10-100x faster installs
- Newer tool in exchange for better reliability

---

## LLM Client: Unified vs Per-Provider SDKs

### Decision
Use **single unified client** with OpenAI-compatible API (not official SDKs)

### Rationale

**Pros of Unified Client:**
- ✅ Single codebase for all providers
- ✅ Smaller dependency footprint (only `httpx`)
- ✅ Full control over request/response handling
- ✅ No SDK version conflicts
- ✅ Easier to add new providers (just endpoint + headers)

**Cons of Unified Client:**
- ❌ Manual implementation of API calls
- ❌ Need to handle provider-specific quirks ourselves
- ❌ No SDK-level retries or error handling

**Alternatives Considered:**

**Official SDKs (openai, anthropic, etc.):**
- Pros: Official support, automatic retries, typed responses
- Cons: Multiple dependencies (openai + anthropic + ...), version conflicts, larger Docker image
- **Rejected:** Complexity not worth the benefits for our simple use case

**Langchain:**
- Pros: Unified abstraction, provider switching
- Cons: Heavy dependency (50+ packages), over-engineered for our needs
- **Rejected:** Too much overhead for simple chat completion

### Trade-offs Accepted
- Manual API implementation in exchange for simplicity and control
- Provider-specific quirks handled manually in exchange for smaller footprint

### Implementation Details

**Provider Support:**
```python
PROVIDER_ENDPOINTS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}
```

**Provider-Specific Headers:**
- Anthropic: `x-api-key`, `anthropic-version`
- OpenRouter: `HTTP-Referer`, `X-Title`
- Others: Standard `Authorization: Bearer`

---

## Output: Job Summary vs PR Comments

### Decision
**v1.0.0:** Output to Job Summary only (not PR comments)

### Rationale

**Pros of Job Summary:**
- ✅ No additional permissions needed (uses existing actions context)
- ✅ Persistent (stays with workflow run forever)
- ✅ Visible in GitHub Actions UI (dedicated tab)
- ✅ Shareable (link to run shares analysis)
- ✅ Simpler implementation (just write to file)

**Cons of Job Summary:**
- ❌ Not visible in PR conversation
- ❌ Developers might miss it (need to click into workflow)

**Alternatives Considered:**

**PR Comments:**
- Pros: Visible in PR conversation, better visibility
- Cons: Requires `pull-requests: write` permission, need to handle comment updates, only works for PRs (not push/schedule)
- **Decision:** Add in v1.1.0 as opt-in feature

**Both (Job Summary + PR Comments):**
- Pros: Best visibility
- Cons: More complexity, duplicate content
- **Decision:** Add in v1.1.0 with flag to enable PR comments

### Trade-offs Accepted
- Lower initial visibility in exchange for simpler implementation
- Plan to add PR comment mode in v1.1.0

---

## Prompt Strategy: Single vs Split Prompts

### Decision
Use **single adaptive prompt** (not separate prompts for simple vs complex errors)

### Rationale

**Pros of Single Prompt:**
- ✅ Simpler implementation (one prompt to maintain)
- ✅ LLM naturally adapts based on error complexity
- ✅ Consistent UX (predictable output format)
- ✅ No classification logic needed
- ✅ Easier testing (one path to test)

**Cons of Single Prompt:**
- ❌ Might be too verbose for simple errors
- ❌ Might be too brief for complex errors

**Alternatives Considered:**

**Split Prompts (simple vs complex):**
```python
if is_simple_error(logs):
    prompt = SIMPLE_PROMPT  # Brief, 1-2 recommendations
else:
    prompt = COMPLEX_PROMPT  # Detailed, 3-4 recommendations
```
- Pros: Tailored responses, potentially better quality
- Cons: How to classify "simple" vs "complex"? Adds brittle logic, 2x maintenance, unpredictable UX
- **Rejected:** Complexity not justified

**Multiple Prompts (per language):**
- Pros: Language-specific advice
- Cons: 10+ prompts to maintain, no clear benefit
- **Rejected:** Single prompt handles all languages well

### Trade-offs Accepted
- Occasional over-verbose responses for simple errors in exchange for simplicity
- Reliance on LLM adaptability in exchange for maintainability

### Implementation

**Adaptive Guidelines in Prompt:**
```
Be concise for obvious errors (syntax errors, missing dependencies)
Be thorough for complex issues (race conditions, integration failures)
```

LLM interprets context and adjusts automatically:
- Syntax error → 1-2 brief recommendations
- Race condition → 3-4 detailed recommendations with code examples

---

## Token Counting: tiktoken vs API Estimates

### Decision
Use **tiktoken library** for local token counting

### Rationale

**Pros of tiktoken:**
- ✅ Accurate (same tokenizer OpenAI uses)
- ✅ Fast (local, no API calls)
- ✅ Free (no additional cost)
- ✅ Works offline

**Cons of tiktoken:**
- ❌ OpenAI-specific (not accurate for Anthropic/other models)
- ❌ Requires Python library (adds dependency)

**Alternatives Considered:**

**API-provided counts:**
- Pros: Always accurate for the model used
- Cons: Only available after sending request, can't estimate cost beforehand
- **Decision:** Use both: tiktoken for estimation, API response for actual

**Character-based estimation:**
- Estimate: `tokens ≈ characters / 4`
- Pros: Simple, no dependencies
- Cons: Inaccurate (can be off by 20-30%)
- **Rejected:** Too inaccurate for cost transparency

### Trade-offs Accepted
- Slight inaccuracy for non-OpenAI models in exchange for local counting
- Use API response as source of truth for actual costs

---

## File Path Extraction: Hardcoded Patterns vs ML

### Decision
Use **hardcoded regex patterns** (not ML-based extraction)

### Rationale

**Pros of Hardcoded Patterns:**
- ✅ Fast (<1ms)
- ✅ Deterministic (predictable results)
- ✅ No model loading overhead
- ✅ No additional dependencies
- ✅ Easy to debug and maintain
- ✅ Works offline

**Cons of Hardcoded Patterns:**
- ❌ Need to maintain patterns for each language
- ❌ Might miss novel error formats
- ❌ No adaptation to new tools/languages

**Alternatives Considered:**

**ML-based extraction (NER model):**
- Train model to detect file paths in text
- Pros: Learns new patterns, handles novel formats
- Cons: 100-500MB model, 100-500ms latency, needs GPU for speed, training data required
- **Rejected:** Overhead too high for simple task

**LLM-based extraction:**
- Ask LLM to extract file paths
- Pros: Very flexible, handles any format
- Cons: Extra API call (~$0.0002), 2-5s latency, unreliable (might hallucinate)
- **Rejected:** Cost and latency not justified

**Hybrid (patterns + LLM fallback):**
- Try patterns first, fall back to LLM if none found
- Pros: Best of both worlds
- Cons: Complex, LLM might still hallucinate
- **Considered for v1.1.0**

### Trade-offs Accepted
- Manual pattern maintenance in exchange for speed and determinism
- Might miss novel formats in exchange for reliability

### Current Patterns

**Supported Languages (10+):**
- Python: `File "path", line N`
- JavaScript: `at path:line:col`
- Go: `path:line: message`
- Rust: `path:line:col`
- Java: `at package.Class(File.java:line)`
- .NET: `File(line,col): error`
- PHP, Ruby, C/C++, Docker: Various patterns

---

## Cost Calculation: Hardcoded Pricing vs API

### Decision
Use **hardcoded pricing table** (not real-time API pricing)

### Rationale

**Pros of Hardcoded Pricing:**
- ✅ Fast (no API call)
- ✅ Simple (no additional dependencies)
- ✅ Works offline
- ✅ Predictable

**Cons of Hardcoded Pricing:**
- ❌ Can become outdated
- ❌ Doesn't reflect actual billing (user might have custom pricing)

**Alternatives Considered:**

**Real-time pricing API:**
- Pros: Always accurate, reflects current pricing
- Cons: Extra API call, not all providers offer pricing API, latency
- **Rejected:** Overhead not worth it for estimates

**User-provided pricing:**
- Allow users to configure pricing in action inputs
- Pros: Most accurate for users with custom pricing
- Cons: Complex, most users don't know their pricing
- **Considered for v1.1.0**

### Trade-offs Accepted
- Occasional outdated pricing in exchange for simplicity
- Estimates only (not actual billing) in exchange for no API calls

### Pricing Table

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

**Maintenance:** Update when providers announce pricing changes

---

## Log Preprocessing: Hardcoded Rules vs Configurable

### Decision
Use **hardcoded preprocessing rules** (not user-configurable)

### Rationale

**Pros of Hardcoded Rules:**
- ✅ Zero-config (works out of the box)
- ✅ Optimized for 70% token reduction
- ✅ No user error (can't misconfigure)
- ✅ Simpler implementation
- ✅ Easier to test

**Cons of Hardcoded Rules:**
- ❌ Not customizable (some users might want different rules)
- ❌ Might remove content users want to keep

**Alternatives Considered:**

**Configurable preprocessing:**
```yaml
preprocessing:
  remove_ansi: true
  remove_timestamps: true
  collapse_repeated: true
  collapse_threshold: 3
```
- Pros: Users can fine-tune for their use case
- Cons: Complex, most users won't change defaults, increases support burden
- **Rejected:** Complexity not justified for v1

**Preprocessor plugins:**
- Allow users to write custom preprocessor functions
- Pros: Ultimate flexibility
- Cons: Security risk, complex, very few users would use
- **Rejected:** Too complex for v1

### Trade-offs Accepted
- Lack of customization in exchange for simplicity
- Might remove wanted content in edge cases in exchange for zero-config

### Current Rules

1. **ANSI removal** — Strips color codes (`\x1b[...m`)
2. **Timestamp removal** — Removes ISO 8601 timestamps
3. **Metadata filtering** — Removes `##[group]`, `::set-output`
4. **Repeated line collapse** — `npm WARN` × 50 → single line
5. **Failed step extraction** — Focus on failed steps only
6. **Context trimming** — Last 150 lines per step

**Result:** ~70% token reduction (30KB → 10KB)

---

## Summary of Decisions

| Decision | Chosen Approach | Primary Reason |
|----------|----------------|----------------|
| **Action Type** | Docker | Consistency & control |
| **Language** | Python 3.12+ | LLM ecosystem |
| **Package Manager** | uv | Speed & reliability |
| **LLM Client** | Unified (httpx) | Simplicity |
| **Output** | Job Summary | Simplicity (v1) |
| **Prompt Strategy** | Single adaptive | Simplicity |
| **Token Counting** | tiktoken | Speed & accuracy |
| **File Extraction** | Regex patterns | Speed & determinism |
| **Cost Calculation** | Hardcoded pricing | Simplicity |
| **Preprocessing** | Hardcoded rules | Zero-config |

---

## Future Decisions to Make

### v1.1.0
- [ ] PR comment mode (opt-in flag)
- [ ] Custom prompts (user-provided or from file)
- [ ] Analysis caching strategy
- [ ] Matrix job grouping approach

### v1.2.0
- [ ] Web UI technology stack
- [ ] Metrics storage (SQLite? PostgreSQL? Cloud?)
- [ ] Chat integration (Slack API? Webhooks?)
- [ ] GitHub Enterprise compatibility approach

### Research Phase
- [ ] Local LLM support (Ollama integration?)
- [ ] Multi-agent analysis (coordinator + specialists?)
- [ ] Auto-fix PR generation (safety constraints?)
- [ ] Failure prediction (ML model? Rule-based?)

---

## Lessons Learned

### What Worked Well
1. **Single prompt approach** — LLM adapts naturally, no classification needed
2. **Hardcoded preprocessing** — 70% reduction with zero config
3. **Unified LLM client** — Easy to add new providers
4. **Docker action** — Consistent environment, easy testing

### What We'd Do Differently
1. **Consider tiktoken alternatives** — Anthropic tokenizer for Claude models
2. **Earlier documentation** — Should have started docs/ earlier
3. **More language patterns** — Add Julia, Elixir, Haskell from the start

### Open Questions
1. Should we support streaming responses? (lower latency vs complexity)
2. Should we allow multiple LLM calls for multi-job failures? (cost vs better analysis)
3. Should we add retry logic for LLM API failures? (reliability vs simplicity)

---

## Contributing to Design Decisions

When proposing new features or changes, consider:

1. **Simplicity** — Does this add complexity? Is it worth it?
2. **Zero-config** — Can it work with defaults? Do users need to configure?
3. **Cost** — Does this increase per-analysis cost? By how much?
4. **Security** — Does this require additional permissions?
5. **Maintenance** — Who maintains this? How complex is the code?

See [Development Guide](development.md) for contribution process.
