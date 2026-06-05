# US-002 Search & Filter News

## Status

implemented

## Lane

normal

## Product Contract

The application must support searching and filtering news articles. It must load keywords, launch a Playwright browser instance, retrieve search results from Google/Bing News, filter them for trillion-related keywords, and remove duplicates.

Running the command:
```bash
python3 main.py search --keywords keywords.txt --limit 10
```
must execute the search, filter the results, and print the resulting JSON objects to the console.

## Relevant Product Docs

- [overview.md](file:///home/trung/Documents/2026/project/auto-trillion-news-post/docs/product/overview.md)

## Acceptance Criteria

- **Keyword Loading**: System reads search terms from `keywords.txt` or `config.yaml`, skipping blank lines and comments.
- **Search Scraper**: System launches Playwright and crawls Google News or Bing News for each keyword up to the configured limit.
- **Filtering**: Keeps articles where title, snippet, or URL contain case-insensitive trillion-related terms (`trillion`, `trillion-dollar`, `$ trillion`, `USD ... trillion`).
- **Deduplication**: Removes duplicate articles using normalized URLs (stripping query parameters like UTM tags) and normalized titles.
- **CLI output**: Prints the collection of parsed `NewsItem`s as a JSON array.

## Design Notes

- **CLI entrypoint**: `main.py` search subcommand.
- **Searcher**: `src/searcher.py` using Playwright async/sync API.
- **Filter**: `src/filter.py` implementing deduplication and text matching.
- **Config**: `src/config.py` parsing `.env` and `config.yaml`.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-002 --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Verify trillion term matching logic and URL normalization/deduplication in `tests/test_filter.py`. |
| Integration | Verify Playwright searcher fetches and parses result elements from a search page. |
| E2E | N/A |
| Platform | N/A |
| Release | N/A |

## Harness Delta

- Updated US-002 story status to `implemented` and linked standard verify tests.

## Evidence

```bash
$ python3 -m unittest discover tests
Ran 9 tests in 0.010s
OK

$ scripts/bin/harness-cli story verify US-002
Story US-002 verification: pass
```
