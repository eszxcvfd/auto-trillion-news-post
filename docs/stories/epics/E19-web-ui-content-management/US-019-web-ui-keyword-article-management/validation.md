# Validation

## Proof Strategy

Story is done when operators can manage keywords and perform safe article row
actions entirely from the Web UI, with CLI/scheduler harvest still reading the
same canonical keyword file and workbook mutations respecting backup + LinkedIn-only
scope.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | keyword normalize/serialize round-trip; duplicate/empty rejection; disabled keyword skipped by loader |
| Unit | delete row compacts sheet; regenerate calls shared generate path (mocked Gemini) |
| Integration | GET/PUT `/api/keywords` persists to temp keywords file; draft run sees updated list |
| Integration | DELETE workbook row creates backup; inspect no longer returns row; regenerate updates LinkedIn cell |
| E2E | manual: add keyword in UI → Draft Run harvest uses it; delete article row → gone from Dashboard |
| Platform | `python -m pytest tests/` passes |
| Logs/Audit | keyword save and row delete/regenerate emit structured log fields |

## Fixtures

- temp `keywords.txt` with comments and duplicates
- business workbook with multiple sheets and LinkedIn drafts
- row with broken draft ref (regenerate should repair or replace per existing rules)

## Commands

```text
.venv/bin/activate
python -m pytest tests/
python main.py web --port 8080
# manual smoke: Keywords view + Dashboard row actions
```

## Acceptance Evidence

- pytest: **159 passed** (`python -m pytest tests/`)
- harness: `story update --id US-019 --status implemented`
- Keywords view: sidebar **Keywords** with add/toggle/remove + PUT `/api/keywords`
- Dashboard: per-row **Regen** and **Delete** via workbook APIs with confirm modals
- Draft Run: read-only canonical keywords path; harvest uses same file via `load_keywords()` → `keywords_store`