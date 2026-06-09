# Overview

## Current Behavior

The current product direction and release docs describe a shared posting core
that routes multiple supported platforms through one common automation path.

Current truths:

- the business workbook and `Link Post` remain the shared operator-facing source
  of truth
- scheduling, Web UI, and CLI all converge toward one posting orchestration
  surface
- some platform adapters already dispatch differently, but the repo still frames
  posting as a shared cross-platform core

Current concern:

- platform automation behavior is operationally different enough that coupling
  flows together increases regression risk, selector drift, and debugging
  complexity

## Target Behavior

Each supported platform should have its own auto-posting workflow that can be
developed, validated, scheduled, and recovered independently.

After this story is complete, the architecture should make these truths
explicit:

- each platform owns its own browser steps, readiness checks, media rules,
  failure mapping, and recovery path
- platform workflows do not depend on another platform's selectors, composer
  assumptions, or success criteria
- shared concerns remain limited to workbook ingestion, eligibility selection,
  session boundary rules, run recording, and `Link Post` write-back semantics
- CLI, Web UI, and scheduler dispatch into platform-specific workflows instead
  of treating posting as one tightly coupled automation engine

## Affected Users

- Content Admin / Marketing Operator
- Future maintainers of platform automation adapters

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/release-boundaries.md`
- `docs/product/workbook-contracts.md`
- `docs/ARCHITECTURE.md`
- `docs/decisions/0010-platform-session-persistence-boundary.md`

## Non-Goals

- changing the workbook source-of-truth hierarchy
- changing `Link Post` syntax or write-back ownership
- removing selective posting by `row x platform`
- promising full autonomous posting for unsupported or best-effort platform
  modes
