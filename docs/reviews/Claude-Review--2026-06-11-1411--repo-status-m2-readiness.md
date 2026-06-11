# Claude Review - Repo Status and M2 Readiness

- Date: 2026-06-11 14:11 local time
- Reviewer: Claude (Opus 4.8)
- Scope: full repository status and quality review ahead of continued M2 parsing
  and upcoming M3 metadata. Covers roadmap-vs-implementation, data contracts,
  ingest/discovery, the local M2 parser, run output, test coverage, docs and
  forward risk (GROBID, OCR, metadata APIs, relational index, query engine).
- Git: `main` @ `e929dd1`, working tree clean.
- Filename note: this repo's `docs/reviews/README.md` specifies a
  `Codex-Review--` prefix; I use `Claude-Review--` to attribute authorship
  honestly (matching the existing `Claude-Review--2026-06-05` precedent and the
  global authoring rule). See finding L2 — the prefix convention should be
  reconciled.

## Summary verdict

The foundation is **stable and safe to build on**: content-based `doc_id`,
deduplication, robust Windows-path ingest, text-layer detection, the run
manifest/records/inventory output contract, and the cost ledger are all sound,
typed and tested. The corpus ingests cleanly end-to-end (46/46).

The one area that is **not yet ready to be trusted downstream** is local
heuristic sectioning. Section *offsets* are accurate, but section *labels*
(`normalized_type`) and *boundaries* are wrong on a majority of the corpus
(29/46 records show a repeated IMRaD section type; 13 records contain
sub-50-character "sections" split mid-sentence). Treat the local parser as a
text+offset substrate only — do not let M3/M5 route or extract on its section
types until this is fixed or GROBID supersedes it.

No Critical findings. One High, three Medium, three Low.

---

## Findings

### High

#### H1 - Heuristic heading detection mislabels and oversegments the majority of the corpus

- Evidence: [local.py:277-287](../../src/article_analysis_general/parse/local.py#L277-L287)
  (`_classify_heading`) and [local.py:258-274](../../src/article_analysis_general/parse/local.py#L258-L274)
  (`_find_headings`).
- A line is accepted as a heading whenever, after stripping a numbering prefix
  and trailing punctuation, it case-folds to a known alias — with no
  heading-shape guard. Any wrapped body word that lands at the start of a line
  (`methods`, `result`, `results`, `discussion`, `reference.`) becomes a section
  break.
- Corpus measurement (smoke run, 46 records):
  - 29/46 records contain a repeated typed section type (real IMRaD should not
    repeat `results` three times).
  - 13/46 records contain at least one section under 50 characters; 16 such
    sections total.
  - Worst case `2018_Special needs education.pdf`: 21 sections with the IMRaD
    order scrambled — e.g. section 4 heading `reference.` over body text
    "This paper constitutes a", section 9 heading `methods` over "of
    child-based funding exist", section 14 heading `results` with 3 characters
    of text ("and"). `Abstract` ("Summary") surfaces as section 12.
- Risk / failure mode: `normalized_type` is unreliable for ~two-thirds of the
  corpus and section boundaries fall mid-sentence. Any M3/M5 logic that routes
  by section type, feeds a labelled section to a long-context prompt, or derives
  evidence page ranges from a section will inherit wrong structure. This blocks
  using local sections as the extraction substrate.
- Why offsets are still OK (not Critical): start/end offsets and `doc_id`
  remain correct, so this is mislabelling, not data loss.
- Recommended action: add a heading-shape guard before accepting an alias —
  require the candidate to stand alone on its line, be preceded/followed by a
  blank line, carry case evidence (Title Case / UPPERCASE), and reject when the
  following text continues a sentence (starts lowercase). Add a focused
  regression test over the `2018_Special needs education.pdf` pattern and a
  corpus-level guard test (no typed section type repeats more than once without
  a parser-quality flag). Strongly consider bringing the GROBID adapter in as
  the authoritative sectioner before investing further in heuristics (see open
  question Q1). This was raised as Medium F2 in the prior review; the corpus
  measurement above is the basis for escalating it to High.

### Medium

#### M1 - `text_char_count` is a first-page sample, not a document total

- Evidence: [discovery.py:78-83](../../src/article_analysis_general/ingest/discovery.py#L78-L83).
  `inspect_text_layer` returns as soon as the running count reaches
  `MIN_TEXT_LAYER_CHARS` (32), so for any real text PDF it returns after the
  first page.
- Measurement: `1981_The Education of the.pdf` reports `text_char_count=2678`
  for a 195-page document; the parser produces 259 chunks from the same file.
  Inventory values cluster at first-page sizes (840-5290), uncorrelated with
  page count.
- Risk / failure mode: the column reads like a document text volume but is not.
  Any future "text density / how much was extracted / scanned-vs-thin" signal
  built on it will undercount, and reviewers get a false diagnostic.
- Recommended action: continue through all pages, total the characters, then
  classify `text` vs `scanned` after the loop (keep a boolean early-exit only if
  performance needs it). Alternatively rename the field to reflect a threshold
  sample. Add a test asserting the count reflects the whole document. (Prior
  review F1, still open.)

#### M2 - Chunk page provenance inherits the whole section's page span

- Evidence: [local.py:241-243](../../src/article_analysis_general/parse/local.py#L241-L243).
  Each chunk copies `page_start`/`page_end` from its parent section, so every
  chunk in a multi-page section reports the section's full page range rather
  than the chunk's own page(s).
- Risk / failure mode: M5/M6 evidence needs per-quote page provenance. A quote
  located via a chunk would cite the whole section's page span, weakening the
  "every answer traces to article, section, page, quote" acceptance criterion.
- Recommended action: derive each chunk's `page_start`/`page_end` from its own
  `start_offset`/`end_offset` via the existing `_page_number_for_offset`. The
  page map is already threaded into `chunk_sections` callers, so this is local.

#### M3 - Local parse failures are swallowed without a diagnostic

- Evidence: [parse/record.py:13-16](../../src/article_analysis_general/parse/record.py#L13-L16).
  A parse exception is caught, the record is marked `extraction_status="failed"`,
  and the error text is discarded. There is no parse-error field on the record
  (`Article` has `text_layer_error` but no parse analogue).
- Risk / failure mode: on the full corpus this path did not fire (all 45 text
  PDFs reached `ok`), but when it does there is no way to triage why a file
  failed. Silent broad `except Exception` also masks programming errors.
- Recommended action: capture the error string into a record field (mirroring
  `text_layer_error`) or log it, and add a regression test that drives the
  failure path. Narrow the except if practical.

### Low

#### L1 - No regression test guards the fragile parsing behavior

- Evidence: [tests/test_parse_local.py](../../tests/test_parse_local.py) asserts
  only good-case heading detection; nothing asserts resistance to body-word
  false positives, that `text_char_count` is a total, or the parse-failure path.
- Risk: the most fragile area (H1, M1, M3) has no guard, so regressions land
  silently.
- Recommended action: add the targeted tests alongside the fixes above.

#### L2 - Review-filename convention is inconsistent

- Evidence: [AGENTS.md:30](../../AGENTS.md#L30) and
  [docs/reviews/README.md:9-11](README.md#L9-L11) mandate `Codex-Review--`,
  while the global authoring rule and the existing
  `Claude-Review--2026-06-05-0734` report use `Claude-Review--`.
- Risk: low; cosmetic divergence and reviewer confusion.
- Recommended action: pick one prefix (or make it agent-neutral, e.g.
  `Review--`) and update AGENTS.md + the README together.

#### L3 - `Question.answer_schema` is unstructured free text

- Evidence: [record.py:132](../../src/article_analysis_general/store/record.py#L132)
  types `answer_schema` as `str`.
- Risk: low now (no question engine yet), but M5 structured output will need a
  validated schema shape, not an opaque string.
- Recommended action: defer, but decide the schema representation (e.g. JSON
  Schema string vs. a typed model) when M5 starts so questions.yaml has a
  contract.

#### L4 - README repo-status slightly overstates M2 readiness

- Evidence: [README.md:66](../../README.md#L66) describes the local baseline as
  extracting "text, sektioner och chunks" without noting that section labels are
  not yet reliable.
- Risk: low; a future contributor may over-trust local sections.
- Recommended action: add one sentence that local sectioning is a text+offset
  baseline pending GROBID, not an authoritative IMRaD split.

---

## Roadmap vs. implementation (alignment check)

| Milestone | Roadmap intent | Actual state | Verdict |
|---|---|---|---|
| M0 | Module skeleton, core models, doc_id, CLI, first tests | Present; models complete in [record.py](../../src/article_analysis_general/store/record.py) | Done |
| M1 | Recursive ingest, byte-dedupe to multi-source articles, JSON record per article, run manifest, cost-ledger groundwork, early inventory | All present and tested; cost ledger built but not yet wired to any call | Done |
| M2 | PyMuPDF text + sections + chunks with provenance; GROBID + fallback; per-file text-layer diagnostics; minimal `Resultat.xlsx` | Local PyMuPDF baseline done; GROBID/OCR/fallback are stubs; per-file diagnostics and `Resultat.xlsx` not started; sectioning quality is H1 | In progress |
| M3-M7 | Metadata APIs, relational index, query engine, output, RAG | Clean `NotImplementedError` stubs with milestone pointers | Not started (expected) |

The architecture in [alternativ-plan-v1.md](../architecture/alternativ-plan-v1.md)
and the entity model match the implemented Pydantic contracts well: `doc_id =
sha256(file_bytes)`, multi-source `Article`, first-class `Author`/`Authorship`,
`Section`/`Chunk` with `Provenance`, `Answer` with scope + evidence, and the
`article_references` naming reserved for M4 are all faithfully present.

## Data model and contracts

- Contracts are coherent, `extra="forbid"` everywhere, provenance is a shared
  type, and ADRs [0002](../decisions/0002-core-record-contract.md) /
  [0003](../decisions/0003-cost-and-token-usage-contract.md) document the
  intent. No contract defects found.
- Observations carried as findings: `answer_schema` typing (L3); `Article` has
  no parse-error field to complement `text_layer_error` (M3).

## Ingest / discovery

- Strong. Content-based `doc_id`, deduplication into multi-source articles,
  NFC-normalized relative paths, Windows extended-path prefix
  ([discovery.py:98-107](../../src/article_analysis_general/ingest/discovery.py#L98-L107)),
  and exception-to-`unknown` text-layer handling. The full corpus ingested
  46/46 with no `text_layer_error` and the single scanned file correctly
  flagged — the previously failing double-space/unicode filenames now open.
- Findings: M1 (text_char_count semantics). The roadmap's promised M2
  diagnostic that separates "opened but undetermined" from "could not open"
  (both still collapse to `unknown`) remains outstanding.

## Local M2 parser

- Text extraction, page offsets, section splitting, and overlap-aware chunking
  are well structured with accurate character offsets and a sensible
  paragraph/word split point. Roman-numbered and composite headings are handled.
- Findings: H1 (heading false positives / oversegmentation), M2 (chunk page
  provenance), M3 (swallowed failures).

## Output (records, manifest, inventory)

- Run manifest with no-overwrite auto run-id
  ([run.py:81-92](../../src/article_analysis_general/store/run.py#L81-L92)),
  one JSON record per article, and an `inventory.csv` exposing the result
  contract early. All write to a temp dir, nothing under tracked paths.
- `inventory.csv` `title`/`doi`/`published_year` are empty for all 46 (expected
  — populated by M2 parsing/M3 metadata). `text_char_count` column is affected
  by M1.

## Tests and verification

| Gate | Result |
|---|---|
| `pytest` | 43 passed |
| `ruff check .` | All checks passed |
| `mypy src tests` (strict) | Success, no issues in 40 source files |
| Corpus ingest `--parse-local` (46 PDFs) | 46 articles / 46 sources; text layers 45 `text`, 1 `scanned`; record_format `article_record`; written to `%TEMP%`, outside the repo |

Coverage is good on contracts, discovery, run/manifest, cost and CLI. Gap: no
test guards heading false positives, text_char_count totals, or the parse
failure path (L1).

## Open questions

- Q1: Should local PyMuPDF sectioning remain the M2 default, or should GROBID be
  introduced as the authoritative sectioner before more heuristics are added?
  Given H1's spread (29/46), GROBID-first is the lower-risk path and also
  unblocks M3 metadata/references — I'd lean that way rather than hardening the
  heuristic indefinitely.
- Q2: Is `text_char_count` meant as a diagnostic total (fix M1) or an
  intentional threshold sample (rename it)?
- Q3: OpenAlex now requires an API key (per the architecture note). Is a key
  available, or should M3 start with Crossref-only DOI resolution and defer the
  citation graph?

## What is ready to build on

- Ready now: data model/contracts, ingest/discovery, run manifest + records +
  inventory, cost ledger contract. Build directly on these.
- Use with caution: the local parser as a text + offset source only. Do not
  trust `normalized_type` or section boundaries downstream until H1 is resolved.
- Not started (clean stubs, expected): GROBID, OCR, Crossref/OpenAlex/Unpaywall,
  relational index, question engine, output matrix, RAG.

## Recommended next 3-5 implementation slices

1. M2 - heading-shape guard + corpus regression tests (fixes H1). Reject
   aliases that lack heading shape; add the `2018_Special needs education.pdf`
   regression and a corpus guard against repeated typed sections.
2. M2 - GROBID adapter behind the existing stub (TEI -> sections, references,
   title/author/year) with fallback chain to the local parser. Resolves H1 at
   the source and unblocks M3; begins populating inventory `title`/`year`.
3. M2 - parser hardening: make `text_char_count` a true document total (M1),
   add the per-file text-layer diagnostic promised in the roadmap/ADR 0002, and
   derive per-chunk page provenance from offsets (M2 finding).
4. M3 - Crossref DOI resolution from PDF metadata/text to fill `doi`/`title`/
   `published_year` in records and `inventory.csv` (all empty today),
   establishing the metadata contract before the OpenAlex citation graph.
5. M2/M6 seam - capture and surface parse errors (M3 finding) and emit a minimal
   parser-quality report (sections found, suspicious-heading flags, scanned/OCR
   queue) so quality is observable before extraction depends on it.

## Verification commands run

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src tests

$out = Join-Path $env:TEMP "article-analysis-general-review"
.\.venv\Scripts\python.exe -m article_analysis_general.cli ingest --corpus Forskning --out $out --parse-local
```

## Known gaps in this review

- Section-quality assessment is structural (type repeats, tiny sections,
  ordering), not a manual page-by-page check against the PDFs.
- No runtime behavior was exercised beyond ingest + local parse; enrichment,
  query and output paths are stubs and were read, not run.
