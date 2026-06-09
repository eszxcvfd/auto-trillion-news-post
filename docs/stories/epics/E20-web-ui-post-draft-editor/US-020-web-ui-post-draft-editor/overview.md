# Overview

## Current Behavior

Generated LinkedIn drafts are persisted as markdown files under
`output/posts/` (`POST_DIR`). Each file follows a fixed scaffold written by
`write_post_file()`:

```markdown
# Post 001 — Linkedin

## News
Title: …
Source: …
URL: …

## Image
../Ảnh Trillion $ news/…

## Generated Post
<draft body used for posting>
```

Operators today:

- **Preview** draft text read-only in the Dashboard expanded row (truncated
  preview from workbook ingest).
- **Edit** by opening the `.md` file in an external text editor or VS Code.
- **Post** via assisted posting, which calls `parse_post_markdown()` to extract
  content after `## Generated Post`.

There is no in-app rich text editor. US-019 added keyword and workbook row
management but explicitly deferred full draft-body editing in the Web UI.

## Target Behavior

Operators manage and edit post draft **content** from the Web UI with a
**Word-like** experience:

### Post Drafts library

- Browse drafts in `POST_DIR` (default `output/posts/`).
- See filename, modified time, linked workbook sheet/row/title when the LinkedIn
  cell references the file.
- Search/filter by title fragment or filename.

### Rich text editor

- Open a draft in a WYSIWYG editor with familiar formatting controls (toolbar).
- Edit the **Generated Post** body visually; metadata sections (`News`, `Image`)
  shown read-only for context.
- Save persists to the same markdown file using a shared serializer that
  preserves the scaffold and only replaces the generated body.
- Unsaved changes prompt before leaving the editor.

### Dashboard integration

- Rows with a resolvable LinkedIn draft file show **Edit draft** alongside
  existing Post / Regen / Delete actions.
- After save, Dashboard preview and `POST /api/post` flows use the updated body.

## Affected Users

- Content Admin / Marketing Operator — primary editors of LinkedIn copy
- Developers maintaining `draft_paths`, `assisted_posting`, and Web UI

## Affected Product Docs

- `docs/product/overview.md` (Pipeline A review/edit loop)
- `docs/ARCHITECTURE.md` (parse-at-boundary, file-backed drafts)
- `README.md` (operator workflow — drafts editable in Web UI)
- `AGENTS.md` (active work tracking)

## Non-Goals

- Replacing Excel as business source of truth for row identity and posting status
- Import/export `.docx` files (Word-like **UX**, not Microsoft Word file format)
- Collaborative real-time editing or comment threads
- Editing non-LinkedIn platform draft files as a supported operator flow
- Moving draft storage to SQLite or cloud
- AI rewrite / regenerate inside the editor (use existing **Regen** action)
- Implementing this story in the same change set as planning (execution is a
  separate phase)