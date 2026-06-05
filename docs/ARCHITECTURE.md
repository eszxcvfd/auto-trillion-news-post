# Architecture

The application stack and core surfaces have been selected for the Trillion News Auto Post System.

## Product Stack & Surfaces

- **Product Surface**: CLI Tool (`main.py`)
- **Runtime Stack**: Python 3.11+
- **Browser Scraper & Automation**: Playwright
- **Storage & Output**: Local files (`output/Trillion $ news.xlsx` using `openpyxl`, text/markdown files for posts, and images/screenshots).
- **AI Provider**: Google Gemini API using `gemini-1.5-flash` or `gemma-4` models.

For context on these decisions, see [0007-technology-stack-gemini.md](file:///home/trung/Documents/2026/project/auto-trillion-news-post/docs/decisions/0007-technology-stack-gemini.md).

## Core Domain Identification

The core business domains and data contracts for the Trillion News Auto Post System are:

- **NewsItem**: Represents a harvested news article. Attributes include title, URL, source, snippet, publication date, image file reference, generated post reference, and workflow status (`new`, `generated`, `reviewed`, `posted`, `skipped`, `error`).
- **FilterRule**: Domain rules for matching trillion-dollar-related keywords (e.g., case-insensitive checks for `trillion`, `trillion-dollar`, `$ trillion`, `USD ... trillion`).
- **NewsScreenshot**: The visual artifact associated with a news article (stored locally as a PNG screenshot).
- **SocialPost**: The generated social media post draft tailored for a target platform (e.g., LinkedIn). Consists of a target platform, 5 top hashtags (1 main industry + 4 relevant), English post body, and 5 fixed bottom hashtags.
- **AppConfig**: The application's runtime configuration containing search providers, model selection, hashtags, and output directory settings.

## Default Layering

```text
domain
  <- application
      <- infrastructure
          <- interface
              <- app surfaces
```

## Candidate Structure

```text
app/
  domain/
    entities/
    value-objects/
    repositories/
    services/

  application/
    commands/
    queries/
    handlers/

  infrastructure/
    database/
    logging/
    notifications/

  interface/
    controllers/
    dto/
    presenters/
    routes/
    middlewares/

surfaces/
  browser/
  mobile/
  desktop/
  cli/
```

This is a thinking template, not a scaffold. Create real folders only when a
story enters implementation and the selected stack needs them.

## Dependency Rule

Inner layers must not depend on outer layers.

| Layer | May depend on | Must not depend on |
| --- | --- | --- |
| domain | nothing project-external except tiny pure utilities | framework, database, UI, provider, process/env |
| application | domain | framework, UI, provider, database concrete clients |
| infrastructure | domain, application | interface controllers or UI |
| interface | all backend layers | UI state or platform shell assumptions |
| app surfaces | API contracts and app-facing clients | domain internals directly |

## Parse-First Boundary Rule

Unknown data must be parsed at boundaries before it enters inner code.

Boundaries include:

- HTTP request bodies, params, and query strings.
- Session payloads and identity claims.
- Environment variables.
- Database rows returned from external clients.
- Platform shell payloads.
- Deep links, tokens, and signed URLs.
- Provider webhooks, events, and async payloads.

Target flow:

```text
unknown input
  -> parser
  -> typed DTO or command
  -> application use case
  -> domain object/value object
```

Inner layers should work with meaningful product types such as `UserId`,
`AccountId`, `WorkspaceId`, `Role`, `DateRange`, or domain-specific IDs,
rather than repeatedly validating raw strings.

## Command/Query Boundary

If the product has both reads and writes, keep command/query separation clear at
the code level even when the storage layer is simple:

- Commands mutate state and own audit side effects.
- Queries read state and format for consumers.
- Shared domain rules live in domain/application, not controllers.

## Observability Contract

The future server should emit one canonical JSON log line per request with:

- timestamp
- level
- request_id
- user_id when known
- action
- duration_ms
- status_code
- message

Audit logs are product records. Application logs are operational records. Do not
use one as a substitute for the other.
