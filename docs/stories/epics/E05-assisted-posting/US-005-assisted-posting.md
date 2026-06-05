# US-005 Assisted Posting

## Status

implemented

## Lane

normal

## Product Contract

The application must support assisted social media posting. By running:
```bash
python main.py post --id <id> --platform linkedin
```
the system will:
1. Look up the news article matching `<id>` in `output/Trillion $ news.xlsx`.
2. Locate the generated Markdown post file (from `Generated Post File` column) and read its contents.
3. Parse the Markdown file to extract the social post body (excluding metadata like title, URL, source headings).
4. Locate the screenshot image file (from `Image File` column).
5. Launch a Playwright browser window with `headless=False` and persistent browser context (saving session state in `output/.browser_context`).
6. Navigate to `https://www.linkedin.com/feed/` (or the composer directly).
7. Guide the user to log in if they aren't already.
8. Locate and trigger the post composer, paste the post body, and upload the screenshot.
9. Pause and wait for the user to review and manually click "Post". The tool must **never** auto-click the post submission button.
10. Prompt the user in the CLI asking if the post was successfully published.
11. Update the Excel row status to `posted` if confirmed, or leave as is / log an error.

If the LinkedIn selectors fail to locate composer elements (e.g. due to UI changes or localization), the script must output a detailed error message and print the post body clearly in the console so that the user can manually copy/paste it, keeping the browser open.

## Relevant Product Docs

- [overview.md](file:///home/trung/Documents/2026/project/auto-trillion-news-post/docs/product/overview.md)

## Acceptance Criteria

- **Browser Launch**: Opens a non-headless browser window and persists cookies/sessions.
- **Login Guidance**: Prints helpful instructions in the terminal if the user needs to sign in.
- **Auto-Fill Content**: Populates the LinkedIn composer textbox with the post body and uploads the news card screenshot.
- **No Auto-Submit**: Does not auto-submit the post.
- **Fallback Output**: If selectors are missing, prints the post text and file/image locations to the console with copy instructions.
- **Status Update**: Prompts user on command-line and updates Excel status to `posted` on confirmation.

## Design Notes

- **Assisted Poster Module**: `src/assisted_posting.py`.
- **CLI integration**: `main.py` `post` subcommand.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-005 --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Validate post content parsing and image path resolution in `tests/test_assisted_posting.py`. |
| Integration | Verify browser context configuration, path resolutions, and excel integration using mock playwright components. |
| E2E | Manual execution of the CLI post command, visual verification of browser popup and auto-filling of text/image. |
| Platform | N/A |
| Release | N/A |

## Harness Delta

- Added US-005 story packet.

## Evidence

- Verified unit and integration tests are passing using: `python3 -m unittest discover tests` (Ran 27 tests, all passing / skipped expected).
- Verified story using: `scripts/bin/harness-cli story verify US-005`.
