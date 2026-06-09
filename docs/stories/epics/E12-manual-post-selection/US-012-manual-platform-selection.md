# US-012 Manual Platform Selection for `post`

## Status

implemented

## Lane

normal

## Product Contract

When the operator triggers a manual `post` action for a business-workbook row,
the application must execute posting for exactly one selected platform.

This story makes the manual posting contract explicit across CLI and Web UI:

1. The operator can target one specific platform for the selected row.
2. The system must validate that the chosen platform is eligible for posting on
   that row.
3. The action must launch browser automation only for the chosen platform.
4. The action must not automatically post any other eligible platform from the
   same row.
5. Result write-back must continue to mutate only the selected platform line in
   `Link Post`.

If only one eligible platform exists for the row, the surface may continue
directly without an extra selection step, as long as the action still resolves
to one `row x platform` pair.

## Relevant Product Docs

- `docs/product/overview.md`
- `docs/product/workbook-contracts.md`
- `docs/product/release-boundaries.md`
- `SPEC.md`

## Acceptance Criteria

- Given a row has multiple eligible platform drafts, when the operator triggers
  manual `post`, then the system lets the operator choose one target platform
  and runs posting only for that platform.
- Given a row has exactly one eligible platform draft, when the operator
  triggers manual `post`, then the system may proceed directly with that single
  platform.
- Given the chosen platform has no usable draft content or is not eligible
  under the selective-posting rules, when manual `post` starts, then the system
  returns clear feedback and does not trigger posting for any other platform.
- Given the operator selected one platform, when the posting flow completes,
  skips, or fails, then only that platform's state in `Link Post` may change.
- Given the row still has other eligible platforms after one manual `post`
  action finishes, when the operator returns later, then those remaining
  platforms are still available for future posting actions.

## Design Notes

- Commands:
  `main.py post` remains a single manual posting entrypoint, but each
  invocation must resolve to one explicit platform target.
- Queries:
  reuse workbook ingestion plus row/platform eligibility logic from the shared
  posting core before starting browser automation.
- API:
  Web UI posting endpoints continue to accept a `platform` argument and should
  support selection before launching the background posting job.
- Domain rules:
  the manual posting unit of work is one `row x platform` pair, not one row
  across every populated draft column.
- UI surfaces:
  CLI may accept a platform argument or prompt when needed; Web UI may show a
  platform picker when more than one eligible draft exists.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-012 --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Eligibility and selection tests show that manual posting resolves to one chosen `row x platform` pair and rejects ineligible targets. |
| Integration | CLI and Web UI tests show that posting dispatch receives only the selected platform and does not fan out to sibling drafts on the same row. |
| E2E | Optional manual smoke proof from CLI or Web UI showing a row with multiple drafts where only the chosen platform launches browser automation. |
| Platform | Not required beyond the already supported platform automation path because this story changes selection and dispatch behavior. |
| Release | The accepted contract for manual posting explicitly supports per-platform choice on a row with multiple drafts. |

## Harness Delta

- Added US-012 story packet for manual per-platform posting selection.
- Backlog/release mapping should treat this as an operator-surface story, not
  as new platform support.

## Evidence

- Added `list_eligible_platforms` and `resolve_manual_post_target` in `src/posting_core.py`.
- CLI `post` now resolves one eligible `row x platform` pair, prompts when multiple
  eligible platforms exist, and rejects ineligible targets.
- Web UI `/api/post` validates eligibility before dispatch; workbook inspect
  exposes `eligible_platforms` for the platform picker.
- Tests: `tests/test_posting_core.py` (selection/eligibility unit tests) and
  `tests/test_web_ui.py` (inspect + post dispatch integration tests).
- Full suite passes with `.venv/bin/python -m unittest discover tests`.
