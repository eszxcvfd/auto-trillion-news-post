# US-004 AI Post Generation

## Status

implemented

## Lane

normal

## Product Contract

The application must read `new` news articles from `output/Trillion $ news.xlsx`, invoke Google Gemini API to generate English social media posts according to specific prompt templates, write the output posts to Markdown files under `output/posts/`, and update the Excel row status to `generated`.

Running the command:
```bash
python3 main.py generate --platform linkedin --limit 5
```
must fetch `new` entries, call Gemini API, write `.md` drafts, and update the Excel workbook.

## Relevant Product Docs

- [overview.md](file:///home/trung/Documents/2026/project/auto-trillion-news-post/docs/product/overview.md)

## Acceptance Criteria

- **Excel Reading**: Reads rows with status `new` from `output/Trillion $ news.xlsx`.
- **Gemini AI Integration**: Uses the `google-genai` SDK and configured models (e.g. `gemini-1.5-flash` or `gemma-4`) to request post generation.
- **Hashtag Format**: 
  - Starts with exactly 5 hashtags (the first must be a main industry hashtag).
  - Ends with exactly these 5 fixed hashtags: `#TAHKFoundation #HenryUniverses #USIran #USTariffs #Trump`.
- **Output File**: Saves each post as a Markdown file under `output/posts/` named `YYYY-MM-DD_{id}_{platform}.md` following the format template.
- **Excel Updating**: Updates the row's `Generated Post File` column and changes status to `generated`. If generation fails, status is changed to `error` and the reason is noted.

## Design Notes

- **AI Writer**: `src/ai_writer.py` using `google-genai`.
- **Post File Writer**: `src/post_writer.py` to write Markdown files and update Excel.
- **CLI integration**: `main.py` generate command.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-004 --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Validate generated post starts with 5 hashtags and ends with 5 fixed hashtags in `tests/test_post_validation.py`. |
| Integration | Verify Gemini client initialization, prompt construction, and response parsing. |
| E2E | N/A |
| Platform | N/A |
| Release | N/A |

## Harness Delta

- Added US-004 story.

## Evidence

- Verified unit and integration tests are passing using: `python3 -m unittest discover tests` (Ran 20 tests, all passing / skipped expected).
- Verified story using: `scripts/bin/harness-cli story verify US-004`.
