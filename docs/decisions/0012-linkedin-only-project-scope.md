# 0012 LinkedIn-Only Project Scope

Date: 2026-06-09

## Status

Accepted

## Context

The repo recently expanded toward isolated posting workflows for multiple
platforms. Current leader direction narrows the project scope: this project
should operate only on LinkedIn.

Without an explicit decision, the repo would keep contradicting itself:

- config could still suggest editable platform defaults
- Web UI and scheduler could still offer multi-platform controls
- runtime dispatch could still execute non-LinkedIn workflows
- docs would overstate supported release scope

## Decision

Adopt LinkedIn as the sole supported platform for this project:

1. **Single supported platform**
   Draft generation, planning, assisted posting, scheduling, and session
   management support LinkedIn only.
2. **Fixed default**
   Config and UI treat LinkedIn as a fixed default, not an editable operator
   preference.
3. **Runtime enforcement**
   Non-LinkedIn platform requests are rejected explicitly in runtime surfaces.
4. **Compatibility boundary**
   Existing workbook files may still contain historical non-LinkedIn columns or
   data, but those columns are no longer active supported behavior.
5. **Docs alignment**
   Product docs, stories, and UI copy must stop presenting other platforms as
   supported for this project release.

## Alternatives Considered

1. Keep multi-platform support and merely recommend LinkedIn.
   Rejected because it does not satisfy the explicit scope direction.
2. Hide non-LinkedIn options only in Web UI.
   Rejected because CLI and scheduler would remain contradictory.
3. Remove all non-LinkedIn workbook columns immediately.
   Rejected because it adds migration risk unrelated to the scope directive.

## Consequences

Positive:

- smaller operational scope
- simpler validation and support burden
- fewer provider-specific regressions outside the active project target

Tradeoffs:

- previously added non-LinkedIn workflows become inactive project scope
- some compatibility code may remain temporarily for workbook safety

## Follow-Up

- keep workbook compatibility explicit until a separate migration story exists
- reject new multi-platform feature work unless project scope changes again
