#!/usr/bin/env pwsh
# Project verification gate: pytest, ruff and mypy from the project virtual
# environment, with an optional corpus smoke test (-Smoke). This is the single
# source of truth for the gate referenced by AGENTS.md, the README and
# docs/workflows/review-process.md, so the commands do not drift across docs.

[CmdletBinding()]
param(
    [switch]$Smoke
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Virtual environment not found at $python. Create it with: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -e `".[dev]`""
}

function Invoke-Step {
    param(
        [string]$Name,
        [string[]]$Arguments
    )
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        Write-Error "$Name failed (exit $LASTEXITCODE)."
    }
}

Invoke-Step "pytest" @("-m", "pytest")
Invoke-Step "ruff check" @("-m", "ruff", "check", ".")
Invoke-Step "mypy src tests" @("-m", "mypy", "src", "tests")

if ($Smoke) {
    $out = Join-Path $env:TEMP "article-analysis-general-smoke"
    Invoke-Step "corpus smoke test -> $out" @(
        "-m", "article_analysis_general.cli", "ingest",
        "--corpus", "Forskning", "--out", $out, "--parse-local"
    )
}

Write-Host "All checks passed." -ForegroundColor Green
