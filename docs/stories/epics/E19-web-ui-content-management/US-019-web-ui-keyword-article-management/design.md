# Design

## Intake Classification

| Field | Value |
| --- | --- |
| Input type | New initiative (operator UX slice) |
| Lane | normal |
| Risk | Existing behavior + workbook writes + shared pipeline coupling |

## Domain Model

### KeywordEntry (new application concept)

Represents one harvest search phrase:

- `text` — normalized keyword string (trimmed, non-empty)
- `enabled` — optional; when false, skipped by harvest (default true)
- `sort_order` — stable ordering in file/UI

Persistence remains **file-backed** for MVP (`keywords.txt`), with an adapter
that round-trips:

```text
# comment line
Payment services trillion $
Mobile payments trillion $
```

Disabled keywords may be stored as commented lines (`# keyword`) or a prefixed
marker agreed in implementation — decision deferred to exec phase, must stay
compatible with `load_keywords()`.

### ArticleRow (existing `BusinessWorkbookRow`)

No schema migration. Article management operations map to workbook commands:

- `DeleteRow` — remove row from sheet, compact gaps (reuse repair/compact helpers)
- `RegenerateLinkedInDraft` — single-row generate via shared AI + workbook write
- Optional `HideFromDashboard` — filter-only if delete is too destructive; prefer
  delete + backup for MVP unless operator requests soft-hide

## Application Flow

### Keywords

```text
Web UI Keywords view
  -> GET /api/keywords (read normalized list)
  -> POST /api/keywords (replace list / CRUD payload)
  -> keywords_file_adapter.save()
  -> keywords.txt updated on disk

Draft Run / schedule draft job
  -> load_keywords() / shared helper
  -> execute_search() unchanged contract
```

### Articles

```text
Dashboard row action menu
  -> POST /api/workbook/rows/delete
  -> POST /api/workbook/rows/regenerate-draft
  -> business_workbook + writeback + backup_writer
  -> dashboard re-fetch inspect
```

## Interface Contract

### Proposed API (implementation phase)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/keywords` | List keywords with enabled state and source path |
| PUT | `/api/keywords` | Replace full keyword list (validated) |
| POST | `/api/keywords` | Add one keyword (optional convenience) |
| DELETE | `/api/keywords/<id or index>` | Remove one keyword (optional convenience) |
| DELETE | `/api/workbook/rows` | Delete row by `sheet_name`, `row_idx`; backup first |
| POST | `/api/workbook/rows/regenerate-draft` | Regenerate LinkedIn draft for one row |

All endpoints return explicit JSON errors; no silent workbook overwrite.

### CLI

No new CLI commands required for MVP. Existing `search` / `run` must read the
same keyword file after UI edits.

### Web UI

- New sidebar view **Keywords** (or section under Draft Run): table of keywords
  with add/remove/toggle active.
- Dashboard row **Actions** menu extensions: Delete article, Regenerate LinkedIn
  draft (with confirm modals).
- Remove or demote the raw **Keywords File** path field on Draft Run once keywords
  are managed in-app (path may remain read-only in Config for advanced users).

## Data Model

| Store | Role |
| --- | --- |
| `keywords.txt` | Canonical keyword list (MVP) |
| `Trillion $ news.xlsx` | Article/draft business truth |
| `scheduler.db` | Unchanged; run history only |

## UI / Platform Impact

- LinkedIn-only labels throughout new surfaces.
- Vietnamese/English UI copy follows existing Dashboard tone.
- Destructive actions require confirmation (delete keyword, delete row).

## Observability

Log keyword save and row delete/regenerate with `run_id` or operation id,
`sheet_name`, `row_idx`, `action`, `status`.

## Alternatives Considered

1. **SQLite keyword table** — rejected for MVP; file matches CLI and keeps ops
   visible in repo/output folder.
2. **Inline Excel editing in browser** — rejected; out of scope; Excel remains
   review surface for draft prose.
3. **Separate US for keywords vs articles** — deferred; single US for one
   operator initiative; may split at implementation if diff grows too large.

## Dependencies

- US-013 (Web UI draft run) — shared harvest entrypoint
- US-006 / US-008 — workbook ingest, backup, write-back
- US-018 — LinkedIn-only scope on generation and dashboard filtering