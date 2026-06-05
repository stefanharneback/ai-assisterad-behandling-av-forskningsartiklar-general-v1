# Local Development

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Checks

```powershell
python -m pytest
python -m ruff check .
python -m mypy src
```

## Local data

Do not commit PDF corpora, generated run folders, extracted records, API keys or temporary files. Use these ignored paths:

- `Forskning/`
- `data/raw/`
- `data/extracted/`
- `data/records/`
- `runs/`
- `tmp/`
