# 0007 Technology Stack and Gemini AI Provider

Date: 2026-06-04

## Status

Accepted, clarified 2026-06-05

## Context

The Trillion News Auto Post System requires a defined runtime, browser
automation tools, storage tools, and a specific AI provider for English post
generation. The approved brownfield spec and architecture now also clarify
which responsibilities belong to Python, workbook storage, optional local
database storage, and browser automation.

## Decision

We decided on the following MVP technology direction:

1. **Runtime**: Python 3.11+ remains the single backend/runtime language for
   CLI flows, harvest/generate logic, posting orchestration, and future local
   web or scheduling features.
2. **Scraping & Browser Automation**: Playwright is the browser automation
   layer for news search, screenshots, session reuse, and social posting flows.
3. **Workbook I/O**: `openpyxl` is the workbook adapter for both the internal
   compatibility workbook and the business workbook `Trillion $ news.xlsx`.
4. **Primary Storage**: Local filesystem is the default persistence layer for
   workbook files, screenshots, cached media, generated posts, session
   directories, logs, and backups.
5. **AI Provider**: Google Gemini API is the default AI provider for draft
   generation.
6. **AI Models**: `gemini-1.5-flash` or other approved Gemini-family models.
7. **Optional Operational Database**: A local SQLite database may be added
   later for scheduling, run history, and dashboard-oriented operational
   metadata, but it does not replace Excel as the operator source of truth.

## Alternatives Considered

1. **OpenAI API**: Considered as it was in the recommended stack template. Rejected because the user specifically requested Gemini API keys and Gemini/Gemma models.
2. **Selenium/Puppeteer**: Playwright was selected over Selenium for better performance, faster screenshot capture, and easier CLI setup.

## Consequences

Positive:
- one runtime owns product logic, reducing brownfield split-brain risk
- Playwright and `openpyxl` responsibilities are separated more clearly
- local file persistence matches operator expectations and MVP complexity
- Gemini remains explicit as the AI provider instead of an abstract placeholder

Tradeoffs:
- the operator must provide a valid `GEMINI_API_KEY` in the local environment
- browser selectors and platform flows remain operationally fragile
- local storage means workbook locking, backup, and session safety stay
  important operational concerns
- future SQLite use must remain carefully scoped so it does not compete with
  Excel as the business source of truth

## Follow-Up

- use `docs/ARCHITECTURE.md` as the allocation map for these technologies
- add durable decisions when source-of-truth hierarchy or storage roles change
