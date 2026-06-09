# Validation

## Proof Strategy

This story is done when the repo behaves as a LinkedIn-only project across
config, CLI, Web UI, scheduler, and posting dispatch, without silently allowing
other platform execution paths.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | config forces LinkedIn; capability/dispatch rejects non-LinkedIn; planning only returns LinkedIn |
| Integration | Web UI and scheduler endpoints expose LinkedIn-only controls and normalization |
| E2E | manual Web UI smoke shows LinkedIn as the only visible platform |
| Platform | `.venv/bin/python -m unittest discover tests` passes |
| Performance | unchanged for LinkedIn-only flows |
| Logs/Audit | non-LinkedIn requests fail with explicit LinkedIn-only messaging |

## Fixtures

- business workbook rows with LinkedIn drafts and historical non-LinkedIn draft cells
- scheduler rows with existing `platforms` values from older multi-platform runs
- Web UI responses containing config, planner, and session data

## Commands

```text
.venv/bin/python -m unittest discover tests
```

## Acceptance Evidence

- `2026-06-09`: `.venv/bin/python -m pytest tests/` passed with `146 passed`.
- Verified code paths now force LinkedIn as the fixed platform in:
  `src/config.py`, `main.py`, `src/platform_capabilities.py`,
  `src/business_workbook.py`, `src/scheduler.py`, `src/web_ui.py`,
  and `src/templates/index.html`.
- Existing workbooks with historical non-LinkedIn columns remain readable, but
  new workbook scaffolding and all operator-facing controls now operate on
  LinkedIn only.
