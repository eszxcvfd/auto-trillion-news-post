# Exec Plan

## Goal

Create the safe write-back and retry boundary for Pipeline B so platform
results can be persisted into `Trillion $ news.xlsx` without corrupting the
shared `Link Post` field or hiding workbook-write failures.

## Scope

In scope:

- write or replace one platform line inside `Link Post`
- preserve other platform lines on the same row
- serialize normalized result states such as success URL, `[error]`,
  `[login-required]`, and `[posted-no-link]`
- create timestamped workbook backups when configured
- detect locked or unwritable workbook states
- define retry-aware same-platform overwrite rules
- ensure one write failure does not silently corrupt unrelated row/platform
  data

Out of scope:

- redefining `Link Post` parse semantics
- redefining eligibility or planning logic from `US-007`
- adding new platform support claims
- Web UI and scheduling

## Risk Classification

Risk flags:

- Data model
- Public contracts
- Existing behavior
- Weak proof
- Multi-domain

Hard gates:

- changing `Link Post` write-back behavior
- changing retry behavior
- weakening backup or workbook-safety guarantees

## Work Phases

1. Discovery of current workbook update paths and new business workbook needs.
2. Design of write-back serializer, backup policy, and error model.
3. Validation planning for deterministic backup and lock fixtures.
4. Implementation of safe workbook mutation services.
5. Verification against spec acceptance criteria for FR-10 and FR-11.
6. Harness update for proof status and any follow-up decisions.

## Stop Conditions

Pause for human confirmation if:

- the accepted `Link Post` format must change
- backup behavior must become mandatory or optional in a new way
- workbook locking behavior cannot be surfaced clearly to the operator
- retry semantics need to overwrite states beyond the accepted same-platform
  line replacement model
