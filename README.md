# Trillion News Auto Post System

Local operator tool for harvesting trillion-related news, generating **LinkedIn**
drafts with Gemini, reviewing content in Excel, and posting through assisted
Playwright browser automation.

This is not SaaS. It runs on an operator-controlled machine. Business truth lives
in `Trillion $ news.xlsx`; scheduling and run history use local SQLite
(`scheduler.db`).

## What It Does

```text
keywords
  -> search & filter trillion news (Playwright)
  -> capture screenshots
  -> generate LinkedIn draft (Gemini)
  -> write into Trillion $ news.xlsx
  -> operator reviews/edits in Excel
  -> post eligible rows to LinkedIn
  -> write Link Post result back to workbook
```

**Current scope:** LinkedIn only. Legacy workbook columns for other platforms may
still exist as read-only residue; runtime paths reject non-LinkedIn requests.
See `docs/decisions/0012-linkedin-only-project-scope.md`.

## Requirements

- Python 3.11+
- Google Gemini API key
- Playwright browsers (`playwright install` after pip install)
- A logged-in LinkedIn session (onboarded via Web UI or CLI-assisted flow)

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env        # set GEMINI_API_KEY
python main.py init
python main.py web --port 8080
```

Open `http://127.0.0.1:8080` for the operator dashboard (light/dark theme toggle
in the header).

First-time setup through the Web UI:

1. Confirm workbook path (`output/Trillion $ news.xlsx` by default).
2. Onboard LinkedIn session (browser login, then save session).
3. Run **Harvest & Generate** or use CLI `search` / `generate` / `run`.
4. Review drafts in Excel, then post from the dashboard or CLI.

## Configuration

Paths and secrets are set in `.env` (see `.env.example`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | — | Gemini draft generation |
| `EXCEL_FILE` | `./output/Trillion $ news.xlsx` | Business workbook |
| `IMAGE_DIR` | `./output/Ảnh Trillion $ news` | Screenshot storage |
| `POST_DIR` | `./output/posts` | Generated draft files |
| `HEADLESS` | `false` | Browser visibility for search/post |
| `MAX_POSTS_PER_RUN` | `5` | Posting cap per run |

Search filters, hashtags, and posting behavior are in `config.yaml`. Keywords
live in `keywords.txt` (created by `init` if missing).

`DEFAULT_PLATFORM` is fixed to LinkedIn; it is not an editable multi-platform
preference.

## CLI Commands

```bash
python main.py init              # create output dirs, .env, config, keywords
python main.py search            # harvest news from keywords.txt
python main.py generate          # generate LinkedIn drafts for harvested items
python main.py run               # search + generate in one step
python main.py post              # assisted LinkedIn posting from workbook
python main.py inspect-workbook  # validate workbook rows and eligibility
python main.py web --port 8080   # operator dashboard
```

### Scheduling

```bash
python main.py schedule add --name "Morning post" \
  --expression "0 9 * * *" --job-type post --limit 2

python main.py schedule list
python main.py schedule run-now --id 1
python main.py schedule history
```

## Web UI

The dashboard covers the full operator loop without using the CLI directly:

- Workbook inspection per sheet (rows with LinkedIn footprint only)
- Posting planner and eligibility preview
- Manual harvest & generate with run history
- LinkedIn session onboarding and status
- Assisted posting with operator confirmation
- Light/dark theme (saved in browser `localStorage`)

## Workbook

The operator-facing file is `Trillion $ news.xlsx` (Contract B). Active columns
for the current release:

- `#`, `Trillion $ news Title`, `Image link`, `Linkedin`, `Link Post`

`Link Post` stores per-platform result lines; only the LinkedIn line is active
in scope. The app can repair broken draft references, remove legacy stray rows
(title/image only, no LinkedIn draft), and compact empty row gaps so Excel row
counts match the dashboard.

Run repair from the Web UI or CLI when workbook and dashboard counts diverge.

## Project Layout

```text
main.py                 # CLI entry
config.yaml             # search, hashtags, posting defaults
keywords.txt            # harvest keywords
src/
  business_workbook.py  # ingest, save, repair, dashboard filter
  posting_core.py       # eligibility, Link Post, posting plan
  web_ui.py             # Flask dashboard API
  templates/index.html  # operator UI
  assisted_posting.py   # Playwright LinkedIn posting
  scheduler.py          # local schedules + run history
output/
  Trillion $ news.xlsx  # business workbook (default)
  Ảnh Trillion $ news/    # screenshots
  posts/                # draft markdown files
tests/                  # pytest suite
docs/                   # product contract, architecture, decisions
```

## Development

```bash
source .venv/bin/activate
python -m pytest tests/
```

Key docs before changing behavior:

- `docs/product/overview.md` — current product position
- `docs/product/workbook-contracts.md` — workbook rules
- `docs/ARCHITECTURE.md` — layering and boundaries
- `AGENTS.md` — agent/contributor entrypoint