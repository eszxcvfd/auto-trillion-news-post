# Product Docs

These files are the living product surface derived from
[SPEC.md](/home/trung/Documents/2026/project/auto-trillion-news-post/SPEC.md).

Current product docs:

- [overview.md](/home/trung/Documents/2026/project/auto-trillion-news-post/docs/product/overview.md)
  Product position, current baseline, target v2, surfaces, and golden flow.
- [workbook-contracts.md](/home/trung/Documents/2026/project/auto-trillion-news-post/docs/product/workbook-contracts.md)
  Dual workbook contracts, parsing rules, and `Link Post` behavior.
- [release-boundaries.md](/home/trung/Documents/2026/project/auto-trillion-news-post/docs/product/release-boundaries.md)
  Brownfield rollout slices from stabilization through UI/scheduling.

Update rule:

1. Update the affected product doc when behavior or scope changes.
2. Update story packets or backlog slices that depend on that behavior.
3. Update `docs/TEST_MATRIX.md` and durable story proof when validation shape
   changes.
4. Add or refresh a decision when architecture, source-of-truth hierarchy,
   runtime/storage direction, or validation requirements change.
