# Exec Plan

## Goal

Create the local scheduling and run-history slice for Release C so the operator
can define recoverable timed runs and inspect what happened without relying on
memory, ad-hoc notes, or direct CLI timing.

## Scope

In scope:

- define the supported local schedule model for workbook-based jobs
- persist schedule configuration and enabled/disabled state
- trigger due jobs through the shared application core
- record run-history summaries and failure visibility for each scheduled run
- expose shared schedule/history queries for CLI and future Web UI use
- preserve current posting safety rules such as workbook truth, selective
  posting, backup policy, and posting limits

Out of scope:

- cloud scheduling or distributed workers
- replacing explicit manual runs with scheduler-only behavior
- storing draft content or posting decisions in operational history tables
- changing platform capability scope from Releases B1 to B3
- weakening write-back, retry, or dry-run safety guarantees

## Risk Classification

Risk flags:

- Data model
- Public contracts
- Existing behavior
- Weak proof
- Multi-domain

Hard gates:

- changing local runtime/storage assumptions beyond the accepted local SQLite
  boundary
- allowing scheduled runs to bypass the workbook as the reviewed source of
  truth
- reducing visibility or recoverability for automatic runs compared with manual
  runs

## Work Phases

1. Discovery of current posting entrypoints, run logging, and Release C
   operator expectations.
2. Design of schedule definitions, run-history views, and trigger boundaries.
3. Validation planning for fake-clock, fixture workbook, and failure-history
   proof.
4. Implementation of the scheduler service, operational store, and shared
   queries.
5. Verification against FR-14 and Release C recoverability goals.
6. Harness update for proof status and any follow-up decisions.

## Stop Conditions

Pause for human confirmation if:

- scheduled execution needs a different source of truth than the workbook
- the accepted local-only runtime assumption must change
- run history requires sensitive data retention not covered by current logging
  rules
- scheduler support would require weakening posting safety or operator recovery
  guarantees
