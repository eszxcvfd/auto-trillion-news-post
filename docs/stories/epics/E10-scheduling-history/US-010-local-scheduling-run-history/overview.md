# Overview

## Current Behavior

The repo currently supports operator-driven execution through the CLI and the
new local Web UI surface.

Current truths:

- posting still starts from an explicit operator action
- workbook rows and `Link Post` remain the reviewed business source of truth
- per-run platform outcomes are written back into the workbook and emitted to
  local logs
- no local scheduler or recoverable product-level run history exists yet

Current limitations:

- the operator must remember when to run posting jobs
- there is no persisted schedule definition for repeated local runs
- there is no shared history view for successful, partial, failed, or missed
  runs
- future dashboard/history expectations from Release C are not yet satisfied

## Target Behavior

The application must add local scheduling and run history without changing the
business workbook source-of-truth boundary.

After this story is complete, the system should be able to:

- create and persist local schedule definitions for supported jobs
- trigger due jobs automatically on the operator machine
- record run history with enough detail for recovery and operator visibility
- expose schedule and history state to the CLI and shared application queries
- keep workbook review, selective posting, and write-back rules owned by the
  existing shared application core

This story adds operational automation. It must not move draft review, posting
decisions, or `Link Post` truth out of Excel.

## Affected Users

- Content Admin / Marketing Operator

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/release-boundaries.md`
- `docs/product/workbook-contracts.md`
- `docs/ARCHITECTURE.md`

## Non-Goals

- replacing manual CLI or Web UI triggers for one-off runs
- introducing cloud-hosted scheduling or remote workers
- using operational storage as a second business source of truth
- expanding platform support beyond the already accepted rollout
