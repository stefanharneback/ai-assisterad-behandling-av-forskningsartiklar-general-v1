# Repository Instructions

This repository implements a general, reusable research-article analysis pipeline.

Primary architecture source: `docs/architecture/alternativ-plan-v1.md`.

Follow these constraints:

- Build from the new architecture, not from the previous repo's pipeline layout.
- Keep `doc_id` content-based: `sha256(file_bytes)`.
- Keep questions data-driven; avoid hardcoding question semantics by column number.
- Keep deterministic operations in SQL or typed Python code; use LLMs only for text interpretation.
- Every extracted answer must have provenance or an explicit `not_found` / low-confidence state.
- Do not commit research PDFs, run outputs, API keys or local caches.
- Spell out abbreviations on first use in each document or file, in parentheses,
  e.g. `DOI (Digital Object Identifier)`. Exempt: code identifiers and ubiquitous
  abbreviations (API, PDF, URL, HTTP, JSON, ID, AI).

