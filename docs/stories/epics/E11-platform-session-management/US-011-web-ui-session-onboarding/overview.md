# Overview

## Current Behavior

The product contract already expects persistent platform sessions, but the
operator-facing future flow is still incomplete.

Current truths:

- posting should reuse saved platform sessions when they are valid
- `login-required` is already part of the accepted result vocabulary
- Web UI is an accepted future operator surface

Current limitations:

- the future contract does not yet make Web UI the explicit onboarding surface
  for platform login
- the boundary between application-managed sessions and a logged-in developer
  browser environment is too implicit
- a non-technical operator could still be forced to rely on an external dev
  browser setup before posting

## Target Behavior

The application must let the operator onboard and refresh platform sessions
through the local Web UI, then reuse those saved sessions in later posting
runs.

After this story is complete, the system should be able to:

- start a per-platform login flow from the Web UI
- let the operator complete manual login in a visible browser flow when needed
- persist the resulting platform session as an application-owned local asset
- show whether a platform session is ready, invalid, or needs login
- reuse that saved session during later posting runs without requiring the
  operator to log into a developer Chrome profile or browser environment first

## Affected Users

- Content Admin / Marketing Operator

## Affected Product Docs

- `SPEC.md`
- `docs/product/overview.md`
- `docs/product/release-boundaries.md`
- `docs/ARCHITECTURE.md`

## Non-Goals

- storing raw passwords for automatic login
- bypassing captcha, MFA, or other platform verification flows
- supporting multiple simultaneous accounts for one platform in the same run
- replacing workbook truth or posting rules with session metadata
