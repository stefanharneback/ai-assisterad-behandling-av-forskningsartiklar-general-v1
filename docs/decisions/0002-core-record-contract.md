# ADR 0002 - Core Record Contract

## Decision

The canonical article record uses these contracts from M0 onward:

- `doc_id` is the full SHA-256 hash of the PDF bytes.
- One `Article` can have multiple `ArticleSource` entries when identical PDF bytes appear in multiple corpus folders.
- Authors are first-class records through `Author` and `Authorship`, not only free-text name lists.
- `Article.text_layer` exists from the start with `text`, `scanned` or `unknown`.
- `Answer` has an explicit scope and zero or more `doc_ids`; exact support still lives in `Evidence`.
- Reference edge tables use `article_references`, not `references`, to avoid reserved SQL (Structured Query Language) identifier conflicts.

## Rationale

The architecture depends on stable article identity, reusable records and reliable joins for shared authors and citation analysis. File paths and database folders are source metadata, not article identity. Author disambiguation requires stable author IDs from sources such as OpenAlex and ORCID (Open Researcher and Contributor ID) once enrichment is implemented.
Answers can be scoped to one article, a whole corpus, a run, or a comparison between articles, so a single mandatory `doc_id` would make corpus-level questions awkward. `doc_ids` records the articles materially involved in the answer. `Evidence.doc_id` and its provenance fields remain the precise citation trail for the answer's individual claims.

## Consequences

- Discovery deduplicates byte-identical PDFs and preserves every source path.
- M1 must detect or leave `text_layer="unknown"` explicitly; later parsing can refine it.
- M3/M4 can join author and reference data without relying only on display names.
- M5/M6 can store article-level answers and corpus-level answers with the same model.
- Future SQL schemas should use explicit, non-reserved table names such as `article_references`.
