# US-020 Web UI Post Draft Editor (Word-like)

## Status

implemented

## Lane

normal

## Product Contract

Operators edit LinkedIn post draft bodies stored as markdown files under the
canonical post directory (`output/posts/` by default, `POST_DIR` in config)
directly from the Web UI. Editing uses a **Word-like rich text experience**
(WYSIWYG toolbar: formatting, lists, links, undo/redo) while persisting back to
the existing markdown file contract (`## Generated Post` section) so CLI posting,
assisted posting, and workbook draft references keep working without a fork.

## Relevant Product Docs

- `docs/product/overview.md`
- `docs/product/workbook-contracts.md`
- `docs/ARCHITECTURE.md`
- `docs/decisions/0012-linkedin-only-project-scope.md`

## Acceptance Criteria

- Web UI exposes a **Post Drafts** surface (sidebar view or integrated panel)
  listing markdown drafts from `POST_DIR`, with search/filter and linkage to
  workbook rows when the LinkedIn cell references the file.
- Operators can open a draft in an in-browser **rich text editor** that feels
  comparable to basic Word/Google Docs editing (not raw markdown textarea only):
  bold/italic/underline, headings, bullet/numbered lists, links, undo/redo,
  paste-from-Word cleanup (best-effort).
- **Save** writes the edited body back into the markdown file, preserving the
  existing file scaffold (`# Post …`, `## News`, `## Image`, `## Generated Post`).
  Only the `## Generated Post` body is operator-editable in MVP; metadata
  sections remain read-only unless opened in advanced/raw mode.
- `GET` and `PUT` (or equivalent) `/api/posts` endpoints read/write through a
  shared `post_draft_store` adapter; path validation rejects traversal outside
  `POST_DIR`.
- Dashboard row actions include **Edit draft** when the row's LinkedIn draft
  resolves to a post markdown file; after save, assisted posting and inspect
  preview show updated content.
- Unsaved-change warning before navigation; explicit Save / Discard; clear error
  toasts on locked files or write failures.
- Optional file backup before overwrite (align with workbook backup semantics when
  feasible — at minimum timestamped `.bak` beside the file or in output backups).
- LinkedIn-only scope preserved; editor labels and flows reference LinkedIn drafts
  only in MVP.
- Tests cover markdown round-trip, API validation, and editor save integration;
  harness matrix updated when implemented.

## Design Notes

- Commands: save post draft body; optional create-backup-before-save.
- Queries: list posts; get post with parsed sections; workbook inspect linkage.
- API: `/api/posts`, `/api/posts/<relative_path>`, optional
  `/api/posts/<relative_path>/raw` for advanced operators.
- Tables: none new; `output/posts/*.md` remain canonical draft storage.
- Domain rules: parse at boundary via `parse_post_markdown` / shared serializer;
  never write outside `POST_DIR`; preserve posting pipeline contract.
- UI surfaces: Post Drafts view; Dashboard **Edit draft** action; rich text
  editor component (library choice deferred to exec phase — e.g. TipTap, Quill,
  TinyMCE).

## Story Packet

- `docs/stories/epics/E20-web-ui-post-draft-editor/US-020-web-ui-post-draft-editor/overview.md`
- `docs/stories/epics/E20-web-ui-post-draft-editor/US-020-web-ui-post-draft-editor/design.md`
- `docs/stories/epics/E20-web-ui-post-draft-editor/US-020-web-ui-post-draft-editor/execplan.md`
- `docs/stories/epics/E20-web-ui-post-draft-editor/US-020-web-ui-post-draft-editor/validation.md`

## Validation

When updating durable proof status, use numeric booleans:

`scripts/bin/harness-cli story update --id US-020 --unit 1 --integration 1 --e2e 1 --platform 1`

| Layer | Expected proof |
| --- | --- |
| Unit | Markdown parse/serialize round-trip; path guard |
| Integration | Flask list/get/put post routes |
| E2E | Manual open → edit → save → posting preview reads new text |
| Platform | `python -m pytest tests/` passes |
| Release | Operator edits `output/posts` drafts without external editor |

## Harness Delta

- New epic E20 and US-020 story packet for Web UI post draft editing.
- Register US-020 in harness matrix as **planned**.

## Evidence

None yet — planning only.