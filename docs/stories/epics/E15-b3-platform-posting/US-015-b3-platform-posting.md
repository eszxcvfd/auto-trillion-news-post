# US-015 B3 Best-Effort TikTok and YouTube Posting

## Status

implemented

## Lane

normal

## Product Contract

Release B3 adds best-effort assisted posting for TikTok and YouTube while
keeping MVP scope explicit:

- TikTok: photo/image posting mode when the operator account UI supports it.
- YouTube: Community Post mode when the operator channel supports it.
- Neither platform is represented as a full video upload pipeline.
- Permalink capture remains best-effort through the existing operator confirm flow.

## Relevant Product Docs

- `docs/product/release-boundaries.md`
- `SPEC.md` Release B3 and section 8.12

## Acceptance Criteria

- Given a row has a TikTok or YouTube draft and a local image, when manual post
  starts, then the platform-specific adapter opens instead of LinkedIn.
- Given TikTok or YouTube is selected without a local image, when posting
  starts, then the system rejects the action with a clear media requirement.
- Given TikTok or YouTube posting begins, when automation prepares the
  browser composer, then the operator sees best-effort MVP scope messaging.
- Given Web UI session management is used, when TikTok or YouTube are listed,
  then they are supported for onboarding and status checks.

## Design Notes

- `src/platform_capabilities.py` — B3 metadata, session domains, posting support.
- `src/platform_posting.py` — TikTok upload-page and YouTube community adapters.
- `src/web_ui.py` — session checks include B3 platforms.
- `src/templates/index.html` — session cards mark B3 platforms as best-effort.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `tests/test_platform_capabilities.py` covers B3 metadata and media rules. |
| Integration | `tests/test_assisted_posting.py` proves TikTok dispatch with mocked Playwright. |
| E2E | Optional manual browser smoke for one B3 platform. |
| Platform | `.venv/bin/python -m unittest discover tests` passes. |
| Release | TikTok and YouTube are supported only in the documented MVP modes. |

## Evidence

- `.venv/bin/python -m unittest discover tests`