"""Tests for token counting and cost estimation."""

from actions_advisor.tokens import TokenCounter


def test_token_counting():
    """Test token counting."""
    counter = TokenCounter("gpt-4o-mini")
    text = "Hello, world!"
    tokens = counter.count_tokens(text)
    # "Hello, world!" is typically ~3-4 tokens
    assert 2 <= tokens <= 5


def test_token_counting_longer_text():
    """Test token counting with longer text."""
    counter = TokenCounter("gpt-4o-mini")
    text = "This is a longer piece of text that should have more tokens. " * 10
    tokens = counter.count_tokens(text)
    assert tokens > 50  # Should be well over 50 tokens


def test_token_counting_fallback_for_unknown_model():
    """Test that unknown models fall back to cl100k_base."""
    counter = TokenCounter("unknown-model-xyz")
    text = "Hello, world!"
    tokens = counter.count_tokens(text)
    # Should still work with fallback encoding
    assert tokens > 0


def test_cost_estimation_openai():
    """Test cost estimation for OpenAI models."""
    cost = TokenCounter.estimate_cost(
        input_tokens=1000, output_tokens=500, provider="openai", model="gpt-4o-mini"
    )
    # 1000 * 0.15 / 1M + 500 * 0.60 / 1M = 0.00015 + 0.0003 = 0.00045
    assert cost is not None
    assert 0.0004 <= cost <= 0.0005


def test_cost_estimation_anthropic():
    """Test cost estimation for Anthropic models."""
    cost = TokenCounter.estimate_cost(
        input_tokens=2000,
        output_tokens=1000,
        provider="anthropic",
        model="claude-3-5-haiku-latest",
    )
    # 2000 * 0.80 / 1M + 1000 * 4.00 / 1M = 0.0016 + 0.004 = 0.0056
    assert cost is not None
    assert 0.005 <= cost <= 0.006


def test_cost_estimation_unknown_provider():
    """Test that unknown provider returns None."""
    cost = TokenCounter.estimate_cost(
        input_tokens=1000, output_tokens=500, provider="unknown", model="some-model"
    )
    assert cost is None


def test_cost_estimation_unknown_model():
    """Test that unknown model returns None."""
    cost = TokenCounter.estimate_cost(
        input_tokens=1000, output_tokens=500, provider="openai", model="unknown-model"
    )
    assert cost is None


def test_cost_estimation_zero_tokens():
    """Test cost estimation with zero tokens."""
    cost = TokenCounter.estimate_cost(
        input_tokens=0, output_tokens=0, provider="openai", model="gpt-4o-mini"
    )
    assert cost == 0.0
