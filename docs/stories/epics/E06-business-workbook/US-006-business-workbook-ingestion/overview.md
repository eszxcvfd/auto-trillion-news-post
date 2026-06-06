# Overview

## Current Behavior

The baseline repo writes and reads an internal 14-column workbook for harvest,
generation, and assisted LinkedIn posting.

Current constraints:

- the CLI baseline is centered on the internal workbook contract
- the operator-facing business workbook is not yet ingested by the application
- multi-sheet category handling does not exist yet
- operator edits made in `Trillion $ news.xlsx` are not yet part of the main
  runtime flow

## Target Behavior

The application must ingest `Trillion $ news.xlsx` as the operator-facing
business workbook for v2.

After this story is complete, the system should be able to:

- open the business workbook across all valid sheets
- normalize headers before matching
- map valid rows into a stable business row model
- preserve sheet name as category context
- treat operator-edited draft text in Excel as the final input for later
  posting work
- resolve local draft markdown file paths in platform cells to actual post content during ingestion
- coexist with the legacy internal workbook contract without forcing the
  operator to manage both manually

This story establishes the read-side and mapping-side contract. It does not yet
complete selective posting or result write-back.

## Affected Users

- Content Admin / Marketing Operator

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/workbook-contracts.md`
- `docs/product/release-boundaries.md`
- `docs/ARCHITECTURE.md`

## Non-Goals

- implementing the full `Link Post` parser/writer
- implementing multi-platform posting execution
- implementing Web UI or scheduling
- replacing the internal compatibility workbook immediately
