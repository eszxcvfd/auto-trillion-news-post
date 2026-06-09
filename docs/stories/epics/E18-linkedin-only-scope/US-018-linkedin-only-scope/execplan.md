# Exec Plan

## Goal

Shrink the product surface to LinkedIn-only and remove all operator-facing and
runtime support for other platforms.

## Scope

In scope:

- force LinkedIn as the only valid default platform in config/runtime
- remove other platform choices from CLI planning and scheduling surfaces
- remove other platform controls from Web UI
- reject non-LinkedIn dispatch in posting capability and workflow layers
- update docs, decisions, and validation to reflect the narrowed scope

Out of scope:

- workbook schema migration to physically remove old columns
- deleting historical test artifacts or historical workbook data
- adding a future feature flag for restoring other platforms

## Risk Classification

Risk flags:

- External systems
- Public contracts
- Cross-platform
- Existing behavior
- Weak proof
- Multi-domain

Hard gates:

- removing supported platforms from the accepted release matrix
- any workbook-contract change discovered during implementation

## Work Phases

1. Scope and decision update.
2. Runtime/platform dispatch narrowing.
3. UI and config lock-down.
4. Test and proof updates.
5. Product/harness doc alignment.
6. Verification and trace.

## Stop Conditions

Pause for human confirmation if:

- workbook columns must be removed instead of merely ignored
- historical data compatibility would be broken
- a non-LinkedIn platform path is still required for release-critical workflows
