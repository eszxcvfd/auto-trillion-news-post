# 0009 Local Runtime and Operational Storage

Date: 2026-06-05

## Status

Accepted

## Context

The approved spec describes a local operator tool with visible browser
automation, local files, persistent sessions, and possible future scheduling or
history features. The architecture now needs a clear boundary between business
source-of-truth storage and optional operational storage.

Without this decision, future work could:

- over-engineer a server-style product database too early
- confuse Harness durable-layer storage with application storage
- move draft review or posting decisions away from Excel before the product is
  ready

## Decision

Adopt the following storage and runtime boundary:

1. **Runtime**
   The product runs locally on an operator-controlled machine.
2. **Primary business storage**
   Excel workbooks and local filesystem artifacts remain the MVP source of
   truth for product operation.
3. **Operational storage**
   If scheduling, run history, or dashboard history is introduced, use local
   SQLite for operational metadata such as job definitions and run history.
4. **Boundary**
   SQLite supports operations and observability; it does not replace the
   business workbook as the reviewed draft and posting-decision surface.

The Harness durable layer database remains repo tooling and is separate from
the application product storage model.

## Alternatives Considered

1. Introduce a server database now. Rejected because it does not match local
   MVP scope.
2. Keep all future history and scheduling only in markdown or flat files.
   Rejected because structured local operational data is a better fit for
   scheduling and history queries.
3. Move all posting decisions into SQLite. Rejected because the spec defines
   Excel as the operator review and posting surface.

## Consequences

Positive:

- storage roles are explicit before scheduler/history work starts
- the product remains simple for local operators
- future dashboard or scheduling work has a clear local operational store

Tradeoffs:

- the system must coordinate local files, sessions, and optional SQLite state
- docs and code must stay clear about business truth versus operational truth

## Follow-Up

- keep local storage responsibilities explicit in `docs/ARCHITECTURE.md`
- treat any future attempt to replace Excel as a high-risk product/architecture
  change
