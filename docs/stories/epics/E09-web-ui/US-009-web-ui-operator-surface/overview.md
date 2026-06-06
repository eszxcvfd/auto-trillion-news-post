# Overview

## Current Behavior

The repo currently operates through a CLI-first workflow.

Current truths:

- baseline commands exist for harvest, generate, run, and assisted posting
- business workbook contracts and posting-core slices are documented
- non-technical operation is a product goal, but no true operator-facing Web UI
  exists yet

Current limitations:

- the operator needs CLI familiarity for most flows
- there is no browser-based view of workbook rows, run status, or platform
  session state
- there is no shared operator dashboard for triggering business-workbook-based
  flows

## Target Behavior

The application must introduce a Web UI operator surface for local use.

After this story is complete, the system should be able to:

- load or select the active workbook
- display sheets and row-level status at an operator-friendly level
- show platform session or login status
- trigger the same posting or planning workflows already defined in the
  application layer
- show per-row/per-platform outcomes without requiring direct CLI use

This story adds a new surface. It must not fork workbook logic, posting logic,
or source-of-truth behavior away from the CLI and shared application core.

## Affected Users

- Content Admin / Marketing Operator

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/release-boundaries.md`
- `docs/product/workbook-contracts.md`
- `docs/ARCHITECTURE.md`

## Non-Goals

- replacing the CLI surface
- inventing a second product truth outside Excel and shared application rules
- adding scheduling behavior in the same story
- building a cloud-hosted or multi-user web application
