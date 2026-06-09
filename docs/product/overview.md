# Product Overview — Trillion News Auto Post System

Derived from [SPEC.md](/home/trung/Documents/2026/project/auto-trillion-news-post/SPEC.md),
[docs/ARCHITECTURE.md](/home/trung/Documents/2026/project/auto-trillion-news-post/docs/ARCHITECTURE.md),
and [docs/decisions/0012-linkedin-only-project-scope.md](/home/trung/Documents/2026/project/auto-trillion-news-post/docs/decisions/0012-linkedin-only-project-scope.md).

## Position

The Trillion News Auto Post System is a **local operator tool** for a content
or marketing team. It is not a SaaS platform and not a multi-tenant service.

The product serves one end-to-end operating goal:

1. Harvest trillion-related news from search engines.
2. Generate **LinkedIn** drafts with Gemini.
3. Let the operator review or edit drafts in Excel.
4. Post only eligible LinkedIn row targets.
5. Write the posting result back into the workbook.

## Primary User

Primary user:

- Content Admin / Marketing Operator

Working assumptions:

- comfortable with Excel and browser-based workflows
- can log into LinkedIn manually when onboarding or refreshing a saved session
- prefers local files and visible browser automation over hidden background
  systems

## Current Baseline

The repo implements a full local operator baseline:

- CLI: `init`, `search`, `generate`, `run`, `post`
- Web UI dashboard with workbook inspection, planner, session onboarding, and
  manual harvest/generate triggers
- Local scheduling and run history (`scheduler.db`)

Implemented capabilities:

- keyword-based news search with Playwright
- trillion-related filtering and deduplication
- screenshot capture for retained news cards
- Gemini LinkedIn draft generation
- internal 14-column workbook persistence
- business workbook (`Trillion $ news.xlsx`) ingest, repair, and write-back
- assisted LinkedIn posting with operator confirmation
- dashboard filtering that hides workbook rows without a LinkedIn footprint
- repair flows that prune operator-stray legacy rows and compact empty gaps

These are current product truths and should not be described as hypothetical.

## Active Scope — LinkedIn Only

Per decision `0012-linkedin-only-project-scope.md`:

- **Supported platform:** LinkedIn only (draft generation, planning, posting,
  scheduling, session onboarding).
- **Fixed default:** config and Web UI do not expose editable multi-platform
  preferences.
- **Runtime enforcement:** non-LinkedIn platform requests are rejected
  explicitly.
- **Workbook compatibility:** legacy Facebook/X/… columns may still exist in old
  workbooks as read-only residue. Repair may remove stray rows that have no
  LinkedIn draft or posting status.

Do not describe other platforms as supported in product copy, UI labels, or new
feature work unless project scope changes again.

## Pipelines

### Pipeline A — Harvesting and Draft Generation

Pipeline A:

- reads keywords from file or equivalent operator input
- searches and filters trillion-relevant news
- captures local screenshots
- generates **LinkedIn** drafts
- writes title, image reference, and draft into the business workbook

### Pipeline B — Business Workbook Posting

Pipeline B:

- reads eligible rows from the business workbook
- honors operator edits made in Excel
- resolves image sources from local files or Google Drive URLs
- applies selective posting rules from `Link Post` (LinkedIn line only in active
  scope)
- posts to LinkedIn with application-managed persistent sessions
- writes back result lines for LinkedIn

## Control Surfaces

Current surfaces (all share `posting_core` and workbook adapters):

- CLI
- Web UI (`python main.py web`)
- Local scheduler

Brownfield rule:

- new surfaces must call the same business rules and posting core
- new surfaces must not fork their own workbook or posting logic

## Golden Flow

```text
keywords
  -> search and filter news
  -> capture screenshots
  -> generate LinkedIn draft
  -> write draft into Trillion $ news.xlsx
  -> operator review/edit gate
  -> select eligible LinkedIn rows
  -> post through LinkedIn session
  -> write Link Post LinkedIn result back into Trillion $ news.xlsx
```

## Product Boundaries

In scope:

- local browser-driven operation
- review-through-Excel workflow
- selective LinkedIn posting
- LinkedIn result visibility in `Link Post`
- default posting limit of 2 eligible rows per run (LinkedIn)

Out of scope:

- multi-tenant cloud architecture
- mobile app
- direct Google Sheets integration
- complex media editing pipeline
- captcha bypass or anti-bot evasion
- supported posting to non-LinkedIn platforms in the current release

## Capability Status

Implemented now:

- baseline CLI flow
- local harvesting and Gemini generation
- internal and business workbook compatibility
- `Link Post` parser/writer and safe result write-back
- shared posting core with LinkedIn-only runtime enforcement
- Web UI operator surface (light/dark theme)
- Web UI session onboarding and reuse
- local scheduling and run history
- workbook repair, stray-row pruning, and dashboard row filtering

Inactive / historical (code may remain for workbook safety):

- multi-platform draft generation and posting (Facebook, X, Instagram, etc.)
- Web UI multi-platform controls

Future only:

- deeper operational analytics beyond current run history