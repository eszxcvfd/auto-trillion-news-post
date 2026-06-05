# Product Overview — Trillion News Auto Post System v2

Derived from [SPEC.md](file:///home/trung/Documents/2026/project/auto-trillion-news-post/SPEC.md).

The **Trillion News Auto Post System v2** is a local utility designed to read pre-written social media posts from an Excel sheet (`Trillion $ news(1).xlsx`), download post images from Google Drive sharing URLs, automate browser posting via Playwright across 8 social media platforms, capture post permalinks, and save them back into the Excel file. It provides a Web UI for non-technical users and supports scheduled posting.

---

## 1. Objectives & MVP Scope

- **Input Reading**: Read multi-sheet Excel files. Strip whitespace from headers and handle missing output columns dynamically.
- **Image Downloading**: Parse file IDs from Google Drive links and download them to a local directory for upload.
- **Automated Posting**: Log in (via persistent session storage) and post to 8 social media platforms:
  1. LinkedIn
  2. Facebook
  3. X (Twitter)
  4. Instagram
  5. Pinterest
  6. Threads
  7. TikTok
  8. YouTube
- **Selective Posting**: Skip posting for platforms that already have a successful link recorded in the output cell to prevent duplicate posts.
- **Link Capturing**: Capture post permalinks after successful posts, using fallback values if capturing times out.
- **Output Writing**: Append results to the `Link Post` column in real-time, backing up the Excel file first.
- **Enhanced Interface**: Web UI for non-technical users to upload, preview, trigger, and monitor runs.
- **Scheduling**: Persist scheduled posting tasks (one-time or daily/cron recurring) via APScheduler.

---

## 2. Core Workflows

### 2.1 Excel Parsing & Selective run (`python main.py post`)
1. Read the sheet names and values from `Trillion $ news(1).xlsx`.
2. Map headers to columns after stripping trailing/leading whitespaces (e.g. `'TikTok '` -> `'TikTok'`).
3. For each row, check the `Link Post` cell to parse already-posted URLs.
4. Filter down to platforms that have pre-written content (ignoring empty/whitespace-only cells) and do not have a recorded link.
5. If there is an image URL, parse the file ID and download the image to the local `./images` directory.
6. Post up to a configured limit of rows (default 2) per run.

### 2.2 Browser Automation Posting & Capturing
1. Launch Playwright using a persistent browser context per platform (saved in `./.browser_sessions/<platform>`).
2. Navigate to the platform. Check login status. If the operator needs to log in, launch a visible browser and wait.
3. Once logged in, execute the platform-specific posting steps (typing text, selecting files, sharing).
4. Extract the post permalink from the browser. If it times out or fails, mark as `[posted-no-link]`.
5. Append the result to the `Link Post` column and write it back to the Excel file.

### 2.3 Web Interface & Control (`python main.py serve`)
- **Dashboard**: Lists all rows, categories, contents, and status indicators.
- **Upload**: Upload new files and validate columns.
- **Preview**: View draft text and images before posting.
- **Login Status**: Monitor and refresh sessions for all 8 platforms.
- **Schedules**: Add, remove, and monitor automated scheduled runs.

---

## 3. Configuration & Inputs

### 3.1 Excel Column Layout (12 columns)
1. `#` (Row ID)
2. `Trillion $ news Title` (Title, used to name image files)
3. `Image link` (Google Drive sharing link)
4. `Linkedin` (Post body)
5. `Facebook` (Post body)
6. `X (Twitter)` (Post body)
7. `Instagram` (Post body)
8. `Pinterest` (Post body)
9. `Threads` (Post body)
10. `TikTok ` (Post body)
11. `YouTube` (Post body)
12. `Link Post` (Newline-separated status and URLs - Output)

### 3.2 Post Formatting Constraint
Posts contain pre-written tags and body text from Excel. The system posts them exactly as is, except for trailing/leading whitespaces.

---

## 4. Expected Output Structure
Outputs must be kept locally:
```text
auto-trillion-news-post/
├── Trillion $ news(1).xlsx          # Input Excel file (updated in-place)
├── Trillion $ news(1).backup.xlsx   # Automatically created backup
├── images/                          # Downloaded Google Drive photos
├── logs/                            # Real-time execution logs
└── .browser_sessions/               # Playwright persistent contexts
    ├── linkedin/
    ├── facebook/
    └── ...
```
