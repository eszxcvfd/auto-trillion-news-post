# Exec Plan

## Goal

Let operators manage harvest keywords and workbook article rows from the Web UI
without manual file editing or CLI-only flows.

## Scope

In scope:

- keyword list CRUD in Web UI backed by `keywords.txt` adapter
- validation and normalization shared with `load_keywords()`
- Dashboard article actions: delete row (with backup), regenerate LinkedIn draft
- REST endpoints in `src/web_ui.py` calling application/workbook layers
- tests for API + adapter; manual operator smoke on Keywords + Dashboard
- doc updates: `README.md`, `docs/product/overview.md`, backlog, harness matrix

Out of scope (this story):

- keyword history / versioning
- bulk article import/export
- Google Sheets or cloud sync
- editing full draft body in Web UI (Excel remains editor)
- scheduler UI changes beyond consuming updated keywords file automatically

## Risk Classification

Risk flags:

- Existing behavior (harvest pipeline reads keywords file)
- Workbook writes (delete row, regenerate draft)
- Weak proof if only UI manually tested

Hard gates:

- any change to `keywords.txt` format must remain backward compatible with CLI
- row delete must use backup-enabled write path
- regenerate must not fork Gemini/workbook logic outside shared modules

## Work Phases (execution — not started)

1. **Keyword adapter** — extract read/write/normalize from `main.load_keywords()`
   into `src/` module; unit tests.
2. **Keywords API + UI** — GET/PUT `/api/keywords`, new Keywords view.
3. **Article commands** — delete row + regenerate draft in `business_workbook` /
   existing generate path; backup on delete.
4. **Article API + UI** — dashboard action buttons, confirm dialogs, toast errors.
5. **Integration** — Draft Run uses in-app keyword list; remove redundant path field
   or show read-only canonical path.
6. **Proof** — pytest, harness `story update`, validation evidence.

## Stop Conditions

Pause for human confirmation if:

- keyword file format must break `load_keywords()` compatibility
- delete row requires new workbook schema columns
- regenerate draft needs new AI prompt contract beyond current LinkedIn draft flow
- soft-hide (non-delete exclude) is mandatory vs delete+backup

## Suggested File Touch List (implementation reference)

| Area | Files |
| --- | --- |
| Keywords adapter | `src/keywords_store.py` (new), `main.py` |
| API | `src/web_ui.py` |
| Workbook ops | `src/business_workbook.py`, possibly `main.execute_generate` |
| UI | `src/templates/index.html` |
| Tests | `tests/test_keywords_store.py`, `tests/test_web_ui.py`, workbook tests |