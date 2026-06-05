# Architecture

The application stack and core surfaces for the Trillion News Auto Post System v2.

---

## 1. Product Stack & Surfaces

- **Product Surfaces**:
  - **CLI Surface**: Command-line entrypoint (`main.py`) for login management, manual posting, status checks, and scheduling.
  - **Web UI Surface**: FastAPI web server with server-side rendered Jinja2 templates and HTMX for dynamic, real-time UI updates (defaulting to `http://localhost:8080`).
- **Runtime Stack**: Python 3.11+
- **Browser Automation**: Playwright (using persistent browser contexts for session management).
- **Excel Processing**: `openpyxl` for reading inputs and writing post links back.
- **Image Downloading**: HTTP requests via `httpx` or `requests` for downloading Google Drive images.
- **Scheduler**: `APScheduler` for managing scheduled background tasks.
- **Storage & Output**:
  - `Trillion $ news(1).xlsx` for content input and post link updates.
  - Local SQLite database (optional, for persistent job scheduling & dashboard logs).
  - `.browser_sessions/` directory for saving platform sessions.

---

## 2. Core Domain Identification

The domain components for the system are defined as follows:

- **PostItem**: Represents a single news row loaded from the Excel sheet. Attributes include row ID, title, category (sheet name), local image path, Google Drive link, map of platforms to draft contents, and map of platforms to post results (URLs or error messages).
- **PlatformSession**: Represents a browser session context for a social media platform. Tracks browser context directory, login status, and the date of the last successful verification.
- **PostJob**: A execution instance representing a post run for selected rows and platforms. Tracks progress, start/end time, and intermediate results.
- **ScheduledTask**: An entity defining a scheduled posting configuration (timezone, run times, sheets, platforms, limits) managed by the system scheduler.

---

## 3. Structural Layering

The codebase follows a clean, modular structure split between the posting core, platforms, and the web interface:

```text
auto-trillion-news-post/
├── main.py                          # CLI and application entrypoint
├── src/
│   ├── config.py                    # Configuration loaders (.env & config.yaml)
│   ├── models.py                    # Data classes (PostItem, PostJob, etc.)
│   ├── excel_reader.py              # Parsing rows, stripping spaces, handling missing cols
│   ├── excel_writer.py              # In-place sheet updates with locking/backups
│   ├── image_downloader.py          # Google Drive sharing link conversion and storage
│   ├── platform_base.py             # Abstract base poster class defining standard flows
│   ├── platforms/                   # Specific browser automation workflows
│   │   ├── linkedin.py
│   │   ├── facebook.py
│   │   ├── twitter.py
│   │   └── ...
│   ├── session_manager.py           # Browser context loading and login status checks
│   ├── scheduler.py                 # Task queue and job execution logic
│   └── web/                         # FastAPI web dashboard
│       ├── app.py
│       ├── routes.py
│       ├── templates/
│       └── static/
```

---

## 4. Boundary Rules

### 4.1 Parse-First Boundary Rule
Data boundary inputs must be sanitized before processing:
- **Excel Headers**: Column names must be stripped of trailing/leading whitespaces (e.g. `'TikTok '` mapped to `'TikTok'`).
- **Platform Content**: Values must be stripped. Empty cells, whitespace-only cells, and cells containing `.` are skipped.
- **Missing Columns**: Triggers dynamic column creation if missing (e.g., adding `Link Post`).
- **Google Drive URLs**: Sharing URLs must be parsed to extract the unique file ID before converting to direct download links.

### 4.2 Dependency Rules
- Platform-specific code must inherit from `PlatformBase` and not import Web UI elements.
- Browser automation sessions are isolated per platform to avoid shared state cookies or cross-platform session pollution.
- Changes to the Excel file must perform file-locking checks and save backups to prevent data loss if the file is open.
