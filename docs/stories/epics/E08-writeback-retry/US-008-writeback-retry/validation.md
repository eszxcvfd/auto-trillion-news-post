# Validation

## Proof Strategy

This story is done when the repo has deterministic proof that Pipeline B can
persist posting outcomes into the business workbook safely without corrupting
other platform lines or hiding write failures.

Proof must show:

- per-platform `Link Post` mutation preserves other lines
- same-platform retry replaces only the target line
- backup behavior runs before mutation when enabled
- locked or unwritable workbook states fail clearly
- write-back failures do not silently succeed or partially overwrite data

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Serialize one platform result line; replace only target platform line; preserve other lines; reject malformed `Link Post`; classify retry overwrite for same platform. |
| Integration | Update fixture `Trillion $ news.xlsx` rows and confirm exact `Link Post` preservation; create backup when enabled; simulate locked/unwritable workbook and verify explicit error behavior. |
| E2E | Optional manual CLI proof once Pipeline B mutation commands exist, showing row/platform result visibility after write-back. |
| Platform | Not required; workbook mutation service should stay independent of Playwright adapters. |
| Performance | Repeated row updates should remain acceptable for normal operator workbook sizes. |
| Logs/Audit | Verify write-back attempts emit sheet/row/platform context plus backup or lock failure reasons. |

## Fixtures

Repeatable fixtures should include:

- a workbook row with multiple existing platform lines
- a retry case where the same platform line is replaced
- a malformed `Link Post` row
- backup-enabled configuration
- a simulated locked or permission-denied workbook scenario

## Commands

Add commands after scripts or tests exist.

```text
python3 -m unittest discover tests
scripts/bin/harness-cli story update --id US-008 --unit 1 --integration 1 --e2e 0 --platform 0
```

## Acceptance Evidence

Add results after verification.
