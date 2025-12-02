"""Token counting and cost estimation module."""

import tiktoken

# Pricing per 1M tokens (input, output)
PRICING: dict[str, dict[str, tuple[float, float]]] = {
    "openai": {
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
        "gpt-4-turbo": (10.00, 30.00),
        "gpt-3.5-turbo": (0.50, 1.50),
    },
    "anthropic": {
        "claude-3-5-haiku-latest": (0.80, 4.00),
        "claude-3-5-haiku-20241022": (0.80, 4.00),
        "claude-3-5-sonnet-latest": (3.00, 15.00),
        "claude-3-5-sonnet-20241022": (3.00, 15.00),
        "claude-sonnet-4-latest": (3.00, 15.00),
        "claude-3-opus-latest": (15.00, 75.00),
    },
}


class TokenCounter:
    """Count tokens and estimate costs for LLM API calls."""

    def __init__(self, model: str) -> None:
        """Initialize token counter.

        Args:
            model: Model name to use for token counting
        """
        self.model = model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fall back to cl100k_base for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    @staticmethod
    def estimate_cost(
        input_tokens: int, output_tokens: int, provider: str, model: str
    ) -> float | None:
        """Estimate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: LLM provider name
            model: Model name

        Returns:
            Estimated cost in USD, or None if pricing not available
        """
        if provider not in PRICING:
            return None

        model_pricing = PRICING[provider].get(model)
        if not model_pricing:
            return None

        input_price, output_price = model_pricing
        cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
        return cost
