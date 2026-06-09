# Validation

## Proof Strategy

Story is done when operators can browse, open, edit with a Word-like toolbar,
and save post drafts under `output/posts/` entirely from the Web UI, and
assisted posting / Dashboard preview reflect saved content without external
editors.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | parse scaffold + replace `## Generated Post` only; path traversal rejected |
| Unit | list posts; workbook linkage when LinkedIn cell references file |
| Unit | html/markdown round-trip preserves text used by `parse_post_markdown` |
| Integration | GET/PUT `/api/posts/<path>` on temp `POST_DIR` |
| Integration | save then `load_draft_from_cell` returns updated body |
| E2E | manual: Dashboard Edit draft → format text → Save → Post preview updated |
| Platform | `python -m pytest tests/` passes |
| Logs/Audit | `post_draft_save` log line with path and status |

## Fixtures

- sample `2026-06-09_001_payment_linkedin.md` with full scaffold
- workbook row with LinkedIn cell = `posts/…md` relative reference
- editor paste sample with bold/list from Word (best-effort smoke)

## Commands

```text
.venv/bin/activate
python -m pytest tests/
python main.py web --port 8080
# manual smoke: Post Drafts view + Edit draft from Dashboard
```

## Acceptance Evidence

- pytest: **165 passed** (`python -m pytest tests/`)
- harness: `story update --id US-020 --status implemented`
- Editor: Quill 2 (WYSIWYG) + marked/turndown for markdown round-trip
- API: `GET/PUT /api/posts` via `src/post_draft_store.py`
- UI: **Post Drafts** sidebar view; Dashboard **Edit** opens linked draft file
- Save creates `.bak` backup beside the markdown file