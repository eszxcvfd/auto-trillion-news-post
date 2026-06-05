# US-003 Save to Excel & Image Screenshot

## Status

implemented

## Lane

normal

## Product Contract

The application must persist filtered news items to a local Excel file `output/Trillion $ news.xlsx` and capture screenshots of search result news cards to `output/Ảnh Trillion $ news/`.

Running the command:
```bash
python3 main.py search --keywords keywords.txt --limit 10
```
must execute search, filtering, card screenshotting, and append the results into the Excel sheet.

## Relevant Product Docs

- [overview.md](file:///home/trung/Documents/2026/project/auto-trillion-news-post/docs/product/overview.md)

## Acceptance Criteria

- **Excel Creation**: If `output/Trillion $ news.xlsx` doesn't exist, it must be created with correct columns.
- **Excel Append**: Appends new rows to the Excel sheet, auto-incrementing the ID. Existing rows must not be overwritten.
- **Locked File Handling**: If the Excel file is open or locked, it logs a clear warning asking the user to close it, rather than throwing a traceback.
- **Image Saving**: Captures and saves PNG screenshots of the specific search result news cards under `output/Ảnh Trillion $ news/` using the name template: `YYYY-MM-DD_{id}_{slug_keyword}.png`.
- **Linked Records**: The saved screenshot file name must be populated in the "Image File" column in the Excel row.

## Design Notes

- **Excel Writer**: `src/excel_store.py` using `openpyxl`.
- **Image Capture**: `src/image_capture.py` capturing element screenshots.
- **CLI integration**: `main.py` search command.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-003 --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Verify Excel creation, headers, appending rows, auto-incrementing ID in `tests/test_excel_store.py`. |
| Integration | Verify Playwright screenshot captures elements and stores them correctly as PNG files. |
| E2E | N/A |
| Platform | N/A |
| Release | N/A |

## Harness Delta

- Added US-003 story status to `implemented` and registered standard verify tests.

## Evidence

```bash
$ python3 -m unittest discover tests
Ran 13 tests in 0.006s
OK (skipped=4)

$ scripts/bin/harness-cli story verify US-003
Story US-003 verification: pass
```
