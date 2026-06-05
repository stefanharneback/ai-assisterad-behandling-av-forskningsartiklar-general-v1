# Agent Instructions

General, reusable pipeline for AI-assisted evidence extraction from research
articles. Architecture source of truth: `docs/architecture/alternativ-plan-v1.md`.
Roadmap: `docs/implementation-roadmap.md`.

## Invariants

- Build from the new architecture, not the previous repo's pipeline.
- `doc_id` is content-based: `sha256(file_bytes)` — never path or filename.
- Keep questions data-driven (`questions.yaml` / Excel import), not hardcoded by column.
- Do deterministic work in SQL (Structured Query Language) or typed Python; use
  LLMs (Large Language Models) only for text interpretation.
- Every extracted answer carries provenance (article, section, page, quote) or an
  explicit `not_found` / low-confidence state.
- Do not commit research PDFs, run outputs, API keys or local caches.

## Writing

- Abbreviations — spell out on first use. The first time an abbreviation appears
  in any document or file (prose and code comments), write its expansion in
  parentheses, e.g. `DOI (Digital Object Identifier)`. One expansion per file is
  enough; later uses stay abbreviated. Exempt: code identifiers/symbols and
  ubiquitous abbreviations (API, PDF, URL, HTTP, JSON, ID, AI).
- Code, identifiers, commit messages and technical comments in English; Swedish
  is fine for user-facing documentation.
