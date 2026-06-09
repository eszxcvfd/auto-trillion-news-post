# E2E Smoke Report

Date: 2026-06-09  
Environment: local dev, `.venv/bin/python main.py web --port 8080`  
Workbook: `output/Trillion $ news.xlsx`

## API Smoke (`scripts/smoke/e2e_smoke.sh`)

Command:

```bash
./scripts/smoke/e2e_smoke.sh http://127.0.0.1:8080
```

Result: **11 passed, 0 failed**

| Check | Result |
| --- | --- |
| Root HTML loads | PASS |
| `/api/config` | PASS |
| `/api/workbooks` | PASS |
| `/api/workbook/inspect` | PASS |
| `eligible_platforms` in inspect payload | PASS |
| `/api/plan` for 8 platforms | PASS |
| `/api/sessions/status` | PASS |
| B3 platforms in session status | PASS |
| `/api/post/status` | PASS |
| `/api/schedules` | PASS |
| `/api/history` | PASS |

## Browser Smoke (Chrome DevTools MCP)

| Flow | Result | Notes |
| --- | --- | --- |
| Dashboard workbook inspection | PASS | 3 sheets, row table, Post actions visible |
| Session Status view | PASS | 8 platforms listed; TikTok/YouTube show `Best-effort MVP` badge |
| Draft Run view | PASS | Harvest + generate form visible |
| Manual post from Dashboard (LinkedIn) | PASS | Row 2 Post launched LinkedIn job, browser prep modal reached `Operator Review Required` |
| Skip post job (LinkedIn) | PASS | Skip Platform returned `Platform post skipped!` |
| Manual post Facebook (row 1) | PASS | Platform picker → Facebook → `Operator Review Required` → Skip |
| Manual post X (row 1) | PASS | Single eligible platform auto-launched X → `Operator Review Required` → Skip |
| `/api/post/status` after skip | PASS | Returns `"active":false` (no stale `active:true` on terminal `skipped` job) |

## Operator Notes

- LinkedIn/Facebook/X sessions were already `Ready` from prior onboarding.
- B2/B3 platforms show `Login Required` until operator onboarding is completed.
- Full social publish confirmation was not executed in smoke to avoid writing live posts.
- Facebook/X smoke used row 1 (`Payment services trillion $`) with injected E2E draft cells; Facebook skip was written back before X run.

## Re-run

```bash
.venv/bin/python main.py web --port 8080
./scripts/smoke/e2e_smoke.sh http://127.0.0.1:8080
```