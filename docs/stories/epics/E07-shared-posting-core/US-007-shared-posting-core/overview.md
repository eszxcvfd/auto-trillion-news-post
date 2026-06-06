# Overview

## Current Behavior

The repo currently has:

- baseline assisted LinkedIn posting driven from the internal compatibility
  workbook
- business workbook contract documentation
- planned `US-006`/implemented ingestion layer for reading business workbook
  rows safely

What is still missing:

- shared posting-core logic for row/platform eligibility
- safe parsing of the shared `Link Post` text block
- normalized interpretation of per-platform posting state
- a reusable contract that later platform adapters can call without redoing
  workbook-state logic

## Target Behavior

The application must introduce a shared posting core for Pipeline B.

After this story is complete, the system should be able to:

- parse the raw `Link Post` cell into normalized per-platform states
- determine whether a given `row x platform` pair is eligible, skipped, or
  retryable
- apply the selective posting rules from `SPEC.md`
- enforce the default posting limit of 2 eligible rows per platform per run
- expose a reusable command/query layer so future LinkedIn/Facebook/X posting
  modules do not own business eligibility rules

This story establishes posting-state interpretation and shared orchestration
contracts. It does not yet complete safe workbook backup/write-back mutation
handling, which remains in `US-008`.

## Affected Users

- Content Admin / Marketing Operator

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/workbook-contracts.md`
- `docs/product/release-boundaries.md`
- `docs/ARCHITECTURE.md`

## Non-Goals

- implementing all platform adapters end-to-end
- backup policy and locked-workbook mutation handling
- Web UI or scheduling
- broadening the business workbook schema
