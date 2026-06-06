# Exec Plan

## Goal

Create the shared posting-core layer that interprets business workbook row
state safely and chooses the next eligible row/platform work without embedding
that logic inside platform-specific Playwright code.

## Scope

In scope:

- define normalized `Link Post` state parsing
- define per-platform posting status vocabulary
- apply selective posting rules for `row x platform`
- apply default per-platform posting limits
- surface row/platform eligibility for supported platform adapters
- define command/query contracts for posting planning and execution handoff
- define failure states that later write-back can serialize safely

Out of scope:

- backup creation before workbook mutation
- locked-workbook recovery behavior
- final write-back durability guarantees
- full rollout of every target platform adapter
- Web UI and scheduling

## Risk Classification

Risk flags:

- Data model
- External systems
- Public contracts
- Existing behavior
- Weak proof
- Multi-domain

Hard gates:

- changing `Link Post` semantics
- changing selective posting behavior
- changing supported-platform interpretation

## Work Phases

1. Discovery of business workbook row model and current posting baseline.
2. Design of `Link Post` parser, state model, and eligibility rules.
3. Validation planning for deterministic row-state fixtures.
4. Implementation of shared posting-core commands/queries.
5. Verification against spec rules and release-B1 scope.
6. Harness update for story proof and follow-up boundaries with `US-008`.

## Stop Conditions

Pause for human confirmation if:

- `Link Post` text format must change from the accepted contract
- posting-limit defaults need product re-approval
- eligibility rules conflict with workbook review expectations
- platform-specific realities force changes to shared status vocabulary
