# Design

## Intake Classification

| Field | Value |
| --- | --- |
| Input type | New initiative (operator UX slice) |
| Lane | normal |
| Risk | File writes + posting pipeline coupling + third-party editor dependency |

## Domain Model

### PostDraftFile (existing file, new application wrapper)

Represents one markdown file under `POST_DIR`:

- `relative_path` — path relative to `POST_DIR` (API identifier)
- `absolute_path` — resolved on server only
- `filename` — basename (e.g. `2026-06-09_001_payment_linkedin.md`)
- `modified_at` — filesystem mtime
- `sections` — parsed scaffold:
  - `header` — lines before `## News` (read-only)
  - `news` — `## News` block (read-only in MVP)
  - `image` — `## Image` block (read-only in MVP)
  - `generated_post` — editable body (plain text or markdown subset)
- `workbook_link` — optional `{ sheet_name, row_idx, row_id, title }` when
  ingest resolves a LinkedIn cell reference to this file

Persistence remains **file-backed**; no new database tables.

### PostDraftEditorState (UI concept)

- `dirty` — unsaved changes flag
- `content_html` or `content_json` — editor internal model (library-specific)
- `content_markdown` — normalized export for save pipeline

Round-trip rule: save path always produces valid markdown matching the existing
`write_post_file` scaffold so `parse_post_markdown()` behavior is unchanged.

## Application Flow

```text
Post Drafts view / Dashboard "Edit draft"
  -> GET /api/posts (list)
  -> GET /api/posts/<relative_path> (open: sections + editor payload)
  -> operator edits in WYSIWYG component
  -> PUT /api/posts/<relative_path> (body: generated_post markdown or html-to-md)
  -> post_draft_store.save() writes file (+ optional .bak)
  -> assisted_posting / inspect re-read via parse_post_markdown
```

## Interface Contract

### Proposed API (implementation phase)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/posts` | List drafts in `POST_DIR` with optional workbook linkage |
| GET | `/api/posts/<relative_path>` | Return parsed sections + editable body |
| PUT | `/api/posts/<relative_path>` | Save `generated_post` body; preserve scaffold |
| GET | `/api/posts/<relative_path>/raw` | Optional: full file text for advanced users |

Request validation:

- `relative_path` must not contain `..`, must resolve under `POST_DIR`
- Reject writes to non-`.md` files
- Return `423` when file is locked (if detectable) or `500` with explicit message

### CLI

No new CLI commands required. Existing `post` and assisted posting must read
updated files without restart.

### Web UI

- New sidebar view **Post Drafts** (or **Draft Editor**).
- Editor panel: toolbar + editable canvas + read-only metadata sidebar.
- Dashboard: **Edit draft** button when `linkedin_draft` resolves to a file ref.
- Advanced toggle (optional MVP+): raw markdown textarea for power users.

### Rich text library (exec-phase decision)

Choose a self-hosted, no-cloud-SaaS editor suitable for local operator tool:

| Option | Pros | Cons |
| --- | --- | --- |
| TipTap | Modern, extensible, good markdown bridge | More integration work |
| Quill | Simple toolbar, widely used | Markdown export needs care |
| TinyMCE | Word-like familiarity | Heavier bundle |

Decision deferred to execution; must work offline in local Flask template (CDN
or vendored static assets — prefer vendored for air-gapped operators).

## Data Model

| Store | Role |
| --- | --- |
| `output/posts/*.md` | Canonical LinkedIn draft bodies |
| `Trillion $ news.xlsx` | Row identity; LinkedIn cell holds file reference |
| `scheduler.db` | Unchanged |

## UI / Platform Impact

- LinkedIn-only labels in editor chrome and Dashboard actions.
- Vietnamese/English copy follows existing Dashboard tone.
- Editor must be usable in light/dark theme (reuse CSS variables).

## Observability

Log post save with `relative_path`, `action=post_draft_save`, `status`,
`bytes_written`, optional `workbook_link`.

## Alternatives Considered

1. **Raw markdown textarea only** — rejected; user explicitly requested Word-like
   editing.
2. **Edit inline in Dashboard expand row** — rejected for MVP; dedicated editor
   view gives space for toolbar and unsaved-state handling.
3. **Store HTML in Excel cell** — rejected; breaks file-reference contract and
   assisted posting parser.
4. **Only edit inline cell text (non-file refs)** — deferred; MVP focuses on
   `POST_DIR` files referenced by workbook cells.

## Dependencies

- US-006 / US-008 — workbook ingest, draft path resolution
- US-009 / US-013 — Web UI operator surface
- US-018 — LinkedIn-only scope
- US-019 — Dashboard row actions (add **Edit draft** alongside Regen/Delete)