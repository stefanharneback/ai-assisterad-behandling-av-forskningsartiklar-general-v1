# Review Process

This repository moves fastest when work is split into small, reviewable slices
with explicit verification before each commit.

## Slice Size

A slice should be small enough that a reviewer can understand it in 5-15
minutes. Prefer one coherent behavior or contract change per commit.

Good examples:

- `M2: add text-layer diagnostics to article records`
- `M2: improve roman-numbered section heading detection`
- `M4: create initial relational index schema`

Avoid mixing parser behavior, output format changes and unrelated cleanup in the
same slice.

## Verification Gate

Before every commit that changes code, run the project gate:

```powershell
.\scripts\check.ps1
```

It runs the full gate from the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src tests
```

For parser, ingest or output changes, also run the corpus smoke test against a
temporary output directory:

```powershell
.\scripts\check.ps1 -Smoke
```

This appends the corpus smoke test to the gate:

```powershell
$out = Join-Path $env:TEMP "article-analysis-general-smoke"
.\.venv\Scripts\python.exe -m article_analysis_general.cli ingest --corpus Forskning --out $out --parse-local
```

Do not commit generated run folders, research PDFs, local caches or API keys.

## Review Cadence

Request a structured review after either:

- 2-4 related commits
- one changed public contract, such as models, Command Line Interface (CLI), JSON output or `inventory.csv`
- one milestone boundary, such as moving from M2 parsing to M3 metadata
- any change that affects provenance, `doc_id`, costs or SQL (Structured Query Language) behavior

Use a shorter ad-hoc review only for trivial documentation-only edits.

## Review Packet

Give the reviewer this context:

```text
Scope:
What this slice was meant to solve.

Git range:
The commits or diff to review.

Changed contracts:
Models, CLI flags, output files, schemas or environment variables.

Verification:
Commands run and their results.

Known gaps:
Conscious omissions or deferred work.

Questions:
Specific areas where reviewer judgement is requested.
```

## Review Output

Structured reviews are saved under `docs/reviews/`. Findings come first and are
ordered by severity:

- Critical: likely data loss, incorrect extraction identity, broken provenance or unusable pipeline state.
- High: behavior is wrong for normal use or blocks the next milestone.
- Medium: meaningful maintainability, test or contract risk.
- Low: polish, documentation drift or small follow-up.

Each finding should include file and line evidence, risk, and a suggested fix.
