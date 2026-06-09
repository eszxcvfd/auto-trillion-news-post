# 0010 Platform Session Persistence Boundary

Date: 2026-06-06

## Status

Accepted

## Context

The approved spec already expects persistent platform sessions, but the current
wording leaves an important ambiguity: a later implementation could depend on a
developer Chrome profile or browser environment that happens to be logged in,
instead of treating platform sessions as application-managed local assets.

Without a clearer boundary, future work could:

- force the operator to log back into a developer browser environment before
  every posting run
- blur the ownership of saved platform sessions between ad-hoc browser state
  and application state
- make Web UI operation incomplete for non-technical users because session
  onboarding would still live outside the product surface

## Decision

Adopt the following session boundary for future platform posting work:

1. **Application-owned session assets**
   Saved social-platform sessions are local assets managed by the application
   per supported platform.
2. **Supported onboarding surface**
   The Web UI is an accepted surface for initiating, refreshing, and inspecting
   platform session state.
3. **Reuse requirement**
   Future posting runs must attempt to reuse the saved application-managed
   session instead of requiring the operator to be logged into a developer
   Chrome profile or browser environment beforehand.
4. **Failure behavior**
   When a saved session is expired, revoked, or invalid, the system reports
   `login-required` and sends the operator back through a supported re-login
   flow.
5. **Credential boundary**
   The product may store session state or browser storage artifacts locally,
   but it must not store raw account passwords in source, workbook, or logs.

## Alternatives Considered

1. Depend on a manually logged-in developer Chrome profile or browser
   environment.
   Rejected because it is not a stable product contract and does not support
   non-technical Web UI operation.
2. Require manual login on every posting run.
   Rejected because it defeats the value of persistent local sessions and adds
   unnecessary operator friction.
3. Store raw account credentials for automatic login.
   Rejected because it increases security risk and is outside the accepted
   operator-assisted model.

## Consequences

Positive:

- future Web UI work has a clear responsibility for session onboarding and
  refresh
- posting runs can reuse known-good local sessions without depending on a dev
  browser profile
- local runtime boundaries are clearer for future session, scheduling, and
  observability work

Tradeoffs:

- the product must manage session storage and invalidation more explicitly
- docs and code must distinguish application session state from ad-hoc browser
  state on the machine

## Follow-Up

- keep `SPEC.md`, `docs/product/*`, and Web UI stories aligned on the session
  onboarding contract
- keep session storage local and treat it as sensitive operational data
