# Overview

## Current Behavior

The repo currently has:

- baseline internal-workbook status updates for the old CLI flow
- business workbook contract rules documented in `SPEC.md`
- `US-006` for business workbook ingestion
- `US-007` for shared posting-core parsing and eligibility planning

What is still missing:

- safe mutation of the business workbook `Link Post` cell
- backup handling before write-back
- locked-workbook failure behavior
- controlled retry/write-back semantics for the same platform line
- failure isolation rules at the write-back boundary

## Target Behavior

The application must support safe result write-back for Pipeline B.

After this story is complete, the system should be able to:

- update the correct platform line inside `Link Post`
- preserve existing lines for other platforms on the same row
- update an existing line for the same platform on retry
- create a timestamped backup before workbook mutation when backup mode is on
- fail clearly when the workbook is locked or cannot be written safely
- serialize normalized posting outcomes into stable operator-visible workbook
  state

This story owns the mutation safety boundary for the business workbook. It does
not expand platform coverage or invent new posting-state semantics beyond the
accepted contract.

## Affected Users

- Content Admin / Marketing Operator

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/workbook-contracts.md`
- `docs/product/release-boundaries.md`
- `docs/ARCHITECTURE.md`

## Non-Goals

- implementing every platform adapter end-to-end
- changing the accepted `Link Post` text format
- changing the default posting limit contract
- building Web UI or scheduling
