# Claude Code instructions

This repository's working agreement is shared by all agents. The source of truth
is [AGENTS.md](AGENTS.md) — read it for invariants, working cadence, the review
process and writing conventions. It is imported below so Claude Code follows the
same rules as Codex.

@AGENTS.md

## Notes for Claude Code

- Run the verification gate with `./scripts/check.ps1` (add `-Smoke` for the
  corpus smoke test). It wraps `pytest`, `ruff check .` and `mypy src tests`
  from the `.venv` virtual environment.
- Save review reports under `docs/reviews/` as
  `<reviewer>-Review--YYYY-MM-DD-HHMM--short-description.md`, using
  `Claude-Review--…` when Claude runs the review so authorship stays visible in
  the filename.
- The test runner lives in `.venv`; the system Python lacks pytest, ruff and
  mypy.
