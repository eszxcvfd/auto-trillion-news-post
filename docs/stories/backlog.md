# Story Backlog

This backlog translates the approved `SPEC.md` release boundaries into
candidate implementation slices.

## Active Work

_No story packets are queued for execution._

## Recently Completed

| Story | Slice | Status |
| --- | --- | --- |
| US-020 | Web UI post draft editor (Word-like, `output/posts/`) | implemented |
| US-019 | Web UI keyword and article management | implemented |

See `docs/stories/epics/E20-web-ui-post-draft-editor/US-020-web-ui-post-draft-editor/`.
| US-018 | LinkedIn-only project scope (config, runtime, UI, docs) | implemented |

See `docs/stories/epics/E19-web-ui-content-management/US-019-web-ui-keyword-article-management/`.

See `docs/stories/epics/E18-linkedin-only-scope/US-018-linkedin-only-scope/`.

## Active Brownfield Slices

| Story | Slice | Status |
| --- | --- | --- |
| US-006 | Business workbook ingestion and dual-contract mapping | implemented |
| US-007 | Shared posting core plus `Link Post` parser/writer | implemented |
| US-008 | Result write-back, backup safety, and retry semantics | implemented |
| US-009 | Web UI operator surface | implemented |
| US-010 | Local scheduling and run history | implemented |
| US-011 | Web UI session onboarding and reuse | implemented |
| US-012 | Manual platform selection for `post` action | implemented (LinkedIn-only at runtime) |
| US-013 | Web UI manual draft generation | implemented |
| US-016 | B1 Facebook and X assisted posting adapters | implemented — **inactive scope** per 0012 |
| US-017 | Platform-isolated auto posting workflows | implemented — **LinkedIn active** |

## Historical Multi-Platform Slices (Inactive Scope)

These stories shipped code that remains for workbook compatibility. They are not
active supported behavior after decision `0012-linkedin-only-project-scope.md`.

| Story | Slice | Status |
| --- | --- | --- |
| US-014 | B2 image-first platform posting (Instagram/Pinterest/Threads) | implemented — inactive |
| US-015 | B3 best-effort TikTok and YouTube posting | implemented — inactive |

## Release Mapping

| Release | Main slices | Status |
| --- | --- | --- |
| Current | US-020 Web UI post draft editor (`output/posts/`) | implemented |
| Release D | US-019 operator content management from Web UI | implemented |
| Release E | US-020 Word-like post draft editing in Web UI | implemented |
| Release A | US-001 to US-005 baseline stabilization | implemented |
| Release B1 | US-006, US-007, US-008, US-016 (LinkedIn active) | implemented |
| Release B2 | US-014 Instagram/Pinterest/Threads | implemented — inactive |
| Release B3 | US-015 TikTok and YouTube | implemented — inactive |
| Release C | US-009, US-010, US-011, US-012, US-013 | implemented |

## Historical Baseline

| Story | Description | Status |
| --- | --- | --- |
| US-001 | Local Project Setup | implemented |
| US-002 | Search & Filter Logic | implemented |
| US-003 | Save to Excel and Screenshot | implemented |
| US-004 | AI Post Generation | implemented |
| US-005 | Assisted Posting | implemented |