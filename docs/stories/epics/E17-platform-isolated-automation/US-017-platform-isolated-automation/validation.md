# Validation

## Proof Strategy

This story is done when the repo has a validated plan for isolating platform
automation workflows without weakening workbook truth, session boundaries, or
operator-visible result semantics.

Proof must show:

- one platform workflow can change without requiring behavior changes in
  unrelated platforms
- shared workbook eligibility and write-back rules remain intact
- Web UI, CLI, and scheduler keep dispatching per platform
- logs and run history can attribute failures to a single platform workflow

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | platform capability and workflow selection tests per supported platform |
| Integration | CLI, Web UI, and scheduler dispatch each reach the correct platform workflow |
| E2E | manual smoke for at least one platform from each release group without cross-platform side effects |
| Platform | `.venv/bin/python -m unittest discover tests` plus targeted posting adapter suites |
| Performance | one platform failure does not block unrelated platform planning/execution |
| Logs/Audit | run history and logs identify the failing platform workflow explicitly |

## Fixtures

Repeatable fixtures should include:

- workbook rows with one eligible platform and multiple eligible platforms
- valid and invalid saved sessions per platform
- image-required and text-only rows
- one selector-failure case isolated to a single provider

## Commands

```text
.venv/bin/python -m unittest discover tests
```

## Acceptance Evidence

- Added `src/platform_workflows/` with registry dispatch, LinkedIn and Facebook
  owned workflows, and profile-based workflows for the remaining supported
  platforms.
- `src/platform_posting.py` now acts as a compatibility facade over the registry.
- Scheduler `run_details` stores `workflow_id` for posting outcomes.
- `.venv/bin/python -m unittest discover tests` passed with 140 tests on
  2026-06-09, including new `tests/test_platform_workflows.py`.
