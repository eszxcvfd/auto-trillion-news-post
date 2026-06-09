# Exec Plan

## Goal

Define and later implement a posting architecture where every platform is an
independent automation workflow, while preserving the shared workbook and
operator surface contracts.

## Scope

In scope:

- define the boundary between shared orchestration and platform-owned workflows
- separate per-platform posting responsibilities for CLI, Web UI, and scheduler
- define per-platform validation and observability requirements
- identify migration steps away from a shared posting-core mental model

Out of scope:

- changing Pipeline A harvest or draft generation behavior
- changing workbook schemas
- weakening operator confirmation or session boundaries
- expanding platform support beyond the accepted release matrix

## Risk Classification

Risk flags:

- External systems
- Public contracts
- Cross-platform
- Existing behavior
- Weak proof
- Multi-domain

Hard gates:

- external provider behavior
- changing selective posting or retry semantics if discovered during design

## Work Phases

1. Discovery of current shared posting assumptions.
2. Boundary design for platform-isolated workflows.
3. Validation planning per platform and per operator surface.
4. Implementation slicing by release/platform group.
5. Verification with platform-specific proof.
6. Harness and decision updates.

## Stop Conditions

Pause for human confirmation if:

- the new boundary requires changing `Link Post` semantics
- workbook write-back must move away from the current shared contract
- scheduling or Web UI needs a different run-history contract per platform
- the release matrix must be reordered or narrowed
