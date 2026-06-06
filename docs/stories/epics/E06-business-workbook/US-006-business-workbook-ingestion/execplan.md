# Exec Plan

## Goal

Create the first application-safe ingestion layer for `Trillion $ news.xlsx`
so Pipeline B can reason about business workbook rows without coupling posting
logic directly to raw Excel access.

## Scope

In scope:

- define the business workbook read contract in code-facing terms
- ingest multiple sheets from `Trillion $ news.xlsx`
- normalize headers and content cells
- preserve sheet/category context per row
- tolerate missing `Link Post` on read
- define coexistence rules between the internal compatibility workbook and the
  business workbook
- surface clear parse errors for malformed workbook structures

Out of scope:

- per-platform `Link Post` parsing semantics
- selective posting and retry behavior execution
- result write-back and backup implementation
- posting automation across platforms
- Web UI and scheduling

## Risk Classification

Risk flags:

- Data model
- Public contracts
- Existing behavior
- Weak proof
- Multi-domain

Hard gates:

- workbook contract hierarchy
- operator-facing source-of-truth behavior

## Work Phases

1. Discovery of current internal workbook usage and business workbook schema.
2. Design of row model, sheet model, and normalization rules.
3. Validation planning for deterministic workbook fixtures.
4. Implementation of workbook ingestion and mapping services.
5. Verification against baseline compatibility and spec rules.
6. Harness update for docs, proof status, and any follow-up decisions.

## Stop Conditions

Pause for human confirmation if:

- the business workbook schema needs to change
- coexistence with the internal workbook requires operator-facing workflow
  changes
- `Link Post` semantics need to be interpreted earlier than planned
- validation requirements would need to be weakened because fixtures or parsing
  rules are ambiguous
