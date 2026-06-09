# Agent Instructions

## Project

**Trillion News Auto Post System** — local operator tool for harvesting
trillion-related news, generating LinkedIn drafts with Gemini, reviewing rows in
`Trillion $ news.xlsx`, and posting through assisted browser automation.

This is not SaaS. Runtime is local on an operator-controlled machine. Business
truth lives in Excel; operational history uses local SQLite (`scheduler.db`).

## Active Product Scope

As of decision `docs/decisions/0012-linkedin-only-project-scope.md`:

- **Supported platform:** LinkedIn only (draft generation, planning, posting,
  scheduling, session onboarding).
- **Fixed default:** config and Web UI do not expose editable multi-platform
  preferences.
- **Workbook compatibility:** legacy Facebook/X/… columns may still exist in old
  workbooks and are read-only residue. Repair flows may prune operator-stray
  rows that have no LinkedIn draft or posting status.
- **Non-LinkedIn runtime requests** must be rejected explicitly.

Do not re-expand multi-platform support unless project scope changes again.

## Read First

Harness baseline (always):

- `README.md`
- `docs/HARNESS.md`
- `docs/FEATURE_INTAKE.md`
- `docs/ARCHITECTURE.md`
- `docs/CONTEXT_RULES.md`
- `scripts/bin/harness-cli query matrix`

Product truth for this repo (read before behavior changes):

- `SPEC.md` — seed contract; do not treat every section as current release scope
- `docs/product/overview.md` — current product position
- `docs/product/workbook-contracts.md` — Contract A vs Contract B rules
- `docs/product/release-boundaries.md` — staged rollout history
- `docs/decisions/0012-linkedin-only-project-scope.md` — current scope gate
- `docs/stories/backlog.md` — implemented vs planned slices

## Key Code Paths

| Area | Location |
| --- | --- |
| CLI entry | `main.py` |
| Business workbook ingest/save/repair | `src/business_workbook.py` |
| Posting eligibility & plan | `src/posting_core.py` |
| LinkedIn scope enforcement | `src/platform_capabilities.py` |
| Web UI (Flask) | `src/web_ui.py`, `src/templates/index.html` |
| Assisted posting | `src/assisted_posting.py` |
| Platform workflows | `src/platform_workflows/` |
| Scheduler & run history | `src/scheduler.py` |
| Write-back & backups | `src/writeback.py` |

## Operator Commands

```bash
# Activate venv first when present
. .venv/bin/activate

# CLI baseline
python main.py init
python main.py search
python main.py generate
python main.py run
python main.py post

# Web UI operator surface (light/dark theme toggle in header)
python main.py web --port 8080

# Validation
python -m pytest tests/
# or: python -m unittest discover tests

# Harness proof matrix
scripts/bin/harness-cli query matrix
```

Default paths (override via `.env`):

- Workbook: `output/Trillion $ news.xlsx`
- Images: `output/Ảnh Trillion $ news/`
- Posts: `output/posts/`

## Implementation Rules

1. **Single posting core** — CLI, Web UI, and scheduler must share
   `posting_core`, workbook adapters, and write-back semantics.
2. **Parse at boundaries** — workbook headers, `Link Post`, draft file refs, and
   config/env are normalized before inner logic (see `docs/ARCHITECTURE.md`).
3. **Excel is business source of truth** — SQLite stores scheduling/history, not
   draft review state.
4. **Docs follow scope** — stop describing non-LinkedIn platforms as supported
   in product copy, UI labels, or new feature work.
5. **Proof before done** — run targeted tests; update story validation or
   harness matrix when behavior changes.

## Recent Scope Closure

| Story | Topic | Harness status |
| --- | --- | --- |
| US-018 | LinkedIn-only project scope | implemented |

<!-- HARNESS:BEGIN -->
## Harness

This repo uses Harness. Before work, read:

- `README.md`
- `docs/HARNESS.md`
- `docs/FEATURE_INTAKE.md`
- `docs/ARCHITECTURE.md`
- `docs/CONTEXT_RULES.md`
- `scripts/bin/harness-cli query matrix` on macOS/Linux, or `.\scripts\bin\harness-cli.exe query matrix` on Windows

Use the Rust Harness CLI at `scripts/bin/harness-cli` on macOS/Linux or
`scripts/bin/harness-cli.exe` on Windows as the main operational tool.
<!-- HARNESS:END -->