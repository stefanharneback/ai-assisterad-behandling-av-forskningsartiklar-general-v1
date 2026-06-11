# ADR 0002 - Core Record Contract

## Decision

The canonical article record uses these contracts from M0 onward:

- `doc_id` is the full SHA-256 hash of the PDF bytes.
- One `Article` can have multiple `ArticleSource` entries when identical PDF bytes appear in multiple corpus folders.
- Authors are first-class records through `Author` and `Authorship`, not only free-text name lists.
- `Article.text_layer` exists from the start with `text`, `scanned` or `unknown`.
- `ArticleRecord` is the canonical reusable document artifact. It stores `Article`,
  normalized `full_text`, a page map, sections, chunks, references and external
  works.
- Section and chunk `start_offset` / `end_offset` values are offsets into
  `ArticleRecord.full_text`; a record must therefore be able to resolve its own
  provenance without re-reading the PDF.
- Run-scoped `Answer` and `Evidence` objects do not live inside `ArticleRecord`.
  They belong to later question/output artifacts such as `results.jsonl`,
  `run.sqlite` or an answer set for a run.
- `Answer` has an explicit scope and zero or more `doc_ids`; exact support still lives in `Evidence`.
- Reference edge tables use `article_references`, not `references`, to avoid reserved SQL (Structured Query Language) identifier conflicts.

## Rationale

The architecture depends on stable article identity, reusable records and reliable joins for shared authors and citation analysis. File paths and database folders are source metadata, not article identity. Author disambiguation requires stable author IDs from sources such as OpenAlex and ORCID (Open Researcher and Contributor ID) once enrichment is implemented.
The canonical document artifact must be reusable across question sets. Keeping
full text and page offsets in the record makes provenance auditable from the
JSON alone, while keeping answers outside the record preserves the separation
between one-time document processing and repeated question runs.
Answers can be scoped to one article, a whole corpus, a run, or a comparison between articles, so a single mandatory `doc_id` would make corpus-level questions awkward. `doc_ids` records the articles materially involved in the answer. `Evidence.doc_id` and its provenance fields remain the precise citation trail for the answer's individual claims.

## Consequences

- Discovery deduplicates byte-identical PDFs and preserves every source path.
- M1 must detect or leave `text_layer="unknown"` explicitly; later parsing can refine it. M1 collapses both an unreadable file and an openable-but-undetermined file to `unknown`; M2 adds per-file diagnostics to tell these apart.
- M3/M4 can join author and reference data without relying only on display names.
- M5/M6 can store article-level answers and corpus-level answers with the same
  answer model, but in run-scoped outputs rather than in canonical article
  records.
- Future SQL schemas should use explicit, non-reserved table names such as `article_references`.
