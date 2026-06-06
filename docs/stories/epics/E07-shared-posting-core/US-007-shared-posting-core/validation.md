# Validation

## Proof Strategy

This story is done when the repo has deterministic proof that the shared
posting core can interpret business workbook state consistently before platform
submission and before workbook mutation.

Proof must show:

- `Link Post` parsing works for success, retryable, skip, and malformed states
- per-platform draft-content rules are enforced
- selective posting rules prevent duplicate posts
- default per-platform limit of 2 is enforced
- planning output is reusable for later platform adapters

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Parse `Link Post` lines into normalized states; detect malformed lines; classify duplicate-success, retryable, and no-content states; enforce per-platform limit logic. |
| Integration | Build posting plans from fixture business workbook rows across multiple sheets; verify selected candidates and skipped reasons for LinkedIn/Facebook/X. |
| E2E | Not required if this story stops at shared planning/core behavior and does not yet claim full user-visible post submission. |
| Platform | Optional smoke proof only for adapter handoff shape, not full posting behavior. |
| Performance | Planning should remain predictable for normal operator workbook sizes. |
| Logs/Audit | Verify planning and parse outcomes emit row/platform context and reasons. |

## Fixtures

Repeatable fixtures should include:

- rows with success URLs already present
- rows with `[posted-no-link]`
- rows with `[pending]`, `[error]`, and `[login-required]`
- rows with malformed `Link Post` lines
- rows with empty draft content and `.`
- enough rows per platform to prove the max-2 selection rule

## Commands

Add commands after scripts or tests exist.

```text
python3 -m unittest discover tests
scripts/bin/harness-cli story update --id US-007 --unit 1 --integration 1 --e2e 0 --platform 0
```

## Acceptance Evidence

Add results after verification.
