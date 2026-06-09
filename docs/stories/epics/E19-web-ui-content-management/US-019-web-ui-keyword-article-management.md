# US-019 Web UI Keyword and Article Management

## Status

planned

## Lane

normal

## Product Contract

Operators manage harvest **keywords** and workbook **articles** from the Web UI
without editing `keywords.txt` or Excel manually for routine curation. Keyword
changes persist to the canonical keywords file and feed the same harvest pipeline
as CLI and scheduler. Article actions (delete row with backup, regenerate LinkedIn
draft) mutate the business workbook through shared adapters; Excel remains
business source of truth.

## Relevant Product Docs

- `docs/product/overview.md`
- `docs/product/workbook-contracts.md`
- `docs/ARCHITECTURE.md`
- `docs/decisions/0012-linkedin-only-project-scope.md`

## Acceptance Criteria

- Web UI exposes a **Keywords** management surface: list, add, remove, and
  enable/disable keywords; no required manual file editing for routine updates.
- `GET` and `PUT` (or equivalent) `/api/keywords` endpoints read/write the
  canonical keywords file using a shared adapter; validation rejects empty/
  duplicate entries.
- Draft Run and scheduled draft jobs harvest using the updated keyword list
  without a separate code path.
- Dashboard (or equivalent) offers per-row article actions: **delete row**
  (backup before write) and **regenerate LinkedIn draft** for one row.
- Delete removes the row from workbook inspect/Dashboard; regenerate updates
  the LinkedIn draft cell via shared generation logic.
- Destructive actions show confirmation and clear error toasts on failure.
- LinkedIn-only scope preserved; no new multi-platform controls.
- Tests cover keyword adapter and new API routes; harness matrix updated when
  implemented.

## Design Notes

- Commands: keyword save; workbook row delete; single-row LinkedIn regenerate.
- Queries: `GET /api/keywords`; existing `/api/workbook/inspect`.
- API: `/api/keywords`, `/api/workbook/rows` (delete), `/api/workbook/rows/regenerate-draft`.
- Tables: none new; `keywords.txt` + business workbook only.
- Domain rules: parse keywords at boundary; workbook backup on delete; reuse
  `posting_core` / dashboard filter semantics.
- UI surfaces: new Keywords view; Dashboard row action menu.

## Story Packet

- `docs/stories/epics/E19-web-ui-content-management/US-019-web-ui-keyword-article-management/overview.md`
- `docs/stories/epics/E19-web-ui-content-management/US-019-web-ui-keyword-article-management/design.md`
- `docs/stories/epics/E19-web-ui-content-management/US-019-web-ui-keyword-article-management/execplan.md`
- `docs/stories/epics/E19-web-ui-content-management/US-019-web-ui-keyword-article-management/validation.md`

## Validation

When updating durable proof status, use numeric booleans:

`scripts/bin/harness-cli story update --id US-019 --unit 1 --integration 1 --e2e 1 --platform 1`

| Layer | Expected proof |
| --- | --- |
| Unit | Keyword adapter + row delete/regenerate helpers |
| Integration | Flask keyword and workbook mutation routes |
| E2E | Manual Keywords + Dashboard article action smoke |
| Platform | `python -m pytest tests/` passes |
| Release | Operator manages keywords and articles without CLI/file edits |

## Harness Delta

- New epic E19 and US-019 story packet for Web UI content management.
- Register US-019 in harness matrix as **planned**.

## Evidence

None yet — planning only.