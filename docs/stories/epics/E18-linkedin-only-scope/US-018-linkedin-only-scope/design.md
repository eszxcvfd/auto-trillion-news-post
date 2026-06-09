# Design

## Domain Model

Shared workbook entities remain, but the active platform domain for this
project becomes:

- supported platform set: `linkedin`
- fixed platform identity for default generation and posting preferences
- LinkedIn-only session ownership and validation

Existing workbook fields for other platforms may remain as compatibility data,
but they are not active product behavior after this story.

## Application Flow

Expected runtime behavior:

1. config loads LinkedIn as the fixed default platform
2. generation/planning/scheduling normalize requested platforms down to
   LinkedIn-only
3. posting eligibility and dispatch only consider LinkedIn
4. non-LinkedIn requests fail fast with clear operator-visible messages
5. Web UI and scheduler stop offering other platform actions

## Interface Contract

CLI:

- `generate`, `run`, `post`, `inspect-workbook`, and `schedule add` should no
  longer behave as multi-platform operator surfaces

Web UI:

- platform controls become LinkedIn-only
- session management only shows LinkedIn
- draft generation and planner controls no longer accept editable multi-platform
  lists

Config:

- default platform is fixed to LinkedIn regardless of `.env` or YAML override

## Data Model

No required workbook-schema migration in this story.

Operational implications:

- scheduler rows may still contain historical `platforms` values, but new and
  active flows normalize to LinkedIn
- run history remains valid because platform attribution still works for
  LinkedIn

## UI / Platform Impact

- LinkedIn becomes the only visible platform in forms, buttons, and session
  cards
- any text implying other supported platforms must be removed or rewritten
- config views should show LinkedIn as fixed rather than editable

## Observability

Logs and errors should make scope narrowing explicit:

- non-LinkedIn requests should state that the project is LinkedIn-only
- run history and UI state continue to record LinkedIn outcomes normally

## Alternatives Considered

1. Keep multi-platform code paths but hide them only in UI.
   Rejected because CLI, scheduler, and runtime behavior would still contradict
   project scope.
2. Remove non-LinkedIn workbook columns immediately.
   Rejected for this story because it would add migration and backward
   compatibility risk.
3. Add a feature flag for other platforms.
   Rejected because the requirement is an explicit project-scope narrowing, not
   a temporary operator preference.
