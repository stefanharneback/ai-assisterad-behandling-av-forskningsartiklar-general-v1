# Review Reports

This folder stores structured review reports for implementation slices.

## File Names

Use this pattern:

```text
<reviewer>-Review--YYYY-MM-DD-HHMM--short-description.md
```

`<reviewer>` is the agent or person who ran the review, so authorship is visible
in the filename — for example `Claude-Review--…` or `Codex-Review--…`. Use the
local timezone for the timestamp. Keep the short description lowercase and
hyphen-separated.

## Report Shape

Use this order:

1. Findings, ordered Critical, High, Medium, Low.
2. Open questions or assumptions.
3. Change summary.
4. Verification performed.
5. Known gaps and recommended next steps.

Findings must include:

- file and line reference
- risk or failure mode
- suggested fix

If no issues are found, say that explicitly and still record verification and
remaining risk.

## Review Packet Expected From Implementer

The reviewer should receive:

- scope of the slice
- git range or diff
- changed contracts, including models, Command Line Interface (CLI), JSON, CSV (Comma-Separated Values) or environment variables
- verification results
- known deferred work
- questions for the reviewer

General review is acceptable for small documentation edits. Code, data-contract
or pipeline behavior changes should use the structured packet.
