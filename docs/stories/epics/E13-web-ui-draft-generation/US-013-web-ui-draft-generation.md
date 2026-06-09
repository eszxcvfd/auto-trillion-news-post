# US-013 Web UI Draft Generation

## Status

implemented

## Lane

normal

## Product Contract

The local Web UI must let the operator trigger a new harvest-and-draft run
without dropping to the CLI. The Web UI action must call the same draft
pipeline already used by the CLI and scheduler, record a durable run-history
entry, and make progress/outcome visible from the operator surface.

## Relevant Product Docs

- `docs/product/overview.md`
- `docs/product/release-boundaries.md`
- `docs/product/workbook-contracts.md`

## Acceptance Criteria

- The Web UI includes an operator-visible action to start a new harvest and
  draft generation run.
- The action reuses the shared draft pipeline instead of re-implementing search,
  workbook write, or draft generation rules in the route handler.
- The Web UI surfaces the returned run identifier and latest status so the
  operator can track progress without opening the CLI.
- Manual draft runs are stored in run history with durable status and summary
  evidence.
- The UI rejects overlapping manual draft runs with a clear operator-facing
  error.

## Design Notes

- Commands:
  `execute_run(...)` through a scheduler-backed manual run helper.
- Queries:
  existing run-history endpoints for status polling and operator visibility.
- API:
  `POST /api/drafts/run`
- Tables:
  `runs`
- Domain rules:
  preserve the business workbook as the single operator-facing source of truth.
- UI surfaces:
  add a dedicated Web UI view for manual harvest-and-generate actions.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id <id> --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Scheduler helper records manual draft run results and overlap checks. |
| Integration | Flask route test proves the Web UI starts the shared pipeline through the scheduler-backed helper. |
| E2E | Manual browser check that the Draft Run view can start a run and expose the returned run id/status. |
| Platform | `python3 -m unittest discover tests` passes in the local environment. |
| Release | Operator can start draft generation from the Web UI without CLI-only intervention. |

## Harness Delta

- Added a dedicated story for the missing Web UI draft-generation flow.

## Evidence

- `python3 -m unittest discover tests`
