# Workbook Contracts

Derived from [SPEC.md](/home/trung/Documents/2026/project/auto-trillion-news-post/SPEC.md)
and [docs/decisions/0012-linkedin-only-project-scope.md](/home/trung/Documents/2026/project/auto-trillion-news-post/docs/decisions/0012-linkedin-only-project-scope.md).

This project has two workbook contracts. They must remain explicit during
brownfield refactor.

## LinkedIn-Only Active Scope

Per decision `0012`, the **active** business workbook columns for draft review
and posting are:

- `#`, `Trillion $ news Title`, `Image link`, `Linkedin`, `Link Post`

Columns for Facebook, X, Instagram, Pinterest, Threads, TikTok, and YouTube may
still exist in legacy workbooks. They are read-only residue — not supported for
new draft generation or posting in the current release.

Runtime and UI surfaces scope `Link Post` display and write-back to the LinkedIn
line when presenting operator-facing status.

## Contract A — Internal Compatibility Workbook

The existing baseline code writes and reads a 14-column internal workbook.

Purpose:

- preserve the current CLI baseline
- support current harvest and generate behavior while v2 expands

Headers:

1. `ID`
2. `Found Date`
3. `Keyword`
4. `Title`
5. `Source`
6. `URL`
7. `Snippet`
8. `Published Text`
9. `Image File`
10. `Platform`
11. `Top Hashtags`
12. `Generated Post File`
13. `Status`
14. `Notes`

This workbook is a compatibility contract, not the target operator-facing
business contract.

## Contract B — Business Workbook

The target v2 workbook is:

```text
Trillion $ news.xlsx
```

Purpose:

- operator review surface
- draft source of truth before posting
- per-platform result write-back target

Expected columns:

1. `#`
2. `Trillion $ news Title`
3. `Image link`
4. `Linkedin`
5. `Facebook`
6. `X (Twitter)`
7. `Instagram`
8. `Pinterest`
9. `Threads`
10. `TikTok`
11. `YouTube`
12. `Link Post`

## Brownfield Rule

The operator must not be forced to manually reconcile these two workbook
contracts.

If legacy compatibility or migration is needed, the application handles that
mapping. The operator still works against the business workbook contract.

## Header Rules

When reading the business workbook:

- trim all headers before matching
- do not fail on leading or trailing whitespace
- treat `TikTok ` and `TikTok` as the same header
- treat ` X (Twitter)` and `X (Twitter)` as the same header

## Content Rules

A draft cell means "no content" when it is:

- empty
- whitespace only
- `.`

No-content cells must be skipped rather than treated as system errors.

## Link Post Rules

`Link Post` is a shared text block with one line per platform:

```text
LinkedIn: https://...
Facebook: https://...
X: [posted-no-link]
Instagram: [error] upload failed
Pinterest: [skip] no content
Threads: [login-required]
```

Allowed value types:

- success URL
- `[pending]`
- `[skip] <reason>`
- `[error] <reason>`
- `[login-required]`
- `[posted-no-link]`

The parser/writer must:

- update only the target platform line
- preserve other platform lines
- allow retry for retryable states
- report malformed operator edits clearly instead of overwriting silently

## Selective Posting Rules

For each `row x platform` pair:

- skip when a success URL already exists
- skip when `[posted-no-link]` already exists
- allow retry when the state is `[pending]`, `[error]`, `[login-required]`, or
  missing
- skip when there is no draft content

## Image Source Rules

`Image link` may contain:

1. a local file path
2. a Google Drive sharing URL

Google Drive links must be resolvable without requiring extra Google login in
the image download flow.

If the image cannot be resolved:

- LinkedIn may continue text-only when the operator draft allows it
- otherwise record an explicit error in `Link Post`

## Operator-Stray Rows and Repair

Legacy workbooks may contain rows that appear in high Excel row indices after
empty gaps, or rows with only title/image and no LinkedIn draft. These are
**operator-stray** rows from the pre-LinkedIn-only era.

Behavior:

- the Web UI dashboard hides rows without a LinkedIn footprint
- `repair_broken_draft_references()` may remove stray rows, clear broken draft
  file references, and compact empty gaps so new rows append contiguously
- operators should run repair after manual Excel cleanup when row counts look
  inconsistent between Excel and the dashboard
