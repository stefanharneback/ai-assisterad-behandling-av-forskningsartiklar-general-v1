# Codex Review - Current Status Before Next Slice

- Date: 2026-06-11 13:55 local time
- Scope: current repository status after M1 ingest, local M2 parsing baseline, text-layer diagnostics and review-process documentation
- Git status at review time: documentation changes uncommitted in the working tree; no generated run output under tracked paths
- Verification: full local test/type/lint gate plus corpus smoke test

## Findings

No Critical or High findings.

| ID | Severity | File / line | Finding | Risk | Suggested fix |
|---|---|---|---|---|---|
| F1 | Medium | [discovery.py:77](../../src/article_analysis_general/ingest/discovery.py#L77) | `inspect_text_layer()` returns as soon as `MIN_TEXT_LAYER_CHARS` is reached, so `text_char_count` is not the total extracted text length for text PDFs. | Inventory and future parser-quality reports can undercount text-heavy files and give reviewers a false diagnostic signal. | Continue through all pages, calculate total character count, then classify `text` versus `scanned` after the loop. Keep the early threshold only as a boolean if needed. |
| F2 | Medium | [local.py:277](../../src/article_analysis_general/parse/local.py#L277) | Heading classification accepts short body lines that exactly match aliases such as `result`, `discussion` or `reference` without checking heading shape. The corpus smoke test still shows likely oversegmentation in `2018_Special needs education.pdf` with 21 sections and repeated section types. | Downstream chunks can be split at false headings, which weakens provenance and long-context extraction quality. | Add a heading-shape guard, for example uppercase/title-case checks, font/layout evidence when available, or a parser-quality flag for repeated suspicious section types. Cover the 2018 case with a focused regression test. |

## Open Questions

- Should `text_char_count` be treated as a diagnostic total, or renamed if it remains a threshold-limited sample?
- Should local PyMuPDF sectioning remain the default M2 baseline, or should GROBID be introduced before more heuristics are added?

## Change Summary

- Added [docs/workflows/review-process.md](../workflows/review-process.md) with slice size, verification gate, review cadence, review packet and severity definitions.
- Added [docs/reviews/README.md](README.md) with report naming and expected report shape.
- Updated [AGENTS.md](../../AGENTS.md#L18) so future agents follow the same review cadence.
- Updated [README.md](../../README.md#L54) with the repository review workflow.
- Updated [docs/operations/local-dev.md](../operations/local-dev.md#L11) so local checks match the current project gate.

## Verification Performed

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src tests
```

Results:

- `pytest`: 43 passed
- `ruff check .`: passed
- `mypy src tests`: passed

Corpus smoke test:

```powershell
$out = Join-Path $env:TEMP 'article-analysis-general-review-smoke'
.\.venv\Scripts\python.exe -m article_analysis_general.cli ingest --corpus Forskning --out $out --parse-local
```

Result:

- article count: 46
- source count: 46
- text layers: 45 `text`, 1 `scanned`
- record format: `article_record`
- output path: temporary directory outside the repository

## Known Gaps And Recommended Next Steps

1. Fix F1 before building parser quality reporting, because that report should rely on total text length.
2. Address or explicitly accept F2 before using local sections as the main input to extraction prompts.
3. Commit the documentation slice separately from the next code slice.
4. Next implementation slice should be either `M2: make parser quality report explicit` or `M2: reduce heading false positives with corpus-backed tests`.
