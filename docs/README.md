# Documentation Map

This directory holds the Harness operating model and the living product
contract for **Trillion News Auto Post System**.

## Main Files

- `HARNESS.md`: how humans and agents collaborate.
- `FEATURE_INTAKE.md`: how prompts become tiny, normal, or high-risk work.
- `ARCHITECTURE.md`: application architecture, boundaries, and layering.
- `TEST_MATRIX.md`: legacy proof map; current proof status is queried with
  `scripts/bin/harness-cli query matrix`.
- `HARNESS_BACKLOG.md`: legacy improvement list; current improvement records
  are stored with `scripts/bin/harness-cli backlog`.
- `GLOSSARY.md`: shared terms.

## Folders

- `product/`: current product truth (`overview.md`, workbook contracts, release
  boundaries).
- `stories/`: feature packets, backlog, and epic folders (e.g. US-018).
- `decisions/`: durable decisions and tradeoffs (scope gate:
  `0012-linkedin-only-project-scope.md`).
- `demo/`: concrete walkthroughs that show how the harness transforms input
  into agent-ready work.
- `templates/`: reusable spec-intake, story, plan, decision, and validation
  formats.

## Current State

The application is implemented and operator-ready on a local machine:

- harvest, draft generation, workbook review, assisted LinkedIn posting
- Web UI dashboard, session onboarding, scheduling, and run history
- shared posting core used by CLI, Web UI, and scheduler

**Active scope:** LinkedIn only (`docs/decisions/0012-linkedin-only-project-scope.md`).

**Agent entrypoint:** `AGENTS.md` at the repo root.

**Proof:** `python -m pytest tests/` and `scripts/bin/harness-cli query matrix`.

Harness docs describe how to change the product safely; they do not imply the
app is unimplemented.