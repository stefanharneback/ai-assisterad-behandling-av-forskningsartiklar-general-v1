from __future__ import annotations

import unittest
from decimal import Decimal

from article_analysis_general.cost import (
    ModelTokenPricing,
    TokenUsage,
    UsageLedgerEntry,
    estimate_token_cost,
    summarize_costs,
    token_usage_from_response_usage,
)


class CostUsageTests(unittest.TestCase):
    def test_token_usage_from_response_usage_keeps_cached_and_reasoning_tokens(self) -> None:
        usage = token_usage_from_response_usage(
            {
                "prompt_tokens": 1000,
                "completion_tokens": 250,
                "total_tokens": 1250,
                "prompt_tokens_details": {"cached_tokens": 400},
                "completion_tokens_details": {"reasoning_tokens": 75},
            }
        )

        self.assertEqual(usage.prompt_tokens, 1000)
        self.assertEqual(usage.cached_prompt_tokens, 400)
        self.assertEqual(usage.reasoning_tokens, 75)

    def test_estimate_token_cost_uses_pricing_snapshot(self) -> None:
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=100, total_tokens=1100, cached_prompt_tokens=200)
        pricing = ModelTokenPricing(
            provider="azure_openai",
            model="gpt-example",
            deployment="article-extraction",
            prompt_per_million=Decimal("2.00"),
            cached_prompt_per_million=Decimal("0.50"),
            completion_per_million=Decimal("10.00"),
            effective_date="2026-06-05",
            source="test",
        )

        cost = estimate_token_cost(usage, pricing)

        self.assertEqual(cost.prompt_cost, Decimal("0.00160000"))
        self.assertEqual(cost.cached_prompt_cost, Decimal("0.00010000"))
        self.assertEqual(cost.completion_cost, Decimal("0.00100000"))
        self.assertEqual(cost.total_cost, Decimal("0.00270000"))

    def test_summarize_costs_adds_usage_and_costs(self) -> None:
        pricing = ModelTokenPricing(
            provider="azure_openai",
            model="gpt-example",
            prompt_per_million=Decimal("1.00"),
            completion_per_million=Decimal("4.00"),
        )
        first_usage = TokenUsage(prompt_tokens=100, completion_tokens=25, total_tokens=125, reasoning_tokens=5)
        second_usage = TokenUsage(prompt_tokens=200, completion_tokens=50, total_tokens=250, cached_prompt_tokens=20)
        entries = [
            UsageLedgerEntry(
                usage_id="u1",
                operation="extract_answer",
                provider=pricing.provider,
                model=pricing.model,
                usage=first_usage,
                pricing=pricing,
                cost=estimate_token_cost(first_usage, pricing),
            ),
            UsageLedgerEntry(
                usage_id="u2",
                operation="extract_answer",
                provider=pricing.provider,
                model=pricing.model,
                usage=second_usage,
                pricing=pricing,
                cost=estimate_token_cost(second_usage, pricing),
            ),
        ]

        summary = summarize_costs(entries)

        self.assertEqual(summary.request_count, 2)
        self.assertEqual(summary.prompt_tokens, 300)
        self.assertEqual(summary.completion_tokens, 75)
        self.assertEqual(summary.cached_prompt_tokens, 20)
        self.assertEqual(summary.reasoning_tokens, 5)
        self.assertEqual(summary.total_cost, Decimal("0.00060000"))

    def test_summarize_costs_rejects_mixed_currencies(self) -> None:
        usage = TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2)
        usd_pricing = ModelTokenPricing(
            provider="azure_openai",
            model="gpt-example",
            currency="USD",
            prompt_per_million=Decimal("1"),
            completion_per_million=Decimal("1"),
        )
        eur_pricing = ModelTokenPricing(
            provider="azure_openai",
            model="gpt-example",
            currency="EUR",
            prompt_per_million=Decimal("1"),
            completion_per_million=Decimal("1"),
        )

        entries = [
            UsageLedgerEntry(
                usage_id="u1",
                operation="extract_answer",
                provider=usd_pricing.provider,
                model=usd_pricing.model,
                usage=usage,
                pricing=usd_pricing,
                cost=estimate_token_cost(usage, usd_pricing),
            ),
            UsageLedgerEntry(
                usage_id="u2",
                operation="extract_answer",
                provider=eur_pricing.provider,
                model=eur_pricing.model,
                usage=usage,
                pricing=eur_pricing,
                cost=estimate_token_cost(usage, eur_pricing),
            ),
        ]

        with self.assertRaisesRegex(ValueError, "mixed currencies"):
            summarize_costs(entries)


if __name__ == "__main__":
    unittest.main()
