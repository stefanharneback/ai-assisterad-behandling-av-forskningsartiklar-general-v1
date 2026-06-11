# Local Development

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Checks

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src tests
```

For parser, ingest or output changes, run a corpus smoke test to a temporary
directory:

```powershell
$out = Join-Path $env:TEMP "article-analysis-general-smoke"
.\.venv\Scripts\python.exe -m article_analysis_general.cli ingest --corpus Forskning --out $out --parse-local
```

## Local data

Do not commit PDF corpora, generated run folders, extracted records, API keys or temporary files. Use these ignored paths:

- `Forskning/`
- `data/raw/`
- `data/extracted/`
- `data/records/`
- `runs/`
- `tmp/`
