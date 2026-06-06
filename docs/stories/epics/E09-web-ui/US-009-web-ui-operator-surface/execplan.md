# Exec Plan

## Goal

Create the first local Web UI operator surface so a non-technical user can
select a workbook, inspect status, and trigger the main posting workflows
without depending on direct CLI commands.

## Scope

In scope:

- define the local web server surface and basic navigation shape
- show workbook selection or active workbook context
- show sheet/row summaries derived from the shared application layer
- show platform session/login status
- trigger posting or dry-run workflows through shared commands
- show row/platform result visibility after command execution

Out of scope:

- scheduling UI
- a cloud deployment model
- multi-user auth or permissions
- platform-specific posting logic inside web handlers
- replacing the workbook as the operator source of truth

## Risk Classification

Risk flags:

- Public contracts
- Existing behavior
- Weak proof
- Multi-domain

Hard gates:

- introducing Web UI as a new operator surface
- any design that bypasses shared posting or workbook logic

## Work Phases

1. Discovery of current CLI workflows and shared application seams.
2. Design of web routes, presenters, and minimal operator interactions.
3. Validation planning for local UI proof and surface-to-core integration.
4. Implementation of the local web backend and operator pages.
5. Verification against Release C operator goals.
6. Harness update for proof status and any new architecture decisions.

## Stop Conditions

Pause for human confirmation if:

- the UI requires product behavior not yet defined in the shared application
  core
- the local-only runtime assumption must change
- the UI needs an auth/permission model not already accepted
- workbook edits or posting actions would need a different source-of-truth
  hierarchy than the CLI
