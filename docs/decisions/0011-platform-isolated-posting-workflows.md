# 0011 Platform-Isolated Posting Workflows

Date: 2026-06-09

## Status

Accepted

## Context

Platform automation behavior diverged enough that a single shared posting-core
adapter raised regression risk. LinkedIn, Facebook, and the image-first or
best-effort platforms each need different composer handling, media rules, and
failure recovery, while workbook eligibility and `Link Post` write-back must
remain shared.

## Decision

Adopt platform-isolated posting workflows with a shared dispatch boundary:

1. **Shared orchestration**
   `posting_core` continues to own eligibility, `Link Post` parsing, and
   posting-plan generation.
2. **Platform-owned workflows**
   Each supported platform registers an isolated workflow under
   `src/platform_workflows/` with its own `workflow_id`.
3. **Single dispatch surface**
   CLI, Web UI, and scheduler posting paths dispatch through
   `platform_workflows.registry` instead of branching inside one monolithic
   adapter.
4. **Observability**
   Posting attempts and scheduler run details record `workflow_id` so failures
   can be attributed to one provider workflow.
5. **Workbook contract unchanged**
   `Link Post` semantics, selective posting, and write-back ownership stay in
   the existing shared contract.

## Alternatives Considered

1. Keep one shared posting core with growing platform branches.
   Rejected because selector drift in one provider would keep affecting
   unrelated platforms.
2. Split workbook and result semantics per platform.
   Rejected because it would break the accepted dual-workbook contract.
3. Move posting into separate standalone services.
   Rejected because it exceeds the local-runtime MVP boundary.

## Consequences

Positive:

- platform adapter changes stay isolated to one workflow module
- shared workbook truth and operator surfaces remain stable
- run history can identify which workflow failed

Tradeoffs:

- more modules to maintain, but with clearer ownership boundaries
- legacy imports from `platform_posting` remain as a compatibility facade

## Follow-Up

- keep new platform work inside `src/platform_workflows/`
- extend workflow-specific proof when a provider UI changes materially