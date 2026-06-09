# US-016 B1 Facebook and X Posting Adapters

## Status

implemented

## Lane

normal

## Product Contract

Release B1 requires assisted posting for Facebook and X through the shared
platform posting core. The adapters must:

- Route manual and scheduled posting to the correct platform composer.
- Support optional image upload when a local image is available.
- Reuse the same operator-confirm flow and `Link Post` write-back semantics.
- Use the same session validation profiles as Web UI onboarding.

## Relevant Product Docs

- `docs/product/release-boundaries.md`
- `SPEC.md` Release B1 and FR-09

## Acceptance Criteria

- Given a row with a Facebook draft, when manual `post` targets Facebook, then
  the Facebook adapter opens instead of LinkedIn.
- Given a row with an X draft, when manual `post` targets X, then the X compose
  flow opens instead of LinkedIn.
- Given Facebook or X is selected, when no image is available, then posting may
  still proceed as text-only per the capability matrix.
- Given session onboarding runs for Facebook or X, when validation completes,
  then the shared `PLATFORM_PROFILES` session check is used.

## Design Notes

- `src/platform_capabilities.py` — add Facebook and X to `SUPPORTED_POSTING_PLATFORMS`.
- `src/platform_posting.py` — Facebook feed composer and X compose adapters.
- `src/web_ui.py` — remove duplicate Facebook/X session branches.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `tests/test_platform_capabilities.py` marks Facebook/X as supported. |
| Integration | `tests/test_assisted_posting.py` mocks Facebook and X dispatch paths. |
| E2E | Optional manual browser smoke for Facebook or X posting. |
| Platform | `.venv/bin/python -m unittest discover tests` passes. |
| Release | B1 posting gap for Facebook and X is closed. |

## Evidence

- `.venv/bin/python -m unittest discover tests`