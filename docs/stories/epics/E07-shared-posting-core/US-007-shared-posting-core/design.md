# Design

## Domain Model

Introduce posting-core-facing concepts on top of the business workbook row
model:

- `PlatformPostState`
  normalized state for one platform entry in `Link Post`
- `LinkPostDocument`
  parsed representation of the full shared `Link Post` cell
- `PostingEligibility`
  outcome for one `row x platform` pair such as eligible, skipped, retryable,
  or blocked
- `PostingCandidate`
  a concrete planned posting action selected for a platform
- `PostingPlan`
  selected candidates for one run after limits are applied

Business rules:

- URL success means do not repost
- `[posted-no-link]` means do not repost
- `[pending]`, `[error]`, `[login-required]`, or missing platform line are
  retryable
- no draft content means skip, not system failure
- default maximum is 2 eligible rows per platform per run
- malformed operator edits in `Link Post` fail clearly instead of overwriting
  silently

## Application Flow

Main command/query candidates:

- query: `parse_link_post_document`
- query: `evaluate_posting_eligibility`
- query: `build_posting_plan`
- command: `run_supported_platform_posting`

Expected application flow:

1. receive business workbook rows
2. parse each raw `Link Post` cell
3. normalize draft availability per platform
4. compute eligibility per `row x platform`
5. rank/select the next candidates per platform up to the configured limit
6. hand selected candidates to supported platform adapters
7. return normalized post results for later write-back

Platform adapters must consume `PostingCandidate` objects instead of making
their own direct decisions from raw workbook cells.

## Interface Contract

Expected interface behavior:

- CLI or future UI can request dry-run planning and real posting planning
- planning output must identify sheet, row id, platform, reason, and status
- malformed `Link Post` content must point back to the specific row and
  platform line that could not be parsed

Expected error classes:

- malformed `Link Post` document
- unsupported platform requested
- no eligible candidates found
- image/source prerequisites unresolved for a platform that requires them

## Data Model

No application database is required for this story.

Storage touched:

- read business workbook row state
- return normalized results for later mutation work

This story may define serialization rules for `Link Post`, but `US-008`
retains ownership of safe workbook write-back behavior.

## UI / Platform Impact

- current CLI is the first consumer
- future dry-run and session-status surfaces should call the same planning
  logic
- LinkedIn, Facebook, and X are the first intended supported adapters in
  Release B1
- no UI surface should reimplement eligibility or retry decisions

## Observability

Every planning or posting-core run should be able to emit:

- `run_id`
- `sheet_name`
- `row_id`
- `platform`
- `action`
- `status`
- `message`

Useful messages include:

- parsed `Link Post` successfully
- malformed `Link Post` line
- skipped because success already exists
- skipped because no content
- selected as candidate under per-platform limit
- blocked because image is required but unavailable

## Alternatives Considered

1. Let each platform adapter parse and interpret `Link Post` independently.
   Rejected because it duplicates contract logic, increases divergence risk, and
   makes selective posting inconsistent across platforms.
