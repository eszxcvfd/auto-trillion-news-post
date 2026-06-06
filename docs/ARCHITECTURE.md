# Architecture

This document defines the application architecture for the brownfield
**Trillion News Auto Post System** based on the approved `SPEC.md`.

The repo already has working Python code, but the target v2 architecture is
larger than the current baseline. This document exists to make that expansion
explicit without confusing current implementation with planned capability.

## Architecture Position

This system is a **local operator tool**, not a SaaS platform.

- Primary operator surface today: CLI
- Future operator surface: Web UI
- Runtime model: local execution on an operator-controlled machine
- Main workflow: harvest news, generate drafts, review in Excel, post to social
  platforms, write results back into Excel
- Priority: operational stability and recoverability over maximal automation

Brownfield rule:

- Baseline commands `init`, `search`, `generate`, `run`, and `post` remain the
  compatibility contract unless a later decision explicitly changes them.
- Web UI, scheduler, and unified 8-platform posting are target capabilities,
  not baseline capabilities.

## Discovery Before Shape

Before adding or reshaping implementation, identify:

- Product surfaces:
  CLI is required. Web UI is planned. Mobile and desktop app shells are out of
  scope.
- Runtime stack:
  Python 3.11+, Playwright, `openpyxl`, local filesystem persistence, and
  Google Gemini.
- Core domains:
  harvested news items, business workbook rows, platform drafts, posting
  results, platform sessions, and future posting jobs.
- Boundary inputs:
  keywords, workbook rows, image sources, generated drafts, browser state,
  config, environment variables, and provider responses.
- Validation ladder:
  unit checks for parsing/filtering/validation, workflow-level integration
  checks for workbook flows, and manual operator proof for browser-posting
  steps.

Record stack or architecture choices in `docs/decisions/` when they
meaningfully constrain future work.

## Technology Allocation

The approved technical direction in `SPEC.md` and
`docs/decisions/0007-technology-stack-gemini.md` maps to the architecture like
this.

### Python 3.11+

Python is the application runtime for:

- CLI entrypoints and orchestration
- harvesting pipeline logic
- workbook parsing and write-back
- AI integration with Gemini
- posting core and platform adapters
- future web backend if a web surface is introduced
- future scheduling and local job execution if scheduling is introduced

Python should remain the single backend language for the MVP and brownfield
refactor to avoid splitting business logic across multiple runtimes.

### Playwright

Playwright is used for browser automation responsibilities only:

- searching Google/Bing news
- capturing screenshots of retained news cards
- loading persistent browser sessions
- checking login state per platform
- opening composers or post forms
- filling draft content
- uploading images when required
- submitting posts
- attempting permalink/status capture after post

Playwright should not own workbook parsing, row selection, or posting decision
logic.

### openpyxl

`openpyxl` is used for workbook I/O responsibilities:

- internal compatibility workbook reads and writes
- business workbook reads and writes
- header normalization and column mapping
- `Link Post` field preservation and updates
- optional backup creation before write-back

Workbook logic belongs in dedicated adapters/services, not inside platform
automation modules.

### Google Gemini

Google Gemini is used only for AI draft generation:

- generate English drafts from harvested news inputs
- produce platform-suitable draft text
- support the 8-target-platform content generation goal in v2

Gemini is not part of posting automation, session handling, or workbook
write-back.

### Filesystem Storage

Local filesystem storage is the default persistence layer for MVP operation:

- workbook files
- screenshots
- downloaded or cached images
- generated post markdown files
- session directories
- logs
- temporary artifacts and backups

This is the primary operational storage model today.

### Database

There is **no required application database in the current baseline MVP flow**.

Current source-of-truth model:

- business truth for the customer flow lives in Excel
- compatibility truth for the legacy baseline lives in the internal workbook
- operational artifacts live on the local filesystem

If later releases add scheduling, job history, or dashboard history, a **local
SQLite database** is the approved direction for:

- scheduled job definitions
- run history
- per-run/per-platform operational logs
- retry or audit-friendly execution metadata

Important boundary rule:

- SQLite, if introduced, supports operational history and scheduling.
- SQLite must not replace `Trillion $ news.xlsx` as the business
  source of truth for draft review and posting decisions in MVP.
- The Harness durable layer database is repo tooling, not the application
  product database.

## Source-of-Truth Contracts

This project must keep two workbook contracts explicit.

### Internal Compatibility Workbook

The current baseline code uses a 14-column internal workbook contract for
harvest and generation compatibility.

This workbook exists to preserve current CLI behavior during brownfield
refactor.

### Business Workbook

The target operator-facing workbook for v2 is:

```text
Trillion $ news.xlsx
```

This workbook is the business source of truth for:

- generated drafts after Pipeline A
- operator review and manual draft edits
- selective posting decisions in Pipeline B
- per-platform write-back via `Link Post`

Future implementation must not collapse the internal workbook and the business
workbook into one ambiguous model.

## Default Layering

The recommended layering for this project is:

```text
domain
  <- application
      <- infrastructure
          <- interface
              <- app surfaces
```

### Domain

Owns stable business concepts and rules:

- `NewsItem`
- future `BusinessWorkbookRow`
- `PlatformName`
- `ImageSource`
- `PlatformPostResult`
- selective posting rules
- platform capability rules
- status vocabulary such as `pending`, `skip`, `error`, `login-required`,
  `posted-no-link`

Domain code should not know about Playwright selectors, workbook libraries, UI
handlers, or environment variables.

### Application

Owns use cases and orchestration logic:

- harvest news
- generate drafts
- ingest workbook rows
- resolve image sources
- choose eligible rows per platform
- run posting attempts
- write posting results
- dry-run planning
- session status checks

Application code coordinates domain rules and calls infrastructure ports.

### Infrastructure

Owns concrete integrations:

- Playwright browser automation
- Gemini API client
- `openpyxl` workbook adapters
- filesystem storage
- future SQLite job store
- logging implementation

Infrastructure satisfies application needs but should not redefine business
rules.

### Interface

Owns input/output adapters for a chosen surface:

- CLI argument parsing
- CLI output formatting
- future web request/response DTOs
- future web presenters and handlers

Interface translates surface input into application commands and translates
application results back into operator-facing output.

### App Surfaces

Owns the user-facing shell:

- current CLI surface
- future web UI surface

Surfaces should remain thin and should not directly implement posting logic,
workbook rules, or provider-specific decision logic.

## Candidate Structure

The current repo is still relatively flat, but the target structure should
evolve toward this layout when implementation stories justify it:

```text
main.py
src/
  domain/
    entities/
      news_item.py
      business_workbook_row.py
      platform_session.py
    value_objects/
      platform_name.py
      image_source.py
      link_post_entry.py
    services/
      posting_eligibility.py
      platform_capabilities.py

  application/
    commands/
      harvest_news.py
      generate_drafts.py
      post_from_workbook.py
      dry_run_posting.py
      refresh_sessions.py
    queries/
      inspect_workbook.py
      list_posting_candidates.py
      get_session_status.py
    handlers/
      harvest_handler.py
      generate_handler.py
      posting_handler.py

  infrastructure/
    ai/
      gemini_writer.py
    browser/
      news_search_browser.py
      session_store.py
      platforms/
        linkedin.py
        facebook.py
        x.py
        instagram.py
        pinterest.py
        threads.py
        tiktok.py
        youtube.py
    workbook/
      internal_workbook.py
      business_workbook.py
      link_post_parser.py
      backup_writer.py
    files/
      image_cache.py
      post_file_store.py
      path_resolver.py
    logging/
      run_logger.py
    scheduling/
      sqlite_job_store.py
      scheduler_service.py

  interface/
    cli/
      commands.py
      presenters.py
    web/
      routes.py
      presenters.py
      dto/
        posting_request.py
        workbook_selection.py
```

Current brownfield mapping:

- `main.py` currently mixes surface and orchestration responsibilities
- `src/searcher.py`, `src/ai_writer.py`, `src/excel_store.py`,
  `src/post_writer.py`, and `src/assisted_posting.py` are early infrastructure
  and application hybrids
- future refactor should extract responsibilities gradually, not by a blind
  rewrite

## Dependency Rule

Inner layers must not depend on outer layers.

| Layer | May depend on | Must not depend on |
| --- | --- | --- |
| domain | tiny pure utilities and standard library value types | Playwright, `openpyxl`, Gemini SDK, UI, env/process |
| application | domain | browser selectors, workbook concrete adapters, UI, provider SDKs |
| infrastructure | domain, application | CLI parsing, web handlers, UI presenters |
| interface | application plus DTOs/presenters | direct provider logic and domain internals bypass |
| app surfaces | interface contracts and app-facing clients | direct domain mutation without application layer |

Brownfield additions:

- `main.py` may orchestrate flows for now, but business logic should move
  inward over time.
- platform-specific automation must not own workbook parsing or business row
  selection
- workbook adapters must not own browser interaction logic
- future UI and scheduler layers must call the same posting core, not fork
  separate business logic

## Parse-First Boundary Rule

Unknown data must be parsed at boundaries before it enters inner code.

Boundaries in this project include:

- keyword files and CLI args
- environment variables and `config.yaml`
- rows from the internal compatibility workbook
- rows from `Trillion $ news.xlsx`
- `Link Post` text blocks
- local image paths and Google Drive sharing URLs
- Gemini responses
- Playwright page state and posting outcomes

Target flow:

```text
unknown input
  -> parser
  -> typed DTO or command
  -> application use case
  -> domain object/value object
```

Inner layers should prefer meaningful types such as:

- `Keyword`
- `NewsItemId`
- `BusinessSheetName`
- `PlatformName`
- `ImageSource`
- `PostDraft`
- `PlatformPostResult`

Brownfield parsing rules from `SPEC.md` are mandatory:

- workbook headers are trimmed before matching
- empty strings, whitespace-only values, and `.` mean no platform content
- missing `Link Post` is tolerated and created on write
- `Link Post` must be parsed and updated per platform line safely
- Google Drive links must be resolved before image-required posting steps

## Command/Query Boundary

If the product has both reads and writes, keep command/query separation clear
even when storage is simple.

- Commands mutate state and own workbook writes, file creation, generation, and
  posting attempts.
- Queries read state and format it for CLI output, dry-run previews, and future
  UI views.
- Shared business rules live in domain/application, not in CLI handlers or
  platform adapters.

Brownfield examples:

- `search`, `generate`, `run`, and `post` are command surfaces
- workbook inspection, session inspection, row eligibility, and dry-run output
  should behave like queries

## Observability Contract

Every meaningful Pipeline A or Pipeline B operation should emit a structured
log record with at least:

- `run_id`
- `timestamp`
- `sheet_name`
- `row_id`
- `platform`
- `action`
- `status`
- `message`

Recommended expanded fields:

- `duration_ms`
- `provider`
- `error_code`
- `retryable`

Audit-like posting results stored in workbooks are product records.
Application logs are operational records. Do not use one as a substitute for
the other.

For the current CLI baseline, human-readable console output is acceptable, but
future refactors should standardize these events into structured logs without
hurting operator usability.
