# Release Boundaries

Derived from [SPEC.md](/home/trung/Documents/2026/project/auto-trillion-news-post/SPEC.md)
and [docs/decisions/0012-linkedin-only-project-scope.md](/home/trung/Documents/2026/project/auto-trillion-news-post/docs/decisions/0012-linkedin-only-project-scope.md).

This file turns the seed spec into staged product rollout boundaries.

## Current Release — LinkedIn-Only Scope (US-018)

**Status:** implemented (2026-06-09).

Scope:

- LinkedIn as the sole supported platform for draft generation, planning,
  assisted posting, scheduling, and session onboarding
- config and Web UI treat LinkedIn as a fixed default (no editable platform
  picker)
- runtime rejection of non-LinkedIn requests
- workbook compatibility for legacy non-LinkedIn columns without active
  supported behavior
- dashboard hides rows without a LinkedIn footprint; repair prunes operator-
  stray legacy rows

Done when:

- product docs, UI copy, and agent instructions consistently describe
  LinkedIn-only scope
- tests and harness matrix evidence show LinkedIn-only enforcement
- operators can run the full golden flow on LinkedIn without multi-platform
  controls surfacing as supported

## Release A — Brownfield Stabilization

Scope:

- keep `init`, `search`, `generate`, `run`, and `post` stable
- preserve the internal compatibility workbook
- align docs, logging assumptions, and error handling with current truth

Done when:

- baseline implemented behavior is clearly separated from superseded multi-
  platform direction
- current tests still prove the baseline

**Status:** implemented.

## Release B1 — Business Workbook + LinkedIn Posting Foundation

Scope:

- write Pipeline A results into `Trillion $ news.xlsx`
- ingest multi-sheet business workbook rows
- normalize headers and content cells
- parse and write `Link Post`
- add selective posting
- add image resolution
- support **LinkedIn** through platform-owned posting workflows behind shared
  eligibility and write-back orchestration

Done when:

- the operator can move from keyword input to reviewed workbook drafts without
  manual schema fixes
- LinkedIn can post eligible rows and write back per-platform results

**Status:** implemented (LinkedIn active; historical B1 also shipped Facebook/X
adapters — now inactive per decision 0012).

## Release B2 — Image-First and Mid-Risk Platforms (Historical)

Scope (superseded by decision 0012):

- Instagram, Pinterest, Threads
- stronger media handling and session stability for these platforms

**Status:** code landed historically; **not active project scope**.

## Release B3 — High-Risk / Best-Effort Platforms (Historical)

Scope (superseded by decision 0012):

- TikTok image/photo mode
- YouTube Community Post mode
- best-effort permalink capture

**Status:** code landed historically; **not active project scope**.

## Release C — Web UI and Scheduling

Scope:

- Web UI for non-technical operation
- Web UI session onboarding and refresh for **LinkedIn**
- local scheduling
- dashboard/history for run visibility

Done when:

- the operator can choose a workbook, manage saved LinkedIn sessions, run jobs,
  and inspect status without using the CLI directly
- scheduled runs and run history are visible and recoverable

**Status:** implemented.