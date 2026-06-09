# Overview

## Current Behavior

The repo currently supports a multi-platform product direction:

- draft generation can target several social platforms
- posting plans and workflow dispatch can include multiple platforms
- Web UI session management and scheduling expose multiple platform choices
- isolated posting workflows exist for LinkedIn and additional provider groups

This creates more operational surface area than the current project mandate
requires.

## Target Behavior

Per current leader direction, the project must operate as a **LinkedIn-only**
tool.

After this story is complete:

- LinkedIn is the only supported platform for draft generation, planning,
  assisted posting, scheduling, and session management
- config and UI expose LinkedIn as the fixed default and do not allow operators
  to switch to another platform
- runtime dispatch rejects non-LinkedIn platform requests clearly
- previously added non-LinkedIn platform paths are treated as out of scope for
  this project release

## Affected Users

- Content Admin / Marketing Operator
- Developers maintaining platform automation

## Affected Product Docs

- `docs/product/overview.md`
- `docs/product/release-boundaries.md`
- `docs/ARCHITECTURE.md`
- `docs/decisions/0011-platform-isolated-posting-workflows.md`

## Non-Goals

- changing the workbook file format in this story
- changing `Link Post` write-back syntax beyond LinkedIn-only operational use
- reintroducing any second platform as an optional toggle
- weakening operator confirmation or session boundaries
