# Product Overview — Trillion News Auto Post System

Derived from [SPEC.md](file:///home/trung/Documents/2026/project/auto-trillion-news-post/SPEC.md).

The **Trillion News Auto Post System** is a local utility designed to automate the manual workflow of finding news articles related to the term "trillion" (in various forms), saving their information to an Excel sheet, capturing screenshots of the news items, generating social media post drafts in English using Gen AI, and optionally assisting with posting on LinkedIn.

## 1. Objectives & MVP Scope

- **Search**: Programmatically search Google News or Bing News for configurable keywords (e.g. `Payment services trillion $`, `AI trillion dollar market`).
- **Filter**: Filter results to only keep those containing "trillion", "trillion-dollar", "$ trillion", "USD ... trillion" (case-insensitive) in the title, snippet, or URL.
- **Excel Storage**: Save all filtered news to a local Excel file `output/Trillion $ news.xlsx` with status tracking.
- **Image Capture**: Capture screenshots of the news card or search results and save to `output/Ảnh Trillion $ news/` as PNG, referencing the file name in the Excel row.
- **AI Post Generation**: Generate professional, strategically insightful LinkedIn posts in English based on the news using **Gemini API / Gemma 4** models. Save post drafts to `output/posts/` as Markdown (`.md`).
- **Assisted Posting**: Open a browser via Playwright, paste the generated post content into LinkedIn's composer, upload the captured screenshot, and let the operator manually review and click the "Post" button.

### Non-Goals for MVP
- 100% automated posting using official APIs.
- Captcha, login, rate-limit, or anti-bot bypass.
- Large-scale scraping (limited to target results/keywords).
- Multi-user support or web-based dashboards.

---

## 2. Core Workflows

### 2.1 Full Draft Pipeline (`python main.py run`)
1. Read keywords from `keywords.txt` or `config.yaml`.
2. Open browser with Playwright to search for keywords on Google/Bing News.
3. Parse and filter results matching "trillion" terms.
4. Deduplicate results using normalized URLs and titles.
5. Save results in `output/Trillion $ news.xlsx` with status `new`.
6. Capture screenshots of news cards, saving to `output/Ảnh Trillion $ news/`.
7. Generate posts via **Gemini API** for all `new` items, save as `.md` under `output/posts/`, and update status to `generated`.

### 2.2 Assisted Posting (`python main.py post --id <id>`)
1. Locate the news item by ID in `output/Trillion $ news.xlsx`.
2. Read the post content from its `.md` file.
3. Launch browser (non-headless), navigate to LinkedIn.
4. Wait for operator to login (if needed).
5. Paste content into LinkedIn composer.
6. Upload the news screenshot from `output/Ảnh Trillion $ news/`.
7. Pause execution to let the operator manually edit/submit the post.
8. Upon manual completion, update status to `posted` in the Excel file.

---

## 3. Configuration & System Rules

### 3.1 Environment (`.env`)
- **AI Provider**: `gemini`
- **AI API Key**: `GEMINI_API_KEY` env var
- **AI Model**: `gemini-1.5-flash` or `gemma-4` (or other approved Gemini models)
- **Search Provider**: `browser` (Playwright)
- **Headless Mode**: `false` (for interactive review / debugging)
- **File & Folder Paths**: Configurable outputs for Excel, images, and posts.

### 3.2 Post Formatting Rules (LinkedIn / Facebook)
All generated posts must strictly adhere to the following template:

```text
#IndustryHashtag #Hashtag2 #Hashtag3 #Hashtag4 #Hashtag5

[Post Content - Professional Business Style in English]
[Mention trillion-dollar opportunity and strategic insight]

#TAHKFoundation #HenryUniverses #USIran #USTariffs #Trump
```

#### Hashtag Rules:
1. **Top Hashtags**: Exactly 5 hashtags. The first must be the main industry hashtag. The remaining 4 must be relevant news-specific hashtags proposed by the AI.
2. **Bottom Hashtags**: Exactly these 5 fixed hashtags: `#TAHKFoundation #HenryUniverses #USIran #USTariffs #Trump`.

---

## 4. Expected Output structure
All outputs must be written to the local `./output` folder (configured in `.env` and `.gitignore`d):

```text
output/
├── Trillion $ news.xlsx
├── posts/
│   └── YYYY-MM-DD_{id}_linkedin.md
├── Ảnh Trillion $ news/
│   └── YYYY-MM-DD_{id}_{slug_keyword}.png
└── logs/
    └── YYYY-MM-DD.log
```
