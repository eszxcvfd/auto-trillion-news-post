# US-014 B2 Image-First Platform Posting

## Status

implemented

## Lane

normal

## Product Contract

Release B2 must add assisted posting and session support for Instagram,
Pinterest, and Threads while enforcing the MVP capability matrix:

- Instagram and Pinterest require a local image before posting can start.
- Threads allows text-only posting with optional image upload.
- Posting dispatch must route by platform instead of always opening LinkedIn.
- Web UI session onboarding and status checks must treat B2 platforms as supported.

## Relevant Product Docs

- `docs/product/release-boundaries.md`
- `SPEC.md` sections 8.11 and 8.12

## Acceptance Criteria

- Given a row with an Instagram or Pinterest draft but no local image, when
  eligibility is evaluated, then the platform is excluded with a clear media
  reason.
- Given a row with a Threads draft, when manual post is triggered, then the
  Threads adapter opens the Threads composer instead of LinkedIn.
- Given Instagram, Pinterest, or Threads are supported in the current release
  slice, when the operator uses Web UI session management, then those platforms
  are no longer marked unsupported.
- Given posting completes for one platform, when write-back runs, then only that
  platform line in `Link Post` changes.

## Design Notes

- `src/platform_capabilities.py` — capability matrix and media validation.
- `src/platform_posting.py` — shared assisted posting profiles and dispatch.
- `src/assisted_posting.py` — thin wrapper over platform posting adapters.
- `src/posting_core.py` — optional config-aware media eligibility checks.
- `src/web_ui.py` — B2 session onboarding/check support.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `tests/test_platform_capabilities.py` and updated posting-core tests. |
| Integration | Updated assisted-posting and Web UI tests prove dispatch and rejection paths. |
| E2E | Optional manual browser smoke for one B2 platform. |
| Platform | `.venv/bin/python -m unittest discover tests` passes. |
| Release | Instagram, Pinterest, and Threads are supported per B2 boundary. |

## Evidence

- `.venv/bin/python -m unittest discover tests`