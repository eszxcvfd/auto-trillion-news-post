# Overview

## Current Behavior

Harvest keywords and article rows are managed outside the Web UI operator
surface:

- **Keywords** live in `keywords.txt` (one phrase per line). The Draft Run view
  only exposes a free-text **Keywords File** path (`keywords.txt` by default).
  Operators must edit the file manually in an editor or terminal.
- **Articles** (business workbook rows in `Trillion $ news.xlsx`) are reviewed in
  the Dashboard through read-only inspection, filters, and analytics. Posting and
  draft generation are triggered per row or via bulk harvest runs. There is no
  Web UI to add/remove keywords, curate which keywords are active, or perform
  row-level article lifecycle actions (remove, exclude, regenerate) without
  opening Excel or the CLI.

Pipeline A still depends on `main.load_keywords()` and shared `execute_run()`
paths used by CLI, scheduler, and `POST /api/drafts/run`.

## Target Behavior

Operators manage **keywords** and **articles** from the Web UI without leaving
the dashboard workflow:

### Keywords management

- View the current keyword list with add, edit, remove, and enable/disable (or
  equivalent active flag) actions.
- Persist changes to the canonical keywords file (default `keywords.txt`) through
  a shared application helper — not ad hoc writes in the route handler.
- Draft Run and scheduled draft jobs consume the same normalized keyword list as
  CLI `search` / `run`.
- Validate duplicates, empty lines, and comment lines (`#`) consistently with
  `load_keywords()`.

### Article management

- From the Dashboard (or a dedicated Articles panel), operators can manage
  workbook rows that represent trillion-news articles:
  - remove a row from the business workbook (with backup safety),
  - exclude/include a row from operator surfaces without deleting Excel data
    (optional lightweight flag — only if simpler than delete),
  - trigger LinkedIn draft regeneration for a single row,
  - see clear confirmation and write-back/error messaging.
- All workbook mutations go through `business_workbook` adapters and existing
  backup semantics; Excel remains the business source of truth.
- Actions respect LinkedIn-only scope and dashboard row filtering rules from
  US-018.

## Affected Users

- Content Admin / Marketing Operator
- Developers maintaining harvest pipeline and workbook adapters

## Affected Product Docs

- `docs/product/overview.md` (Pipeline A operator inputs)
- `docs/product/workbook-contracts.md` (row mutation boundaries)
- `docs/ARCHITECTURE.md` (command/query split, parse-at-boundary)
- `README.md` (operator workflow — keywords no longer file-only)
- `AGENTS.md` (active work tracking)

## Non-Goals

- Replacing Excel as the primary review surface for long-form draft editing
- Moving workbook business state into SQLite
- Multi-keyword-file projects or per-schedule keyword file pickers beyond the
  current single canonical file (unless explicitly added in a follow-up story)
- Non-LinkedIn draft regeneration
- Full WYSIWYG article authoring or CMS features
- Implementing this story in the same change set as planning (execution is a
  separate phase)