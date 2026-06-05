# ADR 0003 - Cost and Token Usage Contract

## Decision

LLM (Large Language Model) and embedding calls must produce one usage ledger entry
per provider request from M1 onward. Each entry stores:

- operation, run, article and question identifiers when available
- provider, model, deployment and prompt version
- prompt, completion, total, cached prompt and reasoning token counts
- a pricing snapshot in USD (United States dollar) or the configured currency
- estimated request cost calculated from the stored usage and pricing snapshot

Reasoning tokens are tracked for audit and optimization. They are not charged as
a separate line item by default because they are included in completion tokens in
current Azure OpenAI usage reporting. Cached prompt tokens use a separate rate
only when a pricing snapshot provides one; otherwise they fall back to the normal
prompt-token rate.

## Rationale

Costs cannot be reconstructed reliably from prompts alone. Provider prices and
deployment choices can change over time, while completed runs must stay
auditable. Persisting raw token usage and the exact price snapshot used for the
estimate makes run manifests reproducible and lets later reporting aggregate by
run, article, question, model or operation.

## Consequences

- No future Azure OpenAI or OpenAI call should be added without usage logging.
- The run manifest should include a cost summary derived from the ledger.
- `AI_MODEL_PRICING_JSON` can override or pin the pricing snapshot used in local
  runs.
- M6 still owns final output and quality assurance reporting, but cost capture is
  part of the baseline pipeline contract before the first real model calls.
