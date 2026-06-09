# Exec Plan

## Goal

Let operators edit LinkedIn post draft bodies in `output/posts/` from the Web UI
using a Word-like rich text editor, without breaking the markdown file contract
used by assisted posting and workbook draft references.

## Scope

In scope:

- shared `post_draft_store` (or equivalent) for list/parse/serialize/save
- path validation confined to `POST_DIR`
- REST endpoints in `src/web_ui.py`
- Post Drafts view + rich text editor UI in `src/templates/index.html`
- Dashboard **Edit draft** shortcut to open the linked file
- optional `.bak` on save
- unit + integration tests; manual operator smoke

Out of scope (this story):

- `.docx` import/export
- multi-user collaboration
- editing `## News` / `## Image` sections in WYSIWYG (read-only context only)
- inline-only Excel cell drafts with no file reference (follow-up if needed)
- AI assist inside editor
- new npm build pipeline (prefer vendored editor assets or minimal static bundle)

## Risk Classification

Risk flags:

- Existing behavior (`parse_post_markdown`, `load_draft_from_cell`)
- File writes outside intended directory if path guard is weak
- Editor HTML → markdown lossiness (formatting drift)

Hard gates:

- saved files must still parse via `parse_post_markdown()`
- path resolver must reject `..` and absolute paths outside `POST_DIR`
- posting dry-run after save must show updated text

## Work Phases (execution — not started)

1. **Post draft adapter** — `src/post_draft_store.py`: list, read sections,
   merge `generated_post`, save; unit tests with fixture `.md` files.
2. **Workbook linkage** — helper to map `POST_DIR` files → workbook rows via
   existing `resolve_post_draft_path` / ingest.
3. **API** — `GET/PUT /api/posts` routes with validation and logging.
4. **Editor UI** — Post Drafts view, vendored rich text component, save/discard,
   unsaved guard.
5. **Dashboard hook** — **Edit draft** button opens editor with correct file.
6. **Proof** — pytest, harness `story update`, validation evidence.

## Stop Conditions

Pause for human confirmation if:

- chosen editor cannot round-trip common formatting without breaking posting
- workbook rows store inline text only (no file ref) and user requires those
  editable too — may need scope expansion
- vendored editor assets exceed acceptable template size — consider lighter editor

## Suggested File Touch List (implementation reference)

| Area | Files |
| --- | --- |
| Post adapter | `src/post_draft_store.py` (new), `src/assisted_posting.py` (shared parse only) |
| API | `src/web_ui.py` |
| UI | `src/templates/index.html`, optional `src/static/editor/` |
| Tests | `tests/test_post_draft_store.py`, `tests/test_web_ui.py` |
| Docs | `README.md`, `docs/product/overview.md`, backlog, harness matrix |