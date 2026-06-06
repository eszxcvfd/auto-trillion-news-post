# Design

## Domain Model

Introduce scheduling-facing operational concepts while preserving existing
business truth:

- `ScheduleDefinition`
  local configuration for a recurring or one-shot job
- `ScheduledJobTarget`
  workbook-scoped job intent and allowed execution mode
- `RunRecord`
  one persisted execution attempt with timestamps and terminal status
- `RunOutcomeSummary`
  operator-facing counts and result classification for a completed run
- `RunStatus`
  statuses such as scheduled, running, completed, partial, failed, or missed

Business rules:

- schedules reference local workbook targets and shared commands; they do not
  copy workbook content into operational storage
- scheduled runs must execute the same planning and posting rules as manual
  CLI or Web UI runs
- run history stores operational metadata and summaries, not a second draft or
  posting-decision source of truth
- automatic runs must respect existing selective posting, backup, retry, and
  posting-limit rules
- failed, partial, and missed runs must remain visible for operator recovery

## Application Flow

Main command/query candidates:

- command: `create_schedule`
- command: `update_schedule`
- command: `pause_schedule`
- command: `run_schedule_now`
- command: `trigger_due_schedules`
- query: `list_schedules`
- query: `list_run_history`
- query: `get_run_history_detail`

Expected application flow:

1. the operator creates or updates a schedule tied to a workbook job target
2. the scheduler service loads due schedules from local operational storage
3. a due schedule invokes the same shared application workflow used by manual
   runs
4. run logging captures lifecycle, row/platform summaries, and terminal status
5. run history persists structured operational results for later inspection
6. CLI and future Web UI surfaces render schedule and history views from shared
   queries

The scheduler must orchestrate shared workflows. It must not duplicate posting,
workbook parsing, or write-back rules.

## Interface Contract

Expected interface behavior:

- CLI support for schedule creation, listing, pause/resume, and history
  inspection
- shared presenter/query models that future Web UI pages can reuse
- explicit visibility for next run, last run, last status, and last error
  summary
- clear operator messaging when a run is skipped, partial, failed, or blocked

Expected error classes:

- invalid or missing workbook target
- invalid schedule definition
- scheduler unavailable or disabled
- concurrent run conflict
- shared posting workflow failure
- operational store read/write failure

## Data Model

Operational storage follows `docs/decisions/0009-local-runtime-and-operational-storage.md`.

Expected local SQLite responsibilities:

- schedule definitions
- enabled/disabled state
- run-history summaries
- optional structured event or error records needed for recovery

Boundary rules:

- SQLite supports operations and observability only
- Excel remains the reviewed draft and posting-decision surface
- run-history retention must avoid duplicating full workbook truth unless
  explicitly justified later

## UI / Platform Impact

- CLI remains the first management surface for schedules and history
- the existing local Web UI can later consume the same shared schedule/history
  queries
- platform adapters should remain unaware of scheduler persistence details
- the runtime remains local to the operator machine; no remote scheduler
  infrastructure is introduced

## Observability

Every scheduled run should be able to emit:

- `run_id`
- `schedule_id`
- `trigger=scheduled` or `trigger=manual`
- `timestamp`
- `sheet_name` when applicable
- `row_id` when applicable
- `platform` when applicable
- `action`
- `status`
- `message`

Useful events include:

- schedule created
- schedule paused or resumed
- due run started
- run skipped because of guardrail or conflict
- run completed or partially completed
- run failed with recovery context

## Alternatives Considered

1. Store schedule definitions and history in flat files only.
   Rejected because querying, recovery, and dashboard-style visibility are a
   better fit for structured local operational storage.
2. Depend only on OS-native cron or task scheduler entries.
   Rejected because product-level visibility and recoverable history would be
   fragmented outside the application boundary.
3. Move workbook posting decisions into operational storage for easier
   automation.
   Rejected because it violates the accepted workbook source-of-truth model.
