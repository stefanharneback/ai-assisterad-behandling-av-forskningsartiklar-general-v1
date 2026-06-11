# Claude Review - Design Consistency and Contract Readiness

- Date: 2026-06-11 14:22 local time
- Reviewer: Claude (Opus 4.8)
- Scope: design-level review answering six questions — plan/roadmap consistency,
  which contracts to stabilize, whether `ArticleRecord` is the right level, M2
  baseline vs. GROBID/OCR priority, risks before the query engine / Excel output,
  and test-suite sufficiency for the current phase.
- Git: `main` @ `e929dd1`, working tree clean.
- Companion: builds on
  [Claude-Review--2026-06-11-1411--repo-status-m2-readiness.md](Claude-Review--2026-06-11-1411--repo-status-m2-readiness.md)
  (findings H1/M1/M2/M3 referenced, not restated). The verification gates were
  green at this same HEAD and the tree is unchanged since; not re-run here.

## Design findings (new / sharpened)

| ID | Severity | File / line | Finding |
|---|---|---|---|
| D1 | High | [record.py:160-171](../../src/article_analysis_general/store/record.py#L160-L171) | `ArticleRecord` embeds run-scoped `answers` and `evidence` in the canonical per-article record, coupling the reusable document representation to question runs. |
| D2 | High | [record.py:160-171](../../src/article_analysis_general/store/record.py#L160-L171), [parse/record.py:18-20](../../src/article_analysis_general/parse/record.py#L18-L20) | The canonical record persists no normalized full text or page map, although the architecture names both as part of it and M5 long-context extraction needs whole-article text. Section/chunk offsets reference an unstored string. |
| D3 | Medium | [record.py:126-133](../../src/article_analysis_general/store/record.py#L126-L133) | `Question.answer_schema` is an opaque `str`; M5 structured output needs a validated schema shape. |
| D4 | Medium | (prioritization) | GROBID's real unlock is M3 references/metadata, not sectioning; OCR affects one file. Section-label quality is not on the long-context extraction critical path. |
| D5 | Low | [parse/record.py](../../src/article_analysis_general/parse/record.py), [store/record.py](../../src/article_analysis_general/store/record.py) | Two modules named `record.py` (models vs. builder) invite import confusion. |

---

## 1. Is the implementation consistent with alternativ-plan-v1.md and the roadmap?

**Mostly yes, with two structural divergences worth correcting now.**

Consistent and faithful:

- `doc_id = sha256(file_bytes)`, multi-source `Article`, first-class
  `Author`/`Authorship`, `Section`/`Chunk` with shared `Provenance`, `Answer`
  with scope + evidence, `Reference`/`ExternalWork`, and the reserved
  `article_references` table name all match the plan's entity model.
- Pipeline phasing matches: Fas 0 ingest (done), Fas 1 parse (local baseline +
  stubs), Fas 2-4 deferred behind clean `NotImplementedError` stubs that name
  their milestone.
- Method routing, cost ledger (ADR 0003), and run-manifest discipline are
  present as designed.

Divergences:

- **D2 - missing canonical full text + page map.** The plan states the canonical
  record holds "normaliserad fulltext + sidkarta, provenance (sid/offset) för
  allt" ([alternativ-plan-v1.md:54-57](../architecture/alternativ-plan-v1.md#L54-L57)).
  The implementation computes `full_text` and the `PageText` map in
  [local.py:111-136](../../src/article_analysis_general/parse/local.py#L111-L136)
  but discards both — `build_local_article_record` stores only sections and
  chunks ([parse/record.py:18-20](../../src/article_analysis_general/parse/record.py#L18-L20)).
  Consequence: the section/chunk `start_offset`/`end_offset` are offsets into a
  string that no longer exists in the artifact, so offset-level provenance does
  not round-trip from the JSON alone (page-level survives because page numbers
  are stored). This also leaves the M5 long-context method with no whole-article
  text to send except a lossy re-concatenation of heuristic sections.
- **D1 - answers/evidence embedded in the canonical record.** The plan's core
  idea is to *decouple documents from questions* — "Processa varje artikel en
  gång ... Kör sedan vilken frågeuppsättning som helst billigt och upprepat mot
  den" ([alternativ-plan-v1.md:29-32](../architecture/alternativ-plan-v1.md#L29-L32)).
  The canonical record list there is identity/biblio/sections/references/
  fulltext/provenance — not answers. Embedding `answers`/`evidence` in
  `ArticleRecord` means a new question set would rewrite the canonical per-article
  artifact, which is exactly what the architecture is designed to avoid. M6 also
  separately owns answer output (`results.jsonl`, `run.sqlite`,
  [implementation-roadmap.md:50-53](../implementation-roadmap.md#L50-L53)).

Neither divergence is breaking today (answers/evidence default to empty and are
never populated yet), which is precisely why now — before M5/M6 build on the
shape — is the cheap moment to fix them.

## 2. Which contracts should be stabilized before more code is built on them?

Stabilize these now (cheap pre-M5/M6, expensive after):

1. **`ArticleRecord` shape (D1).** Split the persisted artifact into a canonical
   document record (identity, biblio, sections, chunks, references, external
   works, full text, page map) and run-scoped answer output (answers + evidence)
   written by the query/output layer. Keep `ArticleRecord` as the document
   record; introduce a separate `AnswerSet`/run-scoped container for answers.
2. **Canonical full text + page map (D2).** Add `full_text` and a `pages`/page-map
   to the document record (or persist a sibling `text.json`). Make the contract
   explicit: are section/chunk offsets relative to this stored full text? Today
   they are dangling.
3. **`Provenance` round-trip guarantee.** Decide and document the invariant:
   "given a record, any provenance offset resolves to text without re-parsing the
   PDF." This is the architecture's acceptance criterion ("varje svar ska kunna
   spåras till artikel, sektion och textstycke") and currently cannot be met from
   the JSON alone.
4. **`Question.answer_schema` (D3).** Pick the representation (JSON Schema string
   vs. typed model) before `questions.yaml` lands, so the file has a real
   contract from day one.
5. **`inventory.csv` columns.** Already public; fine to keep, but freeze the
   header order and document that `text_char_count` semantics change with prior
   finding M1.

Stable enough, leave alone: `doc_id`, `Article` identity/source model, run
manifest, cost ledger (ADR 0003).

## 3. Is ArticleRecord the right level for the parser/enrich/output flow?

**Right as the unit; wrong in its current span.** One aggregate per article,
keyed on `doc_id`, is the correct grain for parse and enrich — both operate per
document and the record is the natural accumulation point as GROBID/Crossref/
OpenAlex fill in sections, references, authors and external works.

It is the wrong level for **output/answers**. Answers and evidence are produced
per run and per question set, across the whole corpus, and are re-generated when
questions change. Hanging them off each document record (D1) forces the canonical
artifact to be rewritten on every query run and scatters run output across 46
files instead of the planned `results.jsonl` / `run.sqlite` / `Resultat.xlsx`.

Recommendation: keep `ArticleRecord` as the parse/enrich aggregate, add the
missing full text + page map (D2), and move `answers`/`evidence` out into a
run-scoped output contract owned by M5/M6.

## 4. Is the M2 baseline sufficient to proceed, or should GROBID/OCR come first?

**Proceed on the baseline for the long-context path; prioritize GROBID for M3,
not primarily to fix sectioning; deprioritize OCR.**

Key insight that reframes the prior report's H1: the plan's chosen method for
per-article content extraction is **long-context over the whole article, not
chunked RAG** ([alternativ-plan-v1.md:137-140](../architecture/alternativ-plan-v1.md#L137-L140)).
That path needs reliable *full text + page map* (D2), not reliable section
labels. So H1 (heading false positives) is a real quality defect but it is **not
the blocker** for starting the question engine — D2 is.

Where each parser investment actually pays off:

- **GROBID — high value, M3 driver.** Its unlock is structured references +
  bibliographic metadata (title/author/year/DOI), which is the M3 critical path
  and also happens to give authoritative sections as a by-product. Prioritize it
  for references/metadata, with the local parser as fallback.
- **OCR — low priority.** Exactly one corpus file is scanned. A single-file
  manual or `ocrmypdf` pass is enough; do not build the OCR branch before M3.
- **Local sectioning — sufficient as a text/offset substrate**, not as a label
  source. Fix D2 first; treat H1 as quality hardening that can ride alongside or
  be subsumed by GROBID.

Net: do not block on GROBID/OCR to *start* M5 plumbing, but do land D2 first, and
schedule GROBID as the M3 entry point.

## 5. Which risks must be addressed before building the query engine or Excel output?

Before the **query engine (M5)**:

- D2 (full text + page map): the long-context method has nothing canonical to
  send and evidence offsets do not resolve. **Blocker.**
- D1 (answer/evidence placement): decide where answers live before writing the
  first one, or the storage path will need rework. **Blocker.**
- D3 (`answer_schema` shape): structured output needs a real schema. **Blocker.**
- Cost ledger is built (ADR 0003) but **not yet wired** to any call site; the
  first LLM call must create a ledger entry or the contract is violated on
  arrival. Wire it as part of the first extraction call.
- `questions.yaml` does not exist yet; the schema loader
  ([questions/schema.py](../../src/article_analysis_general/questions/schema.py))
  only validates unique IDs. Land the file + method routing before extraction.

Before **Excel output (M6)**:

- Provenance round-trip (item 3 above) must hold, since `Resultat.xlsx` requires
  per-cell page/section provenance.
- Prior finding M2 (chunk page provenance inherits the section span) should be
  fixed so evidence cites a real page, not a span.
- Decide the run-output contract (`results.jsonl` / `run.sqlite`) before the
  spreadsheet writer, so Excel is a projection of a stable store, not the store.

## 6. Is the test suite sufficient for the current phase?

**Sufficient for the contracts and ingest already shipped; thin exactly where the
current risk is.**

Good: 43 tests cover models, discovery/dedupe/text-layer, run/manifest
no-overwrite, cost math, CLI and inventory — the M0/M1 contracts are well
guarded, and `mypy --strict` is clean.

Gaps relative to where the code is heading:

- No corpus-level or adversarial parser test (heading false positives, tiny
  sections) — the riskiest module has only happy-path tests (prior L1).
- No test that offset provenance resolves (would have surfaced D2).
- No `full_text`/page-map persistence test (D2).
- No parse-failure-path test (prior M3).

For the *current* phase the suite is acceptable; before the next parser/contract
slice, add the adversarial parser test and a provenance round-trip test, since
those encode the two highest design risks.

---

## Recommended sequence (design-driven)

1. Stabilize the document record: add `full_text` + page map, move
   `answers`/`evidence` to a run-scoped output type, document the offset
   round-trip invariant (D1, D2). Land the provenance round-trip test with it.
2. Harden the local parser in place (prior H1/M1/M2 findings) — or fold into the
   GROBID slice if GROBID lands first.
3. GROBID adapter for M3 references + metadata, local parser as fallback;
   populate inventory title/year/doi.
4. Define `Question.answer_schema` shape + land `questions.yaml` with method
   routing (D3).
5. Wire the cost ledger into the first long-context extraction call so ADR 0003
   holds from the first real model request.

## Verification

Gates were green at this HEAD (`e929dd1`, clean tree) per the companion report:
`pytest` 43 passed, `ruff` clean, `mypy --strict` clean, corpus ingest 46/46.
This review is static/design analysis over the same tree and added no code.

## Known gaps in this review

- Recommendations on record splitting are design direction, not a prescribed
  schema; the exact field layout should be settled in a short ADR before the
  slice.
- No enrichment/query/output code was run (stubs); analysis is from reading.
