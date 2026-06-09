# Design

## Domain Model

Introduce session-management concepts without creating a second business truth:

- `PlatformSessionState`
  readiness state such as ready, invalid, expired, or login-required
- `PlatformSessionRecord`
  local metadata about a saved session artifact for one platform
- `SessionOnboardingRequest`
  operator intent to start or refresh a login flow
- `SessionValidationResult`
  result of checking whether a saved session is still reusable

Business rules:

- saved sessions are application-owned local assets per platform
- session metadata is operational state, not workbook truth
- login success may persist session state, but it must not persist raw
  passwords
- later posting runs must try to reuse a valid saved session first
- invalid sessions must surface `login-required` instead of failing silently

## Application Flow

Main command/query candidates:

- command: `start_platform_session_onboarding`
- command: `refresh_platform_session`
- command: `clear_platform_session`
- query: `get_session_status`
- query: `list_supported_platform_sessions`
- query: `validate_saved_platform_session`

Expected application flow:

1. the operator selects a platform in the Web UI
2. the interface layer starts a supported login/onboarding flow
3. the browser automation layer opens a visible login path for that platform
4. after successful manual login, the application persists session state
5. later posting runs load the saved session and validate it before posting
6. invalid or expired sessions return `login-required` and send the operator
   back through the supported refresh flow

The Web UI must trigger shared application commands. It must not directly own
browser-storage semantics or posting rules.

## Interface Contract

Expected web interface behavior:

- per-platform actions for login, refresh, clear, and status inspection
- clear operator messaging about ready, invalid, expired, or login-required
  states
- visible linkage between session state and later posting readiness

Expected error classes:

- platform not supported in the current release
- login flow cancelled or incomplete
- session persistence failure
- session validation failure
- platform-specific login-required or verification interruption

## Data Model

Expected storage touched:

- local session files or Playwright storage-state artifacts
- optional local metadata describing last validation time or status

Boundary rules:

- application-managed session storage is local-only
- workbook files remain the reviewed product truth
- any metadata store must not become a credential vault

## UI / Platform Impact

- the local Web UI becomes the supported onboarding surface for saved sessions
- CLI and posting flows should be able to consume the same saved session state
- platform adapters remain responsible for session validation and posting inside
  shared infrastructure boundaries

## Observability

Every session-management action should be able to emit:

- `platform`
- `action`
- `status`
- `message`
- `session_id` or local correlation id when available

Useful events include:

- session onboarding started
- operator login completed
- session persisted successfully
- session validation failed
- session cleared
- posting reused saved session

## Alternatives Considered

1. Depend on a manually logged-in developer browser environment.
   Rejected because it is not a stable product contract for non-technical
   operation.
2. Re-login manually on every posting run.
   Rejected because it increases operator friction and underuses persistent
   session capabilities.
