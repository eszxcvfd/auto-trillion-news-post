# Validation

## Proof Strategy

This story is done when the repo has deterministic proof that a non-technical
operator can inspect workbook-driven state and trigger the main workflows
through a local Web UI that reuses the shared application core.

Proof must show:

- the UI can render workbook/sheet/row summaries from shared queries
- the UI can show platform session status
- the UI can trigger posting or dry-run commands through shared application
  services
- key operator-visible failures are surfaced clearly
- the UI does not require direct CLI use for the supported MVP surface

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Presenter/view-model formatting for workbook rows, per-platform status, and operator-visible error messages. |
| Integration | Route/handler tests proving the UI calls shared workbook, session, and posting commands rather than duplicating logic. |
| E2E | Manual or browser-driven proof that a local operator can select a workbook, inspect status, trigger a job, and see results. |
| Platform | Local runtime proof that the web server starts and responds correctly in the intended operator environment. |
| Performance | Basic responsiveness for normal workbook sizes and local operator usage. |
| Logs/Audit | Verify UI-triggered actions emit request/run identifiers and operator-relevant status messages. |

## Fixtures

Repeatable fixtures should include:

- a valid business workbook with multiple sheets
- rows representing success, skip, retryable, and error states
- at least one platform session requiring login
- one workbook or write-back error case surfaced through the UI

## Commands

Add commands after scripts or tests exist.

```text
python3 -m unittest discover tests
scripts/bin/harness-cli story update --id US-009 --unit 1 --integration 1 --e2e 1 --platform 1
```

## Acceptance Evidence

Add results after verification.
