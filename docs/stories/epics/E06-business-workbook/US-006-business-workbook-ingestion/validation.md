# Validation

## Proof Strategy

This story is done when the repo has deterministic proof that the business
workbook can be read safely without breaking the baseline internal workbook
flow.

Proof must show:

- header normalization works
- multi-sheet ingestion works
- title-based row filtering works
- content-cell normalization works
- missing `Link Post` does not block ingestion
- business workbook row modeling stays separate from the legacy internal
  workbook model

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Normalize headers; map required columns; treat whitespace and `.` as no content; preserve raw `Link Post` text; retain sheet/category context. |
| Integration | Read a fixture `Trillion $ news.xlsx` with multiple sheets and mixed-validity rows; verify skipped rows, parsed rows, and clear errors. |
| E2E | Not required for this story if CLI/UI surface is only wiring to the ingestion service without new user-visible posting behavior. |
| Platform | Not required; no browser automation should be introduced in this story. |
| Performance | Workbook sizes typical of operator use should ingest without excessive memory growth. |
| Logs/Audit | Verify ingest warnings and parse outcomes include sheet and row context. |

## Fixtures

Repeatable fixtures should include:

- one valid workbook with two sheets
- one sheet missing `Link Post`
- one sheet with whitespace-variant headers
- rows with empty draft cells and `.`
- rows missing title values
- one malformed workbook for parse-error proof

## Commands

Add commands after scripts or tests exist.

```text
python3 -m unittest discover tests
scripts/bin/harness-cli story update --id US-006 --unit 1 --integration 1 --e2e 0 --platform 0
```

## Acceptance Evidence

Add results after verification.
