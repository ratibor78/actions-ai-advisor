# LLM Integration

This document explains how Actions AI Advisor integrates with Large Language Models, including prompt engineering, provider support, and optimization strategies.

---

## Table of Contents

- [Overview](#overview)
- [Unified Client Architecture](#unified-client-architecture)
- [Prompt Engineering](#prompt-engineering)
- [Provider Configuration](#provider-configuration)
- [Token Optimization](#token-optimization)
- [Cost Management](#cost-management)
- [Error Handling](#error-handling)

---

## Overview

Actions AI Advisor uses a **unified LLM client** that works with multiple providers via the OpenAI-compatible chat completions API.

### Key Characteristics

- **Provider-agnostic** — Single client works with OpenAI, Anthropic, OpenRouter, self-hosted
- **Zero dependencies on official SDKs** — Uses `httpx` for HTTP requests
- **Adaptive output** — Single prompt adjusts to error complexity
- **Cost-transparent** — Always shows token counts and estimated cost
- **Fast** — Typical LLM response time: 5-20 seconds

---

## Unified Client Architecture

### Why Unified? (vs Per-Provider SDKs)

**Advantages:**
- ✅ Single codebase for all providers
- ✅ Smaller dependency footprint (only `httpx`)
- ✅ Full control over request/response handling
- ✅ Easy to add new providers (just endpoint + headers)
- ✅ No SDK version conflicts

**Trade-offs:**
- ❌ Manual API implementation
- ❌ Need to handle provider quirks ourselves
- ❌ No SDK-level retries (we implement our own)

See [Design Decisions: LLM Client](design-decisions.md#llm-client-unified-vs-per-provider-sdks) for full rationale.

### Supported Providers

| Provider | Base URL | Auth Method | Special Headers |
|----------|----------|-------------|-----------------|
| **OpenAI** | `https://api.openai.com/v1` | Bearer token | None |
| **Anthropic** | `https://api.anthropic.com/v1` | `x-api-key` | `anthropic-version: 2023-06-01` |
| **OpenRouter** | `https://openrouter.ai/api/v1` | Bearer token | `HTTP-Referer`, `X-Title` |
| **Self-hosted** | Custom (user-provided) | Bearer token | None |

### Request Format

All providers use the **OpenAI chat completions format**:

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "system",
      "content": "[System prompt - see Prompt Engineering section]"
    },
    {
      "role": "user",
      "content": "[User prompt with job metadata + preprocessed logs]"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 1500
}
```

**Parameters:**
- `model` — Provider-specific model name
- `temperature` — `0.3` (deterministic but not completely rigid)
- `max_tokens` — `1500` (enough for detailed analysis without excessive cost)

### Response Parsing

```json
{
  "choices": [
    {
      "message": {
        "content": "[Markdown analysis text]"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 3247,
    "completion_tokens": 423,
    "total_tokens": 3670
  }
}
```

We extract:
- `analysis` — From `choices[0].message.content`
- `input_tokens` — From `usage.prompt_tokens`
- `output_tokens` — From `usage.completion_tokens`

---

## Prompt Engineering

### Design Philosophy

**Goals:**
1. **Concise but complete** — Provide enough guidance without over-constraining
2. **Adaptive** — LLM adjusts verbosity based on error complexity
3. **Professional** — No emojis, engineering-grade output
4. **Actionable** — Focus on fixes developers can implement immediately

**Non-goals:**
- Not trying to replace senior engineers
- Not providing multi-page analysis reports
- Not teaching fundamental concepts

### System Prompt

**Current Version (v1.0.0):**

```
You are an expert CI/CD debugger. Analyze GitHub Actions failures and provide clear, actionable guidance.

**Output Format:**

## Root Cause
[1-3 sentences explaining why it failed]

## Recommended Actions
[Numbered list with code examples - be concise for simple issues, detailed for complex ones]

## Error Context
[Key error lines - include stack trace if relevant]

**Style Guidelines:**
- Use professional terminology (e.g., "Impacted Files" not "Affected Files")
- Number your recommendations (1. 2. 3.)
- Include code snippets for fixes when applicable
- Be concise for obvious errors (syntax errors, missing dependencies, simple config issues)
- Be thorough for complex issues (race conditions, integration failures, logic bugs)
- No emojis
- Focus on actionable fixes that developers can implement immediately
```

### User Prompt Template

```
Analyze this failed GitHub Actions log:

**Job:** {job_name}
**Step:** {step_name}
**Exit Code:** {exit_code}

```
{log_content}
```
```

**Variables:**
- `{job_name}` — E.g., "build", "test", "lint"
- `{step_name}` — E.g., "Run tests", "Install dependencies"
- `{exit_code}` — E.g., "1", "127", "N/A"
- `{log_content}` — Preprocessed logs (cleaned, 70% token reduction)

### Adaptive Verbosity

The prompt includes guidance for the LLM to adapt based on error complexity:

**Simple Errors (syntax, missing deps):**
```markdown
## Root Cause
Ruby syntax error: unclosed parenthesis in method definition.

## Recommended Actions
1. Add closing parenthesis on line 4:
   ```ruby
   def broken(param1)
     puts "Fixed"
   end
   ```

## Error Context
```
ruby-app/bad.rb:5: syntax error, unexpected string literal
```
```

**Complex Errors (race conditions, logic bugs):**
```markdown
## Root Cause
The test expects 20 (5 * 4) but receives 8 (5 + 4) because the `multiply` function incorrectly uses addition instead of multiplication. This is a logic error in the implementation.

## Recommended Actions
1. Fix the operator in `src/calculator.py:42`:
   ```python
   def multiply(a, b):
       return a * b  # Changed from a + b
   ```

2. Add test coverage for edge cases:
   ```python
   def test_multiply_zero():
       assert multiply(5, 0) == 0

   def test_multiply_negative():
       assert multiply(-3, 4) == -12
   ```

3. Consider using type hints to catch similar issues:
   ```python
   def multiply(a: int, b: int) -> int:
       return a * b
   ```

## Error Context
```
AssertionError: assert 8 == 20
  Expected: 20 (5 * 4)
  Got: 8 (5 + 4 due to bug on line 42)
File "src/calculator.py", line 42, in multiply
    return a + b  # Bug here
```
```

The LLM naturally produces more detailed output for complex scenarios based on the "be concise for simple, thorough for complex" guideline.

### Prompt Evolution

**v0.1.0 (Initial):**
- Used emojis (🎯, 💡, 📋)
- Forced 3 fixes always
- Error details in `<details>` collapsible

**v1.0.0 (Current):**
- No emojis (professional)
- Adaptive recommendations (1-4 based on complexity)
- Errors visible (not collapsed)
- Cleaner section headers

**v1.1.0 (Planned):**
- User-configurable prompts (custom system prompt)
- Language-specific hints (optional)
- Project context injection (e.g., "This is a Django project")

---

## Provider Configuration

### OpenAI

**Recommended Models:**
- **gpt-4o-mini** ⭐ — Fast, cheap (~$0.0005/analysis), good quality
- **gpt-4o** — Premium, expensive (~$0.0080/analysis), best quality

**Configuration:**
```yaml
- uses: ratibor78/actions-ai-advisor@v1
  with:
    github-token: ${{ github.token }}
    api-key: ${{ secrets.OPENAI_API_KEY }}
    provider: openai
    model: gpt-4o-mini
```

**API Key:** [Get from OpenAI Platform](https://platform.openai.com/api-keys)

**Headers:**
```python
{
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
```

---

### Anthropic Claude

**Recommended Models:**
- **claude-3-5-haiku-latest** ⭐ — Fast, moderate cost (~$0.0016/analysis)
- **claude-sonnet-4-latest** — Premium, expensive (~$0.0090/analysis)

**Configuration:**
```yaml
- uses: ratibor78/actions-ai-advisor@v1
  with:
    github-token: ${{ github.token }}
    api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    provider: anthropic
    model: claude-3-5-haiku-latest
```

**API Key:** [Get from Anthropic Console](https://console.anthropic.com)

**Headers (Special):**
```python
{
    "x-api-key": api_key,  # NOT "Authorization: Bearer"
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}
```

**Note:** Anthropic uses non-standard auth header (`x-api-key` instead of `Authorization`).

---

### OpenRouter

**Recommended Models:**
- **openai/gpt-4o-mini** — Same as OpenAI but via OpenRouter
- **google/gemini-flash-1.5** — Very cheap (~$0.0002/analysis)
- **anthropic/claude-3-5-haiku** — Via OpenRouter

**Configuration:**
```yaml
- uses: ratibor78/actions-ai-advisor@v1
  with:
    github-token: ${{ github.token }}
    api-key: ${{ secrets.OPENROUTER_API_KEY }}
    provider: openrouter
    model: openai/gpt-4o-mini  # Note: provider/model format
```

**API Key:** [Get from OpenRouter](https://openrouter.ai/keys)

**Headers (Special):**
```python
{
    "Authorization": f"Bearer {api_key}",
    "HTTP-Referer": "https://github.com/actions-ai-advisor",  # Required by OpenRouter
    "X-Title": "Actions AI Advisor",  # Optional but recommended
    "Content-Type": "application/json"
}
```

**Pricing:** Varies by model, check [OpenRouter pricing](https://openrouter.ai/docs#models)

---

### Self-Hosted (vLLM, Ollama, etc.)

**Supported Runtimes:**
- vLLM (OpenAI-compatible API)
- Ollama (via OpenAI compatibility layer)
- LocalAI
- LM Studio
- Any OpenAI-compatible endpoint

**Configuration:**
```yaml
- uses: ratibor78/actions-ai-advisor@v1
  with:
    github-token: ${{ github.token }}
    api-key: ${{ secrets.VLLM_API_KEY }}  # Can be anything for local
    provider: selfhosted
    model: meta-llama/Llama-3.1-8B-Instruct
    base-url: https://your-vllm-instance.com/v1
```

**Requirements:**
- Endpoint must implement OpenAI `/v1/chat/completions` API
- Must return `usage` field with token counts
- Model should support chat format (system + user messages)

**Example: Local Ollama:**
```yaml
    provider: selfhosted
    model: llama3.1
    base-url: http://localhost:11434/v1
```

**Cost:** Free (self-hosted), but requires GPU infrastructure

---

## Token Optimization

### Why Optimize?

**Cost Impact:**
- Unoptimized: 30,000 tokens × $0.15/1M = **$0.0045** per analysis
- Optimized (70% reduction): 10,000 tokens × $0.15/1M = **$0.0015** per analysis
- **Savings: 67%** per analysis

At scale (100 analyses/day):
- Unoptimized: $0.45/day = **$164/year**
- Optimized: $0.15/day = **$55/year**
- **Savings: $109/year** for a single project

### Token Counting

We use **tiktoken** (OpenAI's tokenizer) for accurate local token counting:

```python
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-4o-mini")
tokens = encoding.encode(text)
token_count = len(tokens)
```

**Accuracy:**
- ✅ 100% accurate for OpenAI models
- ⚠️ ~95% accurate for Claude (uses similar BPE tokenizer)
- ⚠️ ~90% accurate for other models (varies)

**Fallback:** Use `cl100k_base` encoding for unknown models.

### Preprocessing Optimizations

See `preprocessor.py` for implementation:

| Optimization | Token Reduction | Example |
|--------------|-----------------|---------|
| **ANSI removal** | 5-10% | `\x1b[31mError\x1b[0m` → `Error` |
| **Timestamp stripping** | 10-15% | `2024-01-15T10:23:45.123Z Error` → `Error` |
| **Metadata filtering** | 5-10% | `##[group]Run tests` → (removed) |
| **Repeated line collapse** | 20-30% | `npm WARN` × 50 → `npm WARN (repeated 50 times)` |
| **Failed step extraction** | 10-15% | Keep only failed steps, not entire workflow |
| **Context trimming** | 5-10% | Last 150 lines per step |

**Total:** ~70% reduction (30,000 → 10,000 tokens typical)

### Max Tokens Configuration

```python
payload = {
    "model": self.model,
    "messages": [...],
    "temperature": 0.3,
    "max_tokens": 1500  # Output limit
}
```

**Why 1500?**
- Allows detailed analysis with multiple recommendations
- Prevents runaway costs (worst case: 1500 output tokens)
- Typical output: 300-600 tokens (well below limit)

**Cost Protection:**
- Input: ~10,000 tokens (after preprocessing)
- Output: max 1,500 tokens
- **Worst case cost:** (10,000 × $0.15 + 1,500 × $0.60) / 1M = **$0.0024** with gpt-4o-mini

---

## Cost Management

### Pricing Table (Hardcoded)

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

**Calculation:**
```python
cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
```

**Example:**
- Input: 3,247 tokens
- Output: 423 tokens
- Model: gpt-4o-mini ($0.15 / $0.60 per 1M)
- Cost: (3,247 × 0.15 + 423 × 0.60) / 1,000,000 = **$0.0007**

### Cost Display

Always shown in Job Summary:
```markdown
### Analysis Details
**Model:** `gpt-4o-mini` | **Tokens:** 3,247 in + 423 out | **Cost:** ~$0.0007
```

**For self-hosted:** Shows "N/A" (no API cost)
**For OpenRouter:** Shows "Varies" (pricing depends on model + provider)

### Cost Optimization Tips

1. **Use gpt-4o-mini** — 5x cheaper than gpt-4o, 90% of the quality
2. **Reduce log verbosity** — Less verbose logging = fewer tokens
3. **Filter early** — Fail fast to avoid long logs
4. **Self-host for high volume** — If >1000 analyses/month, consider local LLM

---

## Error Handling

### API Errors

**Handled Gracefully:**
- `401 Unauthorized` — Invalid API key (clear error message)
- `429 Too Many Requests` — Rate limit (retry with exponential backoff)
- `500 Internal Server Error` — Provider outage (log and fail gracefully)
- `Timeout` — Network issues (retry once, then fail)

**Example Error Message:**
```
Error: OpenAI API authentication failed. Please check your OPENAI_API_KEY secret.
```

### Network Errors

```python
async with httpx.AsyncClient(timeout=60.0) as client:
    try:
        response = await client.post(...)
    except httpx.TimeoutException:
        # Retry once with longer timeout
    except httpx.NetworkError:
        # Log error and exit gracefully
```

**Timeout:** 60 seconds (most LLM responses complete in 5-20s)

### Validation Errors

**Pre-flight checks:**
- ✅ API key is set
- ✅ Provider is valid (`openai`, `anthropic`, `openrouter`, `selfhosted`)
- ✅ Model name is not empty
- ✅ Base URL is set for selfhosted provider

**Example:**
```python
if provider == "selfhosted" and not base_url:
    raise ValueError("base-url is required for selfhosted provider")
```

---

## Future Enhancements

### v1.1.0 Planned

- [ ] **Custom prompts** — User-provided system prompt via `.github/advisor-prompts/system.txt`
- [ ] **Streaming responses** — Lower latency via SSE streaming
- [ ] **Retry logic** — Exponential backoff for transient errors
- [ ] **Model fallbacks** — Try cheaper model if primary fails

### v1.2.0 Research

- [ ] **Local LLM support** — Better integration with Ollama/vLLM
- [ ] **Multi-agent analysis** — Coordinator + language-specific specialists
- [ ] **Function calling** — Structured output via OpenAI function calling
- [ ] **Vision support** — Analyze screenshots in failed UI tests

---

## See Also

- [Design Decisions: Prompt Strategy](design-decisions.md#prompt-strategy-single-vs-split-prompts)
- [Architecture: LLM Client](architecture.md#6-llm_clientpy--llm-integration)
- [Development Guide: Testing LLM Integration](development.md)
