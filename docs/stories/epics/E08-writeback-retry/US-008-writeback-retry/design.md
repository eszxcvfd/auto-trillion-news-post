# Design

## Domain Model

Introduce write-back-facing concepts on top of `US-007` posting-core results:

- `PlatformWritebackEntry`
  one serialized `Platform: value` line
- `LinkPostMutation`
  before/after representation of a `Link Post` document for one row
- `WritebackResult`
  success or failure outcome of one workbook mutation attempt
- `RetryDisposition`
  rule for whether a same-platform line can be replaced

Business rules:

- only the target platform line may be added or replaced
- other platform lines must be preserved verbatim when still valid
- same-platform retry may replace the prior same-platform line
- malformed `Link Post` content must fail clearly before mutation
- backup must happen before workbook write when backup mode is enabled
- locked-workbook failures must be explicit and non-partial

## Application Flow

Main command/query candidates:

- command: `write_post_result`
- command: `write_post_results_batch`
- query: `prepare_link_post_mutation`
- query: `evaluate_retry_disposition`

Expected application flow:

1. receive normalized posting result for one `row x platform`
2. load the current workbook row state
3. parse current `Link Post`
4. prepare mutation for the target platform line only
5. optionally create backup
6. write workbook changes atomically as safely as possible
7. return structured success/failure result for logging and retry behavior

This flow must sit between posting-core results and operator-visible workbook
state.

## Interface Contract

Expected interface behavior:

- CLI or future UI receives explicit mutation success/failure feedback
- errors identify sheet, row, and platform context
- backup failures are surfaced distinctly from workbook-lock failures
- retry of the same platform overwrites only that platform line

Expected error classes:

- malformed `Link Post` document
- backup creation failure
- workbook locked or permission denied
- row or sheet not found during write-back
- partial mutation prevented before write

## Data Model

No application database is required for this story.

Storage touched:

- read and write `Trillion $ news.xlsx`
- create timestamped workbook backups when enabled
- emit operational logs for write-back attempts

The local filesystem remains the operational storage boundary for backups.

## UI / Platform Impact

- current CLI is the first consumer
- future UI must show workbook-write errors distinctly from posting errors
- platform adapters should not write directly to Excel; they should return
  normalized results to the write-back service

## Observability

Every write-back attempt should be able to emit:

- `run_id`
- `sheet_name`
- `row_id`
- `platform`
- `action=write_post_result`
- `status`
- `message`

Useful messages include:

- backup created
- backup skipped by config
- write-back succeeded
- workbook locked
- malformed `Link Post` prevented mutation
- same-platform line replaced on retry

## Alternatives Considered

1. Let each platform adapter write directly into Excel.
   Rejected because it duplicates mutation logic, weakens safety guarantees, and
   risks inconsistent preservation of unrelated platform lines.
