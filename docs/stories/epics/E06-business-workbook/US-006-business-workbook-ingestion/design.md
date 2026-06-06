# Design

## Domain Model

Introduce business-workbook-facing concepts separate from the baseline
`NewsItem`:

- `BusinessWorkbookSheet`
  one valid sheet plus normalized header map
- `BusinessWorkbookRow`
  one row with sheet name, row id, title, image source, raw platform drafts,
  and raw `Link Post` text
- `BusinessWorkbookHeaders`
  normalized mapping for required and optional columns
- `DraftContent`
  trimmed content where empty string, whitespace, and `.` all mean no content

Business rules:

- sheet names are retained as category context
- missing `Link Post` is tolerated on read
- malformed headers fail clearly
- operator-edited workbook values are authoritative for later posting work
- local draft markdown file paths in platform cells are automatically resolved by reading and parsing the markdown file

## Application Flow

Main command/query candidates:

- command: `ingest_business_workbook`
- query: `inspect_business_workbook`
- query: `list_business_workbook_rows`

Expected application flow:

1. open workbook path
2. iterate valid sheets
3. normalize headers
4. read rows with a valid title
5. normalize draft cell values and resolve markdown draft file paths to actual post text if present
6. attach raw `Link Post` text without yet enforcing per-platform semantics
7. return typed workbook/sheet/row objects for later posting-core work

The internal compatibility workbook remains a separate application path until a
later story explicitly unifies more of Pipeline A and Pipeline B.

## Interface Contract

Expected interface behavior:

- CLI or future UI selects workbook path and optional sheet scope
- ingest result returns row objects plus parse warnings/errors
- parse failures must identify sheet and header/row context clearly

Expected error classes:

- workbook missing or unreadable
- required headers missing
- malformed row identity/title cells
- malformed workbook shape that prevents safe ingestion

## Data Model

No application database change is required for this story.

Storage touched:

- read from `Trillion $ news.xlsx`
- optionally read from the internal compatibility workbook when coexistence
  mapping is needed

This story is read-side only for the business workbook. It should not yet own
write-back mutation semantics.

## UI / Platform Impact

- current CLI remains the first consumer
- future Web UI must call the same ingestion service
- no platform-specific browser automation should be embedded in this story

## Observability

Every ingestion run should be able to emit:

- `run_id`
- `sheet_name`
- `row_id`
- `action=ingest_business_workbook`
- `status`
- `message`

Useful warnings include:

- header normalized
- missing `Link Post` tolerated
- row skipped because title missing
- row parsed with no usable draft content

## Alternatives Considered

1. Reuse the baseline `NewsItem` model directly for the business workbook.
   Rejected because it mixes two contracts with different responsibilities and
   source-of-truth rules.
