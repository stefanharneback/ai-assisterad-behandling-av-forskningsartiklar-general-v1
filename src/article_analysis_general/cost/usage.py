from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


COST_QUANTUM = Decimal("0.00000001")
TOKENS_PER_MILLION = Decimal("1000000")


class TokenUsage(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    cached_prompt_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)


class ModelTokenPricing(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    provider: str
    model: str
    deployment: str | None = None
    currency: str = "USD"
    prompt_per_million: Decimal = Field(ge=0)
    completion_per_million: Decimal = Field(ge=0)
    cached_prompt_per_million: Decimal | None = Field(default=None, ge=0)
    effective_date: str | None = None
    source: str | None = None


class CostEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    currency: str = "USD"
    prompt_cost: Decimal = Field(default=Decimal("0"), ge=0)
    cached_prompt_cost: Decimal = Field(default=Decimal("0"), ge=0)
    completion_cost: Decimal = Field(default=Decimal("0"), ge=0)
    total_cost: Decimal = Field(default=Decimal("0"), ge=0)


class UsageLedgerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    usage_id: str
    operation: str
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
    provider: str
    model: str
    deployment: str | None = None
    run_id: str | None = None
    doc_id: str | None = None
    question_id: str | None = None
    prompt_version: str | None = None
    response_id: str | None = None
    usage: TokenUsage
    pricing: ModelTokenPricing
    cost: CostEstimate


class CostSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    currency: str
    request_count: int = Field(ge=0)
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cached_prompt_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(ge=0)
    total_cost: Decimal = Field(ge=0)


def token_usage_from_response_usage(usage: Mapping[str, object]) -> TokenUsage:
    prompt_details = _optional_mapping(usage, "prompt_tokens_details")
    completion_details = _optional_mapping(usage, "completion_tokens_details")

    return TokenUsage(
        prompt_tokens=_int_field(usage, "prompt_tokens"),
        completion_tokens=_int_field(usage, "completion_tokens"),
        total_tokens=_int_field(usage, "total_tokens"),
        cached_prompt_tokens=_int_field(prompt_details, "cached_tokens") if prompt_details is not None else 0,
        reasoning_tokens=_int_field(completion_details, "reasoning_tokens") if completion_details is not None else 0,
    )


def estimate_token_cost(usage: TokenUsage, pricing: ModelTokenPricing) -> CostEstimate:
    cached_prompt_tokens = min(usage.cached_prompt_tokens, usage.prompt_tokens)
    prompt_tokens = usage.prompt_tokens - cached_prompt_tokens
    cached_prompt_rate = pricing.cached_prompt_per_million or pricing.prompt_per_million

    prompt_cost = _price_tokens(prompt_tokens, pricing.prompt_per_million)
    cached_prompt_cost = _price_tokens(cached_prompt_tokens, cached_prompt_rate)
    completion_cost = _price_tokens(usage.completion_tokens, pricing.completion_per_million)
    total_cost = _quantize_cost(prompt_cost + cached_prompt_cost + completion_cost)

    return CostEstimate(
        currency=pricing.currency,
        prompt_cost=prompt_cost,
        cached_prompt_cost=cached_prompt_cost,
        completion_cost=completion_cost,
        total_cost=total_cost,
    )


def summarize_costs(entries: Iterable[UsageLedgerEntry]) -> CostSummary:
    entries_list = list(entries)
    currency = entries_list[0].cost.currency if entries_list else "USD"
    for entry in entries_list:
        if entry.cost.currency != currency:
            raise ValueError("Cannot summarize costs with mixed currencies")

    return CostSummary(
        currency=currency,
        request_count=len(entries_list),
        prompt_tokens=sum(entry.usage.prompt_tokens for entry in entries_list),
        completion_tokens=sum(entry.usage.completion_tokens for entry in entries_list),
        total_tokens=sum(entry.usage.total_tokens for entry in entries_list),
        cached_prompt_tokens=sum(entry.usage.cached_prompt_tokens for entry in entries_list),
        reasoning_tokens=sum(entry.usage.reasoning_tokens for entry in entries_list),
        total_cost=_quantize_cost(sum((entry.cost.total_cost for entry in entries_list), Decimal("0"))),
    )


def _price_tokens(tokens: int, per_million: Decimal) -> Decimal:
    return _quantize_cost(Decimal(tokens) * per_million / TOKENS_PER_MILLION)


def _quantize_cost(cost: Decimal) -> Decimal:
    return cost.quantize(COST_QUANTUM)


def _optional_mapping(data: Mapping[str, object], key: str) -> Mapping[str, object] | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError(f"{key} must be a mapping")
    return value


def _int_field(data: Mapping[str, object], key: str) -> int:
    value = data.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    if value < 0:
        raise ValueError(f"{key} must be non-negative")
    return value
