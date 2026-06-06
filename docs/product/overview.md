# Product Overview — Trillion News Auto Post System

Derived from [SPEC.md](/home/trung/Documents/2026/project/auto-trillion-news-post/SPEC.md)
and [docs/ARCHITECTURE.md](/home/trung/Documents/2026/project/auto-trillion-news-post/docs/ARCHITECTURE.md).

## Position

The Trillion News Auto Post System is a **local operator tool** for a content
or marketing team. It is not a SaaS platform and not a multi-tenant service.

The product serves one end-to-end operating goal:

1. Harvest trillion-related news from search engines.
2. Generate social drafts for target platforms.
3. Let the operator review or edit drafts in Excel.
4. Post only eligible row/platform pairs.
5. Write the posting result back into the workbook.

## Primary User

Primary user:

- Content Admin / Marketing Operator

Working assumptions:

- comfortable with Excel and browser-based workflows
- can log into social platforms manually when required
- prefers local files and visible browser automation over hidden background
  systems

## Current Baseline

The repo already implements a CLI-centered baseline:

- `init`
- `search`
- `generate`
- `run`
- `post`

Implemented baseline capabilities:

- keyword-based news search with Playwright
- trillion-related filtering and deduplication
- screenshot capture for retained news cards
- Gemini draft generation
- internal 14-column workbook persistence
- assisted LinkedIn posting with operator confirmation

These are current product truths and should not be described as hypothetical.

## Target v2

The approved v2 direction expands the baseline into two connected pipelines.

### Pipeline A — Harvesting and Draft Generation

Pipeline A should:

- read keywords from file or equivalent operator input
- search and filter trillion-relevant news
- capture local screenshots
- generate 8 platform drafts
- write title, image reference, and drafts into the business workbook

### Pipeline B — Business Workbook Posting

Pipeline B should:

- read eligible rows from the business workbook
- honor operator edits made in Excel
- resolve image sources from local files or Google Drive URLs
- apply selective posting rules from `Link Post`
- post to supported platforms with persistent sessions
- write back result lines per platform

## Control Surfaces

Required surface today:

- CLI

Planned surfaces:

- Web UI for non-technical operation
- Scheduling for local timed runs after the posting core is stable

Brownfield rule:

- new surfaces must call the same business rules and posting core
- new surfaces must not fork their own workbook or posting logic

## Golden Flow

```text
keywords
  -> search and filter news
  -> capture screenshots
  -> generate 8 drafts
  -> write drafts into Trillion $ news.xlsx
  -> operator review/edit gate
  -> select eligible row/platform pairs
  -> post through platform sessions
  -> write Link Post results back into Trillion $ news.xlsx
```

## Product Boundaries

In scope:

- local browser-driven operation
- review-through-Excel workflow
- selective posting
- per-platform result visibility
- default posting limit of 2 eligible rows per platform per run

Out of scope for MVP:

- multi-tenant cloud architecture
- mobile app
- direct Google Sheets integration
- complex media editing pipeline
- captcha bypass or anti-bot evasion

## Capability Status

Implemented now:

- baseline CLI flow
- local harvesting
- Gemini generation
- internal workbook compatibility
- assisted LinkedIn posting

Planned next:

- business workbook ingestion
- `Link Post` parser/writer
- shared posting core
- LinkedIn, Facebook, and X end-to-end support
- later rollout for Instagram, Pinterest, Threads, TikTok, and YouTube

Future only:

- Web UI
- scheduling
- dashboard/history backed by operational storage
