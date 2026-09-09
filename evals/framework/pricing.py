"""Token pricing table for cost estimation.

Prices are USD per 1 million tokens. Update these from your provider's
pricing page — they change frequently and this table is only a baseline.
"""

from __future__ import annotations

from typing import Optional

# (input_price_per_1M, output_price_per_1M)
PRICE_TABLE: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "o3": (2.00, 8.00),
    "o4-mini": (1.10, 4.40),
    # Anthropic
    "claude-opus-4": (15.00, 75.00),
    "claude-sonnet-4": (3.00, 15.00),
    "claude-haiku-3.5": (0.80, 4.00),
    # Local / self-hosted models are free per-token
    "local": (0.0, 0.0),
    "ollama": (0.0, 0.0),
}


def estimate_cost_usd(model: Optional[str], input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for one response.

    Matching is prefix-based so dated model names (e.g. "gpt-4o-2024-08-06")
    resolve to their base family. Unknown models return 0.0 — treat cost as
    unmeasured rather than zero-billed.
    """
    if not model:
        return 0.0
    model_lower = model.lower()
    for prefix, (pin, pout) in PRICE_TABLE.items():
        if model_lower.startswith(prefix):
            return (input_tokens * pin + output_tokens * pout) / 1_000_000
    return 0.0
