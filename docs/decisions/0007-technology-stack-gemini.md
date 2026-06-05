# 0007 Technology Stack and Gemini AI Provider

Date: 2026-06-04

## Status

Accepted

## Context

The Trillion News Auto Post System requires a defined runtime, browser automation tools, storage tools, and a specific AI provider for English post generation. The specification recommends a local Python CLI tool using Playwright for scraping/screenshots, openpyxl for Excel records, and an OpenAI-compatible or Gemini API. We needed to finalize the stack and the selected AI provider.

## Decision

We decided on the following technology stack for the MVP:
1. **Runtime**: Python 3.11+ (local CLI script).
2. **Scraping & Browser Automation**: Playwright (to scrape news search pages and assist with social posting).
3. **Storage**: Local files, specifically an Excel file (`Trillion $ news.xlsx` using `openpyxl`) and a structured folder output (`output/posts/`, `output/Ảnh Trillion $ news/`).
4. **AI Provider**: Google Gemini API.
5. **AI Models**: `gemini-1.5-flash` or `gemma-4` (or other approved Gemini models).

## Alternatives Considered

1. **OpenAI API**: Considered as it was in the recommended stack template. Rejected because the user specifically requested Gemini API keys and Gemini/Gemma models.
2. **Selenium/Puppeteer**: Playwright was selected over Selenium for better performance, faster screenshot capture, and easier CLI setup.

## Consequences

Positive:
- Integration with powerful Gemini/Gemma models for high-quality content generation.
- Use of Playwright ensures reliable screenshotting of news cards.
- Simple local file-based persistence without complex DB server setups.

Tradeoffs:
- The operator must provide a valid `GEMINI_API_KEY` in their local `.env` file.
- Changes in LinkedIn selectors may break the assisted posting flow, which requires active monitoring.

## Follow-Up

- Implement the first story `US-001` to initialize the repository structure and configuration templates matching this stack.
