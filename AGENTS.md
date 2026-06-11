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

## Working cadence and reviews

- Work in small, reviewable slices. Prefer one coherent behavior or contract
  change per commit.
- Before code commits, run `pytest`, `ruff check .`, and `mypy src tests` from
  the project virtual environment.
- For ingest, parser or output changes, also run a corpus smoke test to a
  temporary output directory, not to committed paths.
- Request a structured review after 2-4 related commits, at milestone
  boundaries, or whenever models, Command Line Interface (CLI), JSON output,
  `inventory.csv`, provenance, cost tracking, `doc_id`, or SQL behavior changes.
- Save substantive review reports in `docs/reviews/` using the
  `Codex-Review--YYYY-MM-DD-HHMM--short-description.md` naming convention.
- Use `docs/workflows/review-process.md` as the source of truth for review
  packets, severity levels and verification gates.

## Writing

- Abbreviations — spell out on first use. The first time an abbreviation appears
  in any document or file (prose and code comments), write its expansion in
  parentheses, e.g. `DOI (Digital Object Identifier)`. One expansion per file is
  enough; later uses stay abbreviated. Exempt: code identifiers/symbols and
  ubiquitous abbreviations (API, PDF, URL, HTTP, JSON, ID, AI).
- Code, identifiers, commit messages and technical comments in English; Swedish
  is fine for user-facing documentation.
