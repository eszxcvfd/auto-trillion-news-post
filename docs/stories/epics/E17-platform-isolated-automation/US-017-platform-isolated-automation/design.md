# Design

## Domain Model

Shared domain concepts remain:

- `BusinessWorkbookRow`
- `PlatformName`
- `PlatformPostResult`
- session state vocabulary such as `ready`, `login-required`, `error`
- `Link Post` per-platform result lines

New boundary expectation:

- each platform owns a dedicated posting workflow definition instead of sharing
  browser behavior through one generic adapter path
- shared domain rules decide **whether** a `row x platform` pair is eligible
- platform workflows decide **how** the posting attempt is executed

## Application Flow

Expected command/query shape:

1. shared application logic ingests workbook rows and resolves eligible
   `row x platform` pairs
2. shared dispatch selects a platform-owned workflow by canonical platform name
3. the selected workflow performs session validation, composer preparation,
   media handling, submission, and provider-specific result capture
4. shared write-back persists the final status into `Link Post`
5. shared run history records the outcome without assuming another platform's
   execution semantics

Expected future slices:

- `run_platform_posting(platform, row, context)` or equivalent workflow entry
- one module/package per supported platform
- release-group dispatch only as an organizational concern, not as a runtime
  coupling mechanism

## Interface Contract

CLI, Web UI, and scheduler should preserve operator-facing inputs while routing
to isolated workflows:

- CLI `post` still chooses one `row x platform` target at a time
- Web UI still presents platform-specific actions per row
- scheduler still plans and records per-platform runs

Errors should become platform-owned where appropriate:

- session invalid for one platform must not imply another platform is invalid
- selector drift for one platform must not require a shared emergency patch in
  unrelated workflows
- media-precondition failures remain platform-specific

## Data Model

No workbook schema change is required by this story.

Potential operational data follow-ups:

- run history may need a clearer field for workflow identity or adapter version
- traces/logs should attribute failures to a specific platform workflow

If storage changes are needed later, they should stay in local SQLite
operational history and must not replace workbook truth.

## UI / Platform Impact

Operator surfaces should make platform independence visible:

- platform actions can fail, pause, or be retried independently
- session onboarding remains per platform
- scheduler/reporting should allow one platform workflow to degrade without
  blocking unrelated platform runs

## Observability

Every posting attempt should emit:

- `platform`
- `workflow_id` or equivalent workflow identity
- `row_id`
- `sheet_name`
- `session_state`
- `result_status`
- provider-specific failure reason when available

Run history should support answering:

- which platform workflow failed
- whether the failure is isolated to one provider
- whether retry is safe for that provider only

## Alternatives Considered

1. Keep one shared posting core and continue adding platform branches.
   Rejected because platform behavior keeps diverging operationally and raises
   the blast radius of each adapter change.
2. Split everything, including workbook and result semantics, per platform.
   Rejected because it would break the accepted workbook and `Link Post`
   contract.
3. Move all posting logic into separate standalone services now.
   Rejected because it exceeds the local-runtime MVP boundary.
