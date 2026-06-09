# Validation

## Proof Strategy

This story is done when the repo has deterministic proof that a platform
session can be onboarded from the local Web UI, persisted locally by the
application, and reused by a later posting run.

Proof must show:

- the UI can start login or refresh for a supported platform
- successful onboarding persists reusable local session state
- later posting or status-check flows load the saved session first
- invalid or expired sessions surface `login-required` clearly
- no raw passwords are written into workbook, logs, or source-controlled files

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Session state mapping, readiness presenters, and session-validation result formatting. |
| Integration | UI handler to session-store flow, proving login completion persists state and later queries or posting flows reuse it. |
| E2E | Manual or browser-driven proof that an operator logs in from the UI once and later posting reuses the saved session. |
| Platform | Local runtime proof for visible login flow, session persistence, and reuse across separate runs. |
| Performance | Session checks stay lightweight enough for normal local operator workflows. |
| Logs/Audit | Session onboarding, validation, reuse, and failure paths emit actionable events without leaking secrets. |

## Fixtures

Repeatable fixtures should include:

- at least one supported platform test path
- a local session artifact store used only for tests
- a valid saved-session case
- an expired or cleared-session case returning `login-required`

## Commands

Add commands after scripts exist.

```text
python3 -m unittest discover tests
scripts/bin/harness-cli story update --id US-011 --unit 1 --integration 1 --e2e 1 --platform 1
```

## Acceptance Evidence

Add results after verification.
