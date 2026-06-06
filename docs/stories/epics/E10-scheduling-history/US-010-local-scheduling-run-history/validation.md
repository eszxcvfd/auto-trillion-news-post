# Validation

## Proof Strategy

This story is done when the repo has deterministic proof that local schedules
can trigger shared workbook-based jobs and leave recoverable run history
without creating a second business source of truth.

Proof must show:

- schedule definitions can be created, updated, enabled, and disabled
- due schedules trigger the shared application workflow rather than a forked
  scheduler-only path
- run history records successful, partial, failed, and skipped outcomes
- operator-visible recovery information exists for failed or missed runs
- workbook truth, selective posting, and write-back guarantees remain intact

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Schedule parsing, next-run calculation, status transitions, and run-history summary formatting. |
| Integration | Scheduler service and local SQLite store with fake time, proving due jobs call shared posting/planning workflows and persist run results. |
| E2E | Local operator flow that creates a schedule, triggers a due run or run-now path, and inspects resulting history through the supported surface. |
| Platform | Local runtime proof that scheduler startup, shutdown, and background polling behave correctly on the operator machine. |
| Performance | Normal schedule counts and history queries stay responsive for local use. |
| Logs/Audit | Scheduled runs emit `run_id`, `schedule_id`, status, and actionable recovery messages with row/platform context when available. |

## Fixtures

Repeatable fixtures should include:

- a valid business workbook with eligible, skipped, and retryable rows
- a deterministic local SQLite test database
- a fake clock or controllable scheduler timing source
- stubbed run outcomes for success, partial failure, and login-required states
- at least one missing-workbook or locked-workbook failure case

## Commands

Add commands after scripts exist.

```text
python3 -m unittest discover tests
scripts/bin/harness-cli story update --id US-010 --unit 1 --integration 1 --e2e 1 --platform 1
```

## Acceptance Evidence

Add results after verification.
