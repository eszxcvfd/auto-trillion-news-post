# Release Boundaries

Derived from [SPEC.md](/home/trung/Documents/2026/project/auto-trillion-news-post/SPEC.md).

This file turns the seed spec into staged product rollout boundaries.

## Release A — Brownfield Stabilization

Scope:

- keep `init`, `search`, `generate`, `run`, and `post` stable
- preserve the internal compatibility workbook
- align docs, logging assumptions, and error handling with current truth

Done when:

- baseline implemented behavior is clearly separated from target v2 behavior
- current tests still prove the baseline

## Release B1 — Business Workbook + Shared Posting Core

Scope:

- write Pipeline A results into `Trillion $ news.xlsx`
- ingest multi-sheet business workbook rows
- normalize headers and content cells
- parse and write `Link Post`
- add selective posting
- add image resolution
- support LinkedIn, Facebook, and X through the shared posting core

Done when:

- the operator can move from keyword input to reviewed workbook drafts without
  manual schema fixes
- LinkedIn, Facebook, and X can post eligible rows and write back per-platform
  results

## Release B2 — Image-First and Mid-Risk Platforms

Scope:

- Instagram
- Pinterest
- Threads
- stronger media handling and session stability for these platforms

Done when:

- these platforms respect the capability matrix
- duplicate posting is prevented through `Link Post`

## Release B3 — High-Risk / Best-Effort Platforms

Scope:

- TikTok image/photo mode when supported by the operator account and UI
- YouTube Community Post mode when supported by the operator channel
- best-effort permalink capture for these platforms

Done when:

- scope is clearly limited to the supported MVP modes
- these platforms are not misrepresented as full video pipelines

## Release C — Web UI and Scheduling

Scope:

- Web UI for non-technical operation
- local scheduling
- dashboard/history for run visibility

Done when:

- the operator can choose a workbook, run jobs, and inspect status without
  using the CLI directly
- scheduled runs and run history are visible and recoverable
