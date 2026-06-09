# Story Backlog

This backlog translates the approved `SPEC.md` release boundaries into
candidate implementation slices.

## Active Brownfield Slices

| Story | Slice | Status |
| --- | --- | --- |
| US-006 | Business workbook ingestion and dual-contract mapping | implemented |
| US-007 | Shared posting core plus `Link Post` parser/writer | implemented |
| US-008 | Result write-back, backup safety, and retry semantics | implemented |
| US-009 | Web UI operator surface | implemented |
| US-010 | Local scheduling and run history | implemented |
| US-011 | Web UI session onboarding and reuse | implemented |
| US-012 | Manual platform selection for `post` action | implemented |
| US-013 | Web UI manual draft generation | implemented |
| US-014 | B2 image-first platform posting (Instagram/Pinterest/Threads) | implemented |
| US-015 | B3 best-effort TikTok and YouTube posting | implemented |
| US-016 | B1 Facebook and X assisted posting adapters | implemented |

## Release Mapping

| Release | Main slices | Status |
| --- | --- | --- |
| Release A | US-001 to US-005 baseline stabilization | implemented |
| Release B1 | US-006, US-007, US-008, US-016 with LinkedIn/Facebook/X | implemented |
| Release B2 | Expand posting core to Instagram/Pinterest/Threads | implemented |
| Release B3 | TikTok and YouTube best-effort MVP modes | implemented |
| Release C | US-009, US-010, US-011, US-012, and US-013 | implemented |

## Historical Baseline

| Story | Description | Status |
| --- | --- | --- |
| US-001 | Local Project Setup | implemented |
| US-002 | Search & Filter Logic | implemented |
| US-003 | Save to Excel and Screenshot | implemented |
| US-004 | AI Post Generation | implemented |
| US-005 | Assisted Posting | implemented |
