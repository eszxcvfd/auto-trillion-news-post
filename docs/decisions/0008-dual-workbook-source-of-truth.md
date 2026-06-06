# 0008 Dual Workbook Source of Truth

Date: 2026-06-05

## Status

Accepted

## Context

The brownfield repo already contains an internal 14-column workbook used by the
current CLI baseline. The approved `SPEC.md` also defines a new operator-facing
business workbook, `Trillion $ news.xlsx`, for the target v2 customer flow.

Without an explicit decision, future implementation could blur these two
contracts, force operators to manage both manually, or silently replace one
truth with another.

## Decision

Keep two workbook contracts explicit:

1. **Internal compatibility workbook**
   Preserves current baseline CLI behavior during brownfield refactor.
2. **Business workbook**
   `Trillion $ news.xlsx` is the operator-facing source of truth for reviewed
   drafts, selective posting, and `Link Post` write-back in v2.

The application may perform mapping or conversion between the two contracts, but
that responsibility belongs to the implementation, not to the operator.

`Link Post` remains a shared per-row text block in the business workbook and
must be parsed and updated safely per platform line.

## Alternatives Considered

1. Replace the internal workbook immediately with the business workbook.
   Rejected because it creates unnecessary brownfield risk for current CLI
   behavior.
2. Keep both workbooks and expect operators to reconcile them manually.
   Rejected because it creates workflow confusion and violates the product
   intent of a single review-and-post surface.
3. Move the operator source of truth into a database immediately. Rejected
   because the spec defines Excel as the operator-facing truth for MVP.

## Consequences

Positive:

- baseline compatibility can survive while v2 is introduced incrementally
- the operator has one clear workbook for review and posting decisions
- architecture, product docs, and intake can refer to one explicit
  source-of-truth hierarchy

Tradeoffs:

- the implementation must own conversion or coexistence complexity
- tests and docs must stay clear about which workbook contract a feature uses

## Follow-Up

- keep workbook rules explicit in `docs/product/workbook-contracts.md`
- treat changes to workbook hierarchy or `Link Post` semantics as high-risk
