# ADR 0004 - Separate Canonical Document Record From Run-Scoped Answers

- Status: Proposed (2026-06-11). Captures the design direction from
  [Claude-Review--2026-06-11-1422--design-consistency-and-contracts.md](../reviews/Claude-Review--2026-06-11-1422--design-consistency-and-contracts.md)
  (findings D1 and D2). Ratify or revise before building M5 (question engine) or
  M6 (output).

## Context

The architecture's core idea is to decouple documents from questions: process
each article once into a reusable representation, then run any question set
against it cheaply and repeatedly
([alternativ-plan-v1.md](../architecture/alternativ-plan-v1.md)). Two aspects of
the current `ArticleRecord` work against that:

- D1: `ArticleRecord` embeds run-scoped `answers` and `evidence`. A new question
  set would rewrite the canonical per-article artifact, which the architecture is
  designed to avoid, and it scatters run output across one file per article
  instead of the planned `results.jsonl` / `run.sqlite` / `Resultat.xlsx`.
- D2: The canonical record persists no normalized full text or page map, although
  the architecture names both as part of it and the M5 long-context method needs
  whole-article text. Section and chunk `start_offset` / `end_offset` reference a
  full-text string that is not stored, so offset-level provenance does not
  round-trip from the JSON alone (page-level provenance survives).

Neither is breaking today: `answers` / `evidence` are never populated, and page
numbers are stored. Now — before M5/M6 build on the shape — is the cheap moment
to settle it.

## Decision

1. The canonical per-article record holds only the reusable document
   representation: identity, bibliography, authors/authorships, sections, chunks,
   references, external works, normalized full text and the page map. It is
   written once per ingest and refined by parse/enrich, not by question runs.
2. `answers` and `evidence` move out of the document record into a run-scoped
   output contract owned by M5/M6 (for example `results.jsonl` plus `run.sqlite`,
   keyed by `run_id`, `doc_id` and `question_id`).
3. The record gains a normalized `full_text` plus a persisted page map so that
   every provenance offset resolves to text without re-parsing the PDF. This
   becomes an explicit invariant: section and chunk offsets are positions within
   the stored `full_text`.

## Consequences

- Re-running a new question set never rewrites canonical document records; it
  only writes new run-scoped answer output. This realizes "process once, query
  many times".
- M5 long-context extraction has a single canonical text to send and to cite,
  and `Evidence` page/section/offset provenance is verifiable from stored data.
- `Provenance` keeps its current fields; the change is what gets persisted
  alongside it, not the shape of `Provenance` itself.
- Migration is low-cost now because `answers` / `evidence` are empty in practice;
  delaying past M5 would require reshaping populated artifacts.

## Open points to settle on ratification

- Exact storage layout for full text and page map: fields on `ArticleRecord`
  versus a sibling `text.json` per article.
- The run-scoped answer schema (ties to `Question.answer_schema`, review finding
  D3) and where it lives relative to the run manifest.
