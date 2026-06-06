# Design

## Domain Model

No new business truth should be created for the Web UI.

The UI consumes existing domain/application concepts such as:

- business workbook rows
- posting candidates and plans
- platform session status
- per-row/per-platform posting results

UI-specific concepts may exist only as presentation models:

- `WorkbookSummaryView`
- `SheetSummaryView`
- `RowStatusView`
- `PlatformStatusView`

Business rules remain owned by the shared application layer.

## Application Flow

Main command/query candidates exposed to the UI:

- query: `inspect_business_workbook`
- query: `list_posting_candidates`
- query: `get_session_status`
- command: `run_supported_platform_posting`
- command: `write_post_result` or later write-back commands

Expected application flow:

1. the web route receives operator input
2. the interface layer maps it into application commands or queries
3. the shared application core executes workbook, planning, or posting logic
4. the UI presenter converts the result into operator-facing status views

The Web UI must call the same core as the CLI. It must not implement its own
posting eligibility, workbook parsing, or mutation logic.

## Interface Contract

Expected web interface behavior:

- local routes for workbook overview, sheet detail, session status, and job
  trigger actions
- response DTOs or presenter models for rows, plans, and outcomes
- explicit rendering of errors such as malformed workbook state, login-needed
  status, or locked-workbook write failures

Expected error classes:

- workbook missing or unreadable
- no active workbook selected
- session unavailable or login-required
- planning/posting command failure
- workbook mutation or backup error from shared services

## Data Model

No application database is required for the first usable UI.

Storage touched through shared services:

- read workbook summaries and row states
- read session state
- optionally trigger posting and write-back commands

If a local SQLite job/history store exists later, the UI should read it through
application queries rather than directly.

## UI / Platform Impact

UI expectations for MVP:

- workbook selection or active workbook visibility
- sheet list and row summary visibility
- row/platform outcome visibility
- session/login status visibility
- operator-triggered posting and dry-run actions

The UI remains a local operator tool, not a public website.

## Observability

Every meaningful UI-triggered action should emit:

- `run_id` or `request_id`
- `action`
- `sheet_name` when applicable
- `row_id` when applicable
- `platform` when applicable
- `status`
- `message`

Useful UI-surface events include:

- workbook selected
- sheet viewed
- session status refreshed
- dry-run requested
- posting job triggered
- write-back failure surfaced to operator

## Alternatives Considered

1. Build the Web UI as a separate logic path from the CLI.
   Rejected because it would duplicate product rules, drift from the CLI, and
   threaten the single-source-of-truth architecture.
