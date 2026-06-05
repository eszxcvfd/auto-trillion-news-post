# SPEC.md — Trillion News Auto Post System v2

## 1. Document Control

| Field | Value |
|---|---|
| Product name | Trillion News Auto Post System |
| Document type | Software Specification |
| Version | 2.0.0 |
| Status | Brownfield — refactor from v1 CLI to multi-platform auto-posting with Web UI |
| Language | Vietnamese UI, English generated posts |
| Primary user | Content Admin / Marketing team (non-tech users) |
| Main goal | Đọc dữ liệu từ file Google Sheet (Excel), tự động đăng bài lên 8 nền tảng mạng xã hội, lấy link bài đăng lưu lại vào cột "Link Post" |

---

## 2. Background

### 2.1 Quy trình hiện tại (v1)

Hệ thống v1 là CLI tool thực hiện:

1. Tìm tin tức bằng keyword → lọc `trillion` → lưu Excel → screenshot → tạo bài AI → hỗ trợ đăng LinkedIn thủ công.

### 2.2 Quy trình mới (v2)

Input đã sẵn sàng trong file Google Sheet `Trillion $ news(1).xlsx`.

File Excel này đã có:

- Tiêu đề tin tức (`Trillion $ news Title`).
- Link ảnh Google Drive (`Image link`).
- Nội dung bài đăng đã viết sẵn cho từng nền tảng: `Linkedin`, `Facebook`, `X (Twitter)`, `Instagram`, `Pinterest`, `Threads`, `TikTok`, `YouTube`.
- Cột `Link Post` để lưu link bài đăng sau khi post.

**Hệ thống v2 chỉ cần:**

1. Đọc file Excel.
2. Tải ảnh từ Google Drive link.
3. Đăng nhập lần lượt 8 nền tảng mạng xã hội.
4. Đăng bài với nội dung + ảnh tương ứng từng nền tảng.
5. Mỗi nền tảng đăng 2 bài mỗi lần chạy (configurable).
6. Lấy link bài đăng → ghi lại vào cột `Link Post`.
7. Cung cấp giao diện web để người dùng không phải tech có thể chạy tool.
8. Hỗ trợ hẹn giờ đăng bài.

---

## 3. Product Goal

Xây dựng hệ thống auto-posting local:

- **Input**: File Excel (Google Sheet export) đã có sẵn nội dung bài viết cho 8 nền tảng.
- **Processing**: Đăng nhập từng nền tảng → đăng bài + ảnh → thu thập link post.
- **Output**: Cột `Link Post` trong Excel được cập nhật link bài đăng thực tế.
- **UI**: Web dashboard để người dùng non-tech thao tác.
- **Scheduling**: Hẹn giờ đăng bài tự động.

---

## 4. Non-Goals

Hệ thống v2 không làm:

- Không tìm kiếm tin tức mới (input đã có sẵn trong Excel).
- Không tạo nội dung AI (bài viết đã có sẵn trong Excel).
- Không crawl web.
- Không bypass captcha phức tạp (dùng persistent browser session).
- Không quản lý nhiều tài khoản cùng lúc cho 1 nền tảng.
- Không cần mobile app.

---

## 5. Scope

### 5.1 Core Scope (MVP)

1. Đọc file Excel input (`Trillion $ news(1).xlsx`).
2. Tải ảnh từ Google Drive link.
3. Đăng bài tự động lên 8 nền tảng: LinkedIn, Facebook, X (Twitter), Instagram, Pinterest, Threads, TikTok, YouTube.
4. Mỗi nền tảng đăng 2 bài/lần chạy (configurable).
5. Thu thập link bài đăng → ghi vào cột `Link Post`.
6. CLI interface để chạy.

### 5.2 Enhanced Scope (v2+)

1. Web UI dashboard cho người dùng non-tech.
2. Hẹn giờ đăng bài (scheduling).
3. Xem trước bài viết trước khi đăng.
4. Dashboard thống kê trạng thái đăng bài.
5. Notification khi đăng xong hoặc lỗi.

---

## 6. Input Data — Excel Schema

### 6.1 File

```
Trillion $ news(1).xlsx
```

### 6.2 Sheets

File có nhiều sheet, mỗi sheet là một chủ đề (category):

| Sheet | Description |
|---|---|
| Payment | Tin tức về Payment, Fintech, Cross-border |
| Charity & Tokenization | Tin tức về Charity, Tokenization |
| *(thêm sheet mới theo nhu cầu)* | |

### 6.3 Columns (mỗi sheet đều giống nhau)

| Col | Header | Type | Description |
|---:|---|---|---|
| 1 | `#` | Number | ID tự tăng |
| 2 | `Trillion $ news Title` | String | Tiêu đề tin tức |
| 3 | `Image link` | URL | Link ảnh trên Google Drive |
| 4 | `Linkedin` | String | Nội dung bài đăng LinkedIn |
| 5 | `Facebook` | String | Nội dung bài đăng Facebook |
| 6 | `X (Twitter)` | String | Nội dung bài đăng X/Twitter |
| 7 | `Instagram` | String | Nội dung bài đăng Instagram |
| 8 | `Pinterest` | String | Nội dung bài đăng Pinterest |
| 9 | `Threads` | String | Nội dung bài đăng Threads |
| 10 | `TikTok` | String | Nội dung bài đăng TikTok |
| 11 | `YouTube` | String | Nội dung bài đăng YouTube |
| 12 | `Link Post` | String | Link bài đăng sau khi post (output) |


> [!NOTE]
> **Lưu ý về dữ liệu thực tế trong file Excel:**
> - Một số tiêu đề cột có khoảng trắng thừa, ví dụ: `'TikTok '` có khoảng trắng phía sau, `' X (Twitter)'` có khoảng trắng phía trước. Hệ thống cần strip (loại bỏ) khoảng trắng hai đầu của tất cả tên cột khi ánh xạ (mapping).
> - Một số sheet (như sheet `Charity & Tokenization`) ban đầu có thể không có cột `Link Post`. Hệ thống phải tự động phát hiện và thêm cột `Link Post` vào cuối sheet khi ghi kết quả bài đăng.

### 6.4 Platform Content Format

Mỗi cell nội dung nền tảng chứa bài viết hoàn chỉnh, bao gồm:

```text
#Hashtag1 #Hashtag2 #Hashtag3 #Hashtag4 #Hashtag5

[Nội dung bài viết]

#TAHKFoundation #HenryUniverses #USIran #USTariffs #Trump
```

### 6.5 Link Post Column — Output Format

Cột `Link Post` (Col 12) sẽ chứa tất cả link bài đăng từ các nền tảng, phân cách bằng newline:

```text
LinkedIn: https://www.linkedin.com/feed/update/urn:li:activity:...
Facebook: https://www.facebook.com/...
X: https://x.com/user/status/...
Instagram: https://www.instagram.com/p/...
Pinterest: https://www.pinterest.com/pin/...
Threads: https://www.threads.net/...
TikTok: https://www.tiktok.com/@user/video/...
YouTube: https://www.youtube.com/post/...
```

Nếu nền tảng nào chưa đăng hoặc lỗi, dòng đó sẽ ghi:

```text
LinkedIn: [pending]
Facebook: [error] Timeout khi đăng bài
```

---

## 7. Supported Platforms

### 7.1 Platform Matrix

| # | Platform | Posting Method | Image Support | Link Capture |
|---:|---|---|---|---|
| 1 | LinkedIn | Playwright browser automation | ✅ Upload image | ✅ From URL after post |
| 2 | Facebook | Playwright browser automation | ✅ Upload image | ✅ From URL after post |
| 3 | X (Twitter) | Playwright browser automation | ✅ Upload image | ✅ From URL after post |
| 4 | Instagram | Playwright browser automation | ✅ Upload image (required) | ✅ From URL after post |
| 5 | Pinterest | Playwright browser automation | ✅ Upload image (required) | ✅ From URL after post |
| 6 | Threads | Playwright browser automation | ✅ Upload image | ✅ From URL after post |
| 7 | TikTok | Playwright browser automation | ✅ Upload image/video | ⚠️ Best-effort |
| 8 | YouTube | Playwright browser automation | ✅ Community post | ⚠️ Best-effort |

### 7.2 Posting Strategy

- Dùng **Playwright persistent browser context** để giữ session login.
- Người dùng login thủ công lần đầu qua giao diện browser → session được lưu.
- Các lần chạy sau không cần login lại (trừ khi session hết hạn).
- Mỗi nền tảng có module riêng để xử lý logic đăng bài.

---

## 8. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Runtime | Python 3.11+ | Đã có từ v1, ecosystem Playwright tốt |
| Browser automation | Playwright | Đăng bài, chụp link, persistent session |
| Excel I/O | openpyxl | Đọc/ghi file `.xlsx` |
| Image download | requests / httpx | Tải ảnh từ Google Drive link |
| Web UI | FastAPI + Jinja2 + HTMX | Server-side rendering, realtime updates, đơn giản |
| Scheduling | APScheduler | Hẹn giờ đăng bài |
| Config | `.env` + `config.yaml` | Dễ cấu hình |
| Storage | Local folder + SQLite (optional) | Session, logs, job queue |
| Logging | Python logging | Structured logs |

---

## 9. System Architecture

### 9.1 High-Level Workflow

```text
Excel File (Input)
       │
       ▼
┌──────────────────┐
│  Excel Reader    │  → Đọc sheet, đọc row, lấy content từng platform
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Image Downloader│  → Tải ảnh từ Google Drive link → lưu local
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│              Platform Poster (8 modules)             │
│                                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────────┐ │
│  │LinkedIn │ │Facebook │ │X/Twitter│ │ Instagram  │ │
│  └─────────┘ └─────────┘ └─────────┘ └────────────┘ │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────────┐ │
│  │Pinterest│ │ Threads │ │ TikTok  │ │  YouTube   │ │
│  └─────────┘ └─────────┘ └─────────┘ └────────────┘ │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Link Collector │  → Thu thập URL bài đăng
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Excel Writer   │  → Ghi link vào cột "Link Post"
              └─────────────────┘
```

### 9.2 Web UI Architecture

```text
┌─────────────────────────────────────────────┐
│                  Browser                     │
│  ┌─────────────────────────────────────────┐ │
│  │          Web Dashboard (HTMX)           │ │
│  │                                         │ │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ │ │
│  │  │Upload   │ │Preview   │ │Schedule  │ │ │
│  │  │Excel    │ │& Select  │ │& Post    │ │ │
│  │  └─────────┘ └──────────┘ └──────────┘ │ │
│  │  ┌─────────────────────────────────────┐ │ │
│  │  │       Status Dashboard              │ │ │
│  │  │  ✅ LinkedIn  ✅ Facebook  ⏳ X    │ │ │
│  │  │  ❌ Instagram  ⏳ Pinterest ...    │ │ │
│  │  └─────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────┘
                   │ HTTP / WebSocket
                   ▼
          ┌─────────────────┐
          │  FastAPI Server  │
          │  + APScheduler   │
          └─────────────────┘
```

---

## 10. Functional Requirements

### FR-001 — Read Excel Input

#### Description

Hệ thống phải đọc file Excel `Trillion $ news(1).xlsx` và parse tất cả sheet.

#### Input

File Excel path (mặc định hoặc user upload qua Web UI).

#### Output

Danh sách `PostItem` từ tất cả sheet.

#### Rules

- Đọc tất cả sheet trong file.
- Mỗi row là 1 tin tức với nội dung cho 8 nền tảng.
- Bỏ qua row không có title (Col 2 rỗng hoặc chỉ chứa khoảng trắng).
- **Xử lý khoảng trắng trong tiêu đề cột (Headers):** Thực hiện loại bỏ khoảng trắng thừa (trim/strip) ở hai đầu của tên cột trước khi thực hiện so khớp nền tảng (ví dụ: biến `' X (Twitter)'` thành `'X (Twitter)'`, `'TikTok '` thành `'TikTok'`).
- **Xử lý cột thiếu:** Nếu sheet nào thiếu cột `Link Post` (ví dụ: `Charity & Tokenization`), trình đọc Excel phải tự hiểu là tất cả các dòng thuộc sheet đó đều ở trạng thái chưa đăng bài (hoặc `[pending]`), và cột này sẽ được thêm tự động khi ghi dữ liệu.
- **Xử lý nội dung rỗng/whitespace:** Cell rỗng, chỉ chứa khoảng trắng (whitespace-only, ví dụ: `' '`, `'  '`), hoặc chỉ chứa ký tự `.` → được coi là không có nội dung cho nền tảng đó → skip nền tảng đó (trạng thái `[skip]`).
- **Kiểm soát đăng trùng (Selective Posting):** Đối với mỗi dòng, nếu cột `Link Post` đã ghi nhận link thành công của một nền tảng (ví dụ: `LinkedIn: https://...` hoặc `LinkedIn: [posted-no-link]`), hệ thống **phải bỏ qua** và không đăng lại trên nền tảng đó. Hệ thống chỉ đăng các nền tảng có trạng thái là `[pending]`, `[error]`, `[login-required]`, hoặc các nền tảng chưa có dòng trạng thái trong cột.
- Bỏ qua row đã có `Link Post` đầy đủ tất cả các nền tảng có nội dung (đã đăng hết).
- Ghi nhận sheet name làm `category`.

#### Acceptance Criteria

- Đọc file có 2 sheet: `Payment` và `Charity & Tokenization`.
- Ánh xạ chính xác các cột nền tảng bất kể có hay không khoảng trắng thừa ở tiêu đề.
- Parse đúng nội dung từng cột platform, tự động loại bỏ khoảng trắng đầu/cuối của nội dung.
- Xác định chính xác các nền tảng cần đăng dựa trên lịch sử trong cột `Link Post`.
- Row có Col 2 rỗng hoặc chỉ chứa khoảng trắng không được parse.

---

### FR-002 — Download Image from Google Drive

#### Description

Hệ thống phải tải ảnh từ Google Drive link trong cột `Image link` (Col 3).

#### Input

Google Drive sharing URL:

```text
https://drive.google.com/file/d/{FILE_ID}/view?usp=sharing
```

#### Output

File ảnh local trong folder `images/`.

#### Image Download Logic

1. Parse `FILE_ID` từ URL.
2. Convert sang direct download URL:

```text
https://drive.google.com/uc?export=download&id={FILE_ID}
```

3. Download và lưu local.
4. Nếu link rỗng hoặc download lỗi → skip ảnh, vẫn đăng bài text-only (nếu platform cho phép).

#### File Naming

```text
images/{sheet}_{row_id}_{slug_title}.{ext}
```

Example:

```text
images/payment_001_merchant_payments.png
```

#### Rules

- Tạo folder `images/` nếu chưa có.
- Không download lại nếu file đã tồn tại.
- Timeout download: 30 giây.
- Hỗ trợ format: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`.

#### Acceptance Criteria

- Link Google Drive hợp lệ → ảnh được tải về.
- Link rỗng → skip, ghi log warning.
- Link lỗi → skip, ghi log error, tiếp tục flow.

---

### FR-003 — Platform Login Management

#### Description

Hệ thống phải quản lý session login cho 8 nền tảng.

#### Login Strategy

1. Sử dụng **Playwright persistent browser context** riêng cho từng nền tảng.
2. Lần đầu: mở browser visible → người dùng login thủ công → session lưu lại.
3. Lần sau: browser tái sử dụng session (cookies/localStorage).
4. Nếu session hết hạn → thông báo người dùng login lại.

#### Browser Context Paths

```text
.browser_sessions/
├── linkedin/
├── facebook/
├── twitter/
├── instagram/
├── pinterest/
├── threads/
├── tiktok/
└── youtube/
```

#### Login Check Flow

```text
1. Open platform URL
2. Check login status (presence of profile element / feed content)
3. If logged in → proceed to post
4. If not logged in → open visible browser → wait for manual login → save session
5. If login timeout (180s) → mark platform as "login_required" → skip
```

#### Acceptance Criteria

- Mỗi nền tảng có session folder riêng.
- Login thành công → session persist cho lần chạy sau.
- Login timeout → skip platform với trạng thái rõ ràng.

---

### FR-004 — Post to Platform

#### Description

Hệ thống phải đăng bài lên từng nền tảng với nội dung và ảnh tương ứng.

#### Input

- Post content (string) từ cột tương ứng trong Excel.
- Image file path (local).
- Platform name.

#### Posting Flow per Platform

```text
1. Check content: cell rỗng hoặc "." → skip platform
2. Open platform in browser
3. Verify login
4. Navigate to post/create page
5. Paste content
6. Upload image (if available)
7. Click Post/Submit
8. Wait for confirmation / URL change
9. Capture post URL
10. Return post URL
```

#### Platform-Specific Logic

Mỗi nền tảng cần module riêng vì UI khác nhau:

##### LinkedIn

```text
- URL: https://www.linkedin.com/feed/
- Trigger: Click "Start a post" button
- Editor: div.ql-editor[role='textbox']
- Image: Media button → file chooser
- Post button: button with "Post" text
- Link capture: URL after redirect or from feed
```

##### Facebook

```text
- URL: https://www.facebook.com/
- Trigger: "What's on your mind?" textbox
- Editor: contenteditable div in composer
- Image: Photo/Video button → file chooser
- Post button: "Post" button
- Link capture: URL of posted content
```

##### X (Twitter)

```text
- URL: https://x.com/compose/post or https://x.com/home
- Trigger: "What is happening?!" textbox
- Editor: contenteditable div in composer
- Image: Media button → file input
- Post button: "Post" button
- Link capture: URL pattern /status/{id}
- Limit: 280 characters (posts may need truncation)
```

##### Instagram

```text
- URL: https://www.instagram.com/
- Trigger: Create (+) button → Post
- Image: Required — select from file
- Caption: Textarea after image selection
- Post button: "Share" button
- Link capture: URL of post after share
```

##### Pinterest

```text
- URL: https://www.pinterest.com/pin-creation-tool/
- Trigger: Direct creation tool
- Image: Required — upload
- Title: Pin title input
- Description: Description textarea
- Post button: "Publish" button
- Link capture: URL of new pin
```

##### Threads

```text
- URL: https://www.threads.net/
- Trigger: Create button
- Editor: Text input area
- Image: Optional attachment
- Post button: "Post" button
- Link capture: URL of new thread
```

##### TikTok

```text
- URL: https://www.tiktok.com/upload (hoặc Creator Center)
- Method: Upload image/slideshow as post
- Caption: Description input
- Post button: "Post" button
- Link capture: Best-effort from redirect
```

##### YouTube

```text
- URL: https://www.youtube.com/
- Method: Community post (nếu channel đủ điều kiện)
- Trigger: Create → Community post
- Editor: Text area
- Image: Optional attachment
- Post button: "Post" button
- Link capture: URL of community post
```

#### Rules

- Không đăng nếu nội dung cell rỗng hoặc chỉ chứa `.`, space.
- Mỗi nền tảng đăng tối đa **2 bài/lần chạy** (configurable).
- Delay giữa các bài đăng: 10–30 giây (configurable, tránh rate limit).
- Delay giữa các nền tảng: 5–15 giây.
- Nếu đăng lỗi → log error → tiếp tục nền tảng tiếp theo.
- Không retry tự động trong MVP (người dùng retry thủ công).

#### Acceptance Criteria

- Đăng bài LinkedIn thành công → link post được capture.
- Platform có cell rỗng → skip, không crash.
- Platform login failed → skip, log rõ ràng.
- Mỗi platform tối đa 2 bài/lần chạy.

---

### FR-005 — Capture Post Link

#### Description

Sau khi đăng bài thành công, hệ thống phải capture URL của bài đăng.

#### Link Capture Strategies

1. **URL change detection**: Theo dõi URL trước/sau khi post.
2. **Feed scan**: Quay lại feed → tìm bài mới nhất → lấy permalink.
3. **API response intercept**: Bắt network response chứa post ID (advanced).
4. **Manual fallback**: Nếu không capture được → đánh dấu `[posted-no-link]`.

#### Rules

- Timeout capture: 15 giây sau khi click Post.
- Nếu không lấy được link → ghi `[posted-no-link]` thay vì fail toàn bộ.
- Link phải là permalink (direct link to post), không phải feed URL.

#### Acceptance Criteria

- Sau khi đăng LinkedIn → capture được link dạng `https://www.linkedin.com/feed/update/...`.
- Nếu capture timeout → ghi `[posted-no-link]`.

---

### FR-006 — Write Link Post to Excel

#### Description

Hệ thống phải ghi link bài đăng vào cột `Link Post` (Col 12) của file Excel.

#### Output Format

Mỗi cell `Link Post` chứa danh sách link, 1 dòng/nền tảng:

```text
LinkedIn: https://www.linkedin.com/feed/update/urn:li:activity:123
Facebook: https://www.facebook.com/post/456
X: https://x.com/user/status/789
Instagram: [pending]
Pinterest: [pending]
Threads: [pending]
TikTok: [skip] No content
YouTube: [skip] No content
```

#### Status Values per Platform

| Status | Meaning |
|---|---|
| `https://...` | Đăng thành công, có link |
| `[posted-no-link]` | Đăng thành công nhưng không capture được link |
| `[pending]` | Chưa đăng |
| `[skip]` | Cell nội dung rỗng, không đăng |
| `[error] message` | Đăng lỗi, có mô tả lỗi |
| `[login-required]` | Cần login lại |

#### Rules

- Ghi ngay sau khi hoàn thành mỗi nền tảng (không đợi xong hết).
- Nếu Link Post đã có nội dung cũ → merge/append, không ghi đè platform đã posted.
- Backup file Excel trước khi ghi (copy thành `*.backup.xlsx`).
- Nếu file đang mở bởi ứng dụng khác → retry 3 lần, rồi báo lỗi.

#### Acceptance Criteria

- Sau khi đăng LinkedIn + Facebook → Link Post có 2 dòng link.
- Link Post giữ lại kết quả cũ nếu đã có.
- File Excel backup tồn tại.

---

### FR-007 — Web UI Dashboard

#### Description

Hệ thống phải có giao diện web đơn giản để người dùng non-tech sử dụng.

#### Pages

##### 1. Home / Dashboard

- Hiển thị danh sách bài viết từ Excel.
- Bảng với columns: `#`, `Title`, `Sheet`, `Platforms`, `Status`, `Actions`.
- Filter theo sheet/category.
- Filter theo trạng thái (pending, posted, error).
- Nút "Start Posting" để bắt đầu.

##### 2. Upload Page

- Upload file Excel mới.
- Validate format (kiểm tra headers).
- Preview nội dung trước khi confirm.

##### 3. Preview Page

- Xem trước nội dung bài viết từng nền tảng cho 1 row.
- Xem ảnh preview.
- Cho phép chỉnh sửa nhỏ trước khi đăng (optional).

##### 4. Posting Control

- Chọn sheet / rows cần đăng.
- Chọn nền tảng muốn đăng (checkbox 8 nền tảng).
- Số bài/nền tảng (mặc định 2).
- Nút "Post Now" và "Schedule Post".
- Realtime progress: hiển thị trạng thái từng nền tảng đang đăng.

##### 5. Login Management

- Hiển thị trạng thái login 8 nền tảng.
- Nút "Login" để mở browser cho từng nền tảng.
- Badge: ✅ Logged in / ❌ Not logged in / ⚠️ Session expired.

##### 6. Schedule Management

- Danh sách job đã schedule.
- Thêm/xóa/sửa schedule.
- Lịch hiển thị các job sắp tới.

##### 7. History / Logs

- Lịch sử đăng bài.
- Log chi tiết từng lần chạy.
- Export log.

#### UI Design

- Mobile-responsive.
- Dark/Light mode.
- Vietnamese UI labels.
- Real-time status updates (HTMX polling hoặc SSE).

#### Acceptance Criteria

- Người dùng non-tech có thể upload Excel → chọn bài → đăng → xem kết quả.
- Không cần mở terminal.
- Status cập nhật realtime khi đang đăng.

---

### FR-008 — Scheduled Posting

#### Description

Hệ thống hỗ trợ hẹn giờ đăng bài.

#### Schedule Types

1. **One-time**: Đăng 1 lần vào thời điểm chỉ định.
2. **Recurring daily**: Đăng hàng ngày vào giờ chỉ định.
3. **Custom cron**: Biểu thức cron cho lịch tùy chỉnh.

#### Schedule Config

```yaml
schedule:
  type: one_time | daily | cron
  time: "09:00"          # HH:MM format (local timezone)
  date: "2026-06-10"     # For one-time only
  cron: "0 9 * * 1-5"    # For cron type (Mon-Fri 9am)
  timezone: "Asia/Ho_Chi_Minh"
  posts_per_platform: 2
  platforms:
    - linkedin
    - facebook
    - twitter
    - instagram
    - pinterest
    - threads
    - tiktok
    - youtube
  sheet: "Payment"        # Optional: specific sheet
```

#### Rules

- Job queue persist qua restart (lưu SQLite hoặc file JSON).
- Nếu miss scheduled time (máy tắt) → chạy ngay khi startup (configurable).
- Log mỗi scheduled run.
- Notification qua Web UI khi schedule chạy xong.

#### Acceptance Criteria

- Schedule đăng 2 bài LinkedIn lúc 9:00 → 9:00 hệ thống tự đăng.
- Schedule persist sau khi restart server.
- Người dùng thấy schedule trong dashboard.

---

## 11. Data Model

### 11.1 PostItem

```python
@dataclass
class PostItem:
    row_id: int                         # Col 1: #
    title: str                          # Col 2: Trillion $ news Title
    image_link: str | None              # Col 3: Image link (Google Drive)
    image_local_path: str | None        # Local path after download
    sheet_name: str                     # Sheet name (category)
    platform_content: dict[str, str]    # Platform → content mapping
    link_post: dict[str, str]           # Platform → post link mapping
    status: str                         # overall status: pending/posting/done/error
```

### 11.2 PlatformSession

```python
@dataclass
class PlatformSession:
    platform: str
    context_dir: str
    is_logged_in: bool
    last_login_check: datetime | None
    last_error: str | None
```

### 11.3 PostJob

```python
@dataclass
class PostJob:
    job_id: str
    created_at: datetime
    scheduled_at: datetime | None
    status: str                         # pending/running/completed/failed
    sheet_name: str | None
    row_ids: list[int]
    platforms: list[str]
    posts_per_platform: int
    results: dict[str, dict]            # platform → {row_id: link}
```

### 11.4 ScheduledTask

```python
@dataclass
class ScheduledTask:
    task_id: str
    schedule_type: str                  # one_time/daily/cron
    schedule_config: dict
    platforms: list[str]
    posts_per_platform: int
    sheet_name: str | None
    is_active: bool
    last_run: datetime | None
    next_run: datetime | None
```

---

## 12. Configuration

### 12.1 `.env`

```env
# Excel Input
EXCEL_FILE=./Trillion $ news(1).xlsx

# Image Storage
IMAGE_DIR=./images

# Browser Sessions
BROWSER_SESSION_DIR=./.browser_sessions

# Web UI
WEB_HOST=0.0.0.0
WEB_PORT=8080

# Posting Config
POSTS_PER_PLATFORM=2
DELAY_BETWEEN_POSTS_SEC=15
DELAY_BETWEEN_PLATFORMS_SEC=10

# Scheduling
TIMEZONE=Asia/Ho_Chi_Minh

# Logging
LOG_DIR=./logs
LOG_LEVEL=INFO
```

### 12.2 `config.yaml`

```yaml
excel_file: "./Trillion $ news(1).xlsx"

platforms:
  linkedin:
    enabled: true
    url: "https://www.linkedin.com/feed/"
    posts_per_run: 2
  facebook:
    enabled: true
    url: "https://www.facebook.com/"
    posts_per_run: 2
  twitter:
    enabled: true
    url: "https://x.com/home"
    posts_per_run: 2
  instagram:
    enabled: true
    url: "https://www.instagram.com/"
    posts_per_run: 2
  pinterest:
    enabled: true
    url: "https://www.pinterest.com/pin-creation-tool/"
    posts_per_run: 2
  threads:
    enabled: true
    url: "https://www.threads.net/"
    posts_per_run: 2
  tiktok:
    enabled: true
    url: "https://www.tiktok.com/upload"
    posts_per_run: 2
  youtube:
    enabled: true
    url: "https://www.youtube.com/"
    posts_per_run: 2

posting:
  delay_between_posts: 15
  delay_between_platforms: 10
  backup_excel_before_write: true
  headless: false

scheduling:
  timezone: "Asia/Ho_Chi_Minh"
  miss_fire_grace_time: 3600
```

---

## 13. CLI Commands

### 13.1 Login

```bash
python main.py login --platform linkedin
python main.py login --all
```

Mở browser để login từng nền tảng. Session lưu lại.

### 13.2 Check Login Status

```bash
python main.py status
```

Hiển thị trạng thái login 8 nền tảng.

### 13.3 Post

```bash
# Đăng 2 bài LinkedIn từ sheet Payment
python main.py post --platform linkedin --sheet Payment --limit 2

# Đăng lên tất cả nền tảng
python main.py post --all --sheet Payment --limit 2

# Đăng row cụ thể
python main.py post --all --row 1 --row 2
```

### 13.4 Start Web UI

```bash
python main.py serve
# → http://localhost:8080
```

### 13.5 Schedule

```bash
# Hẹn đăng lúc 9:00 ngày mai
python main.py schedule --time "09:00" --date "2026-06-10" --all --sheet Payment --limit 2

# Đăng hàng ngày 9:00 sáng
python main.py schedule --daily --time "09:00" --all --limit 2

# Xem schedule
python main.py schedule --list

# Xóa schedule
python main.py schedule --remove JOB_ID
```

---

## 14. Folder Structure

```text
auto-trillion-news-post/
├── SPEC.md
├── README.md
├── AGENTS.md
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── config.yaml
├── main.py                          # CLI entry point
├── Trillion $ news(1).xlsx          # Input Excel file
│
├── src/
│   ├── __init__.py
│   ├── config.py                    # AppConfig loader
│   ├── models.py                    # Data models
│   ├── excel_reader.py              # Read Excel input [NEW]
│   ├── excel_writer.py              # Write Link Post back [REFACTOR]
│   ├── image_downloader.py          # Download from Google Drive [NEW]
│   ├── platform_base.py             # Base class for platform posters [NEW]
│   ├── platforms/                   # Platform-specific posting modules [NEW]
│   │   ├── __init__.py
│   │   ├── linkedin.py
│   │   ├── facebook.py
│   │   ├── twitter.py
│   │   ├── instagram.py
│   │   ├── pinterest.py
│   │   ├── threads.py
│   │   ├── tiktok.py
│   │   └── youtube.py
│   ├── link_collector.py            # Capture post URLs [NEW]
│   ├── session_manager.py           # Browser session management [NEW]
│   ├── scheduler.py                 # APScheduler wrapper [NEW]
│   ├── web/                         # Web UI [NEW]
│   │   ├── __init__.py
│   │   ├── app.py                   # FastAPI app
│   │   ├── routes.py                # API routes
│   │   ├── templates/               # Jinja2 HTML templates
│   │   │   ├── base.html
│   │   │   ├── dashboard.html
│   │   │   ├── upload.html
│   │   │   ├── preview.html
│   │   │   ├── posting.html
│   │   │   ├── login_status.html
│   │   │   ├── schedule.html
│   │   │   └── history.html
│   │   └── static/                  # CSS, JS assets
│   │       ├── style.css
│   │       └── app.js
│   └── logger.py
│
├── images/                          # Downloaded images
├── logs/                            # Application logs
├── .browser_sessions/               # Playwright persistent contexts
│   ├── linkedin/
│   ├── facebook/
│   ├── twitter/
│   ├── instagram/
│   ├── pinterest/
│   ├── threads/
│   ├── tiktok/
│   └── youtube/
│
├── docs/
│   ├── HARNESS.md
│   ├── ARCHITECTURE.md
│   ├── FEATURE_INTAKE.md
│   ├── CONTEXT_RULES.md
│   └── ...
│
├── scripts/
│   └── bin/
│       └── harness-cli
│
└── tests/
    ├── test_excel_reader.py
    ├── test_image_downloader.py
    ├── test_link_collector.py
    ├── test_session_manager.py
    └── test_platforms/
        ├── test_linkedin.py
        └── ...
```

---

## 15. Migration from v1

### 15.1 Files to Keep

| File | Action |
|---|---|
| `src/config.py` | Refactor — thêm platform configs |
| `src/models.py` | Refactor — thay `NewsItem` bằng `PostItem` |
| `src/assisted_posting.py` | Refactor → `src/platforms/linkedin.py` |
| `main.py` | Refactor — thêm commands mới |
| `.env` / `config.yaml` | Update — thêm configs mới |
| `requirements.txt` | Update — thêm FastAPI, APScheduler, httpx |

### 15.2 Files to Remove/Archive

| File | Action |
|---|---|
| `src/searcher.py` | Archive — không còn search tin |
| `src/filter.py` | Archive — không còn filter |
| `src/image_capture.py` | Replace → `src/image_downloader.py` |
| `src/ai_writer.py` | Archive — không còn tạo AI content |
| `src/post_writer.py` | Archive — không còn write markdown posts |
| `src/excel_store.py` | Refactor → `src/excel_reader.py` + `src/excel_writer.py` |
| `keywords.txt` | Archive — không còn dùng |
| `post_all.py` | Archive — thay bằng CLI + Web UI |

### 15.3 New Files

| File | Purpose |
|---|---|
| `src/excel_reader.py` | Đọc Excel input mới |
| `src/excel_writer.py` | Ghi Link Post |
| `src/image_downloader.py` | Tải ảnh Google Drive |
| `src/platform_base.py` | Base class cho platform posters |
| `src/platforms/*.py` | 8 platform modules |
| `src/link_collector.py` | Thu thập link bài đăng |
| `src/session_manager.py` | Quản lý browser sessions |
| `src/scheduler.py` | Job scheduling |
| `src/web/*` | Web UI |

---

## 16. Implementation Plan

### Phase 1 — Core Refactor (Foundation)

Tasks:

- Refactor `models.py` → `PostItem`, `PlatformSession`, `PostJob`.
- Create `excel_reader.py` — đọc Excel theo schema mới.
- Create `image_downloader.py` — tải ảnh Google Drive.
- Create `session_manager.py` — quản lý browser sessions.
- Create `platform_base.py` — abstract base class.
- Refactor `config.py` — thêm platform configs.
- Update `requirements.txt`.

Acceptance:

- `python main.py status` hiển thị 8 nền tảng.
- Excel đọc đúng 2 sheet, parse đúng columns.

---

### Phase 2 — Platform Posting Modules

Tasks:

- Implement `platforms/linkedin.py` (refactor từ `assisted_posting.py`).
- Implement `platforms/facebook.py`.
- Implement `platforms/twitter.py`.
- Implement `platforms/instagram.py`.
- Implement `platforms/pinterest.py`.
- Implement `platforms/threads.py`.
- Implement `platforms/tiktok.py`.
- Implement `platforms/youtube.py`.
- Implement `link_collector.py`.
- Implement `excel_writer.py` — ghi Link Post.

Acceptance:

- `python main.py login --all` mở browser cho từng nền tảng.
- `python main.py post --platform linkedin --limit 2` đăng 2 bài.
- Link Post được ghi vào Excel.

---

### Phase 3 — Web UI

Tasks:

- Setup FastAPI + Jinja2 + HTMX.
- Implement Dashboard page.
- Implement Upload page.
- Implement Preview page.
- Implement Posting Control page.
- Implement Login Management page.
- Implement History page.
- Realtime posting status.

Acceptance:

- `python main.py serve` → http://localhost:8080.
- Upload Excel → preview → chọn bài → đăng → xem link.
- Non-tech user có thể sử dụng.

---

### Phase 4 — Scheduling

Tasks:

- Implement `scheduler.py` với APScheduler.
- Implement Schedule Management page (Web UI).
- Implement schedule CLI commands.
- Persist jobs qua restart.

Acceptance:

- Schedule đăng 9:00 → hệ thống tự đăng đúng giờ.
- Job list hiển thị trong Web UI.
- Jobs persist qua restart.

---

## 17. Validation Rules

### 17.1 Excel Input Validation

- File phải có extension `.xlsx`.
- Mỗi sheet phải có header row đúng format.
- Col 1 (`#`) phải là số.
- Col 2 (`Title`) không được rỗng cho row hợp lệ.

### 17.2 Platform Content Validation

- Nội dung rỗng, `None`, hoặc chỉ chứa `.` / spaces → skip nền tảng đó.
- X (Twitter) content > 280 chars → truncate hoặc warning.
- Instagram/Pinterest phải có ảnh → nếu không có ảnh → warning.

### 17.3 Post Link Validation

- Link phải bắt đầu bằng `https://`.
- Link phải chứa domain tương ứng platform.

---

## 18. Error Handling

| Error | Expected Behavior |
|---|---|
| Excel file not found | Show clear error, suggest upload |
| Excel format invalid | Show validation errors, list bad columns |
| Google Drive link expired | Skip image, continue with text-only post |
| Image download timeout | Skip image, log warning |
| Platform login expired | Prompt re-login, skip platform this run |
| Platform UI changed | Stop that platform, log error, continue others |
| Post failed | Log error, mark `[error]` in Link Post, continue |
| Link capture failed | Mark `[posted-no-link]`, continue |
| Excel file locked | Retry 3x with 2s delay, then error |
| Scheduled job missed | Run immediately on next startup (configurable) |
| Browser crash | Clean shutdown, log error, report in UI |

---

## 19. Logging

### 19.1 Log Location

```text
logs/YYYY-MM-DD.log
```

### 19.2 Log Examples

```text
[INFO] 2026-06-10 09:00:01 — Reading Excel: Trillion $ news(1).xlsx
[INFO] 2026-06-10 09:00:01 — Found 2 sheets: Payment (134 rows), Charity & Tokenization (2 rows)
[INFO] 2026-06-10 09:00:02 — Downloading image for row 1: payment_001_merchant_payments.png
[INFO] 2026-06-10 09:00:05 — Starting LinkedIn posting (2 posts)
[INFO] 2026-06-10 09:00:10 — LinkedIn: Posted row 1 — https://linkedin.com/feed/update/...
[INFO] 2026-06-10 09:00:25 — LinkedIn: Posted row 2 — https://linkedin.com/feed/update/...
[INFO] 2026-06-10 09:00:30 — Starting Facebook posting (2 posts)
[WARN] 2026-06-10 09:00:35 — Facebook: Login session expired, skipping
[INFO] 2026-06-10 09:00:40 — Starting X/Twitter posting (2 posts)
[ERROR] 2026-06-10 09:01:00 — X/Twitter: Post failed for row 1 — Timeout waiting for post button
[INFO] 2026-06-10 09:01:15 — Excel updated: Link Post column for rows 1, 2
[INFO] 2026-06-10 09:01:16 — Run completed: 4 posted, 1 skipped, 1 error
```

---

## 20. Security Requirements

- Không lưu password người dùng.
- Browser session data lưu local, không upload.
- `.browser_sessions/` phải nằm trong `.gitignore`.
- `.env` phải nằm trong `.gitignore`.
- Web UI chỉ chạy local (mặc định `localhost`).
- Không expose Web UI ra internet nếu không có authentication.

---

## 21. Test Plan

### 21.1 Unit Tests

- `test_excel_reader.py`: Đọc Excel đúng schema, xử lý empty cells.
- `test_image_downloader.py`: Parse Google Drive URL, download mock.
- `test_link_collector.py`: Parse link từ URL pattern.
- `test_session_manager.py`: Check login status logic.

### 21.2 Integration Tests

- Đăng 1 bài LinkedIn test → verify link capture.
- Đọc Excel → download image → post → ghi link → verify Excel.

### 21.3 Manual Tests

- Non-tech user test Web UI flow.
- Schedule job → verify auto-run.
- Session expire → verify re-login flow.

---

## 22. Acceptance Criteria for v2 MVP

v2 MVP hoàn thành khi:

1. ✅ Đọc được file `Trillion $ news(1).xlsx` với tất cả sheets.
2. ✅ Tải ảnh từ Google Drive links.
3. ✅ Login thành công 8 nền tảng (persistent session).
4. ✅ Đăng bài thành công lên ít nhất 3 nền tảng (LinkedIn, Facebook, X).
5. ✅ Mỗi nền tảng đăng 2 bài/lần chạy.
6. ✅ Thu thập link bài đăng → ghi vào cột `Link Post`.
7. ✅ CLI interface hoạt động.
8. ✅ Web UI dashboard hoạt động cho non-tech user.
9. ✅ Hẹn giờ đăng bài hoạt động.
10. ✅ Không crash khi 1 nền tảng lỗi → tiếp tục nền tảng khác.

---

## 23. Example Run

### 23.1 CLI Run

```bash
# Step 1: Login tất cả nền tảng (lần đầu)
python main.py login --all

# Step 2: Đăng 2 bài cho mỗi nền tảng từ sheet Payment
python main.py post --all --sheet Payment --limit 2

# Output:
# [INFO] Reading Excel: Trillion $ news(1).xlsx
# [INFO] Sheet Payment: 134 rows
# [INFO] Downloading image for row 1...
# [INFO] Downloading image for row 2...
# [INFO] LinkedIn: Posting row 1...  ✅ https://linkedin.com/...
# [INFO] LinkedIn: Posting row 2...  ✅ https://linkedin.com/...
# [INFO] Facebook: Posting row 1... ✅ https://facebook.com/...
# [INFO] Facebook: Posting row 2... ✅ https://facebook.com/...
# ...
# [INFO] Excel updated: Link Post for rows 1, 2
# [INFO] Done. 16 posts across 8 platforms.
```

### 23.2 Excel After Run

| # | Title | Image link | ... | Link Post |
|---:|---|---|---|---|
| 1 | Merchant Payments: a $100 Trillion... | https://drive.google.com/... | ... | LinkedIn: https://linkedin.com/...<br>Facebook: https://facebook.com/...<br>X: https://x.com/...<br>Instagram: [posted-no-link]<br>Pinterest: https://pinterest.com/...<br>Threads: https://threads.net/...<br>TikTok: [skip] No content<br>YouTube: [skip] No content |

---

## 24. Future Enhancements

Sau v2 MVP, có thể nâng cấp:

1. Google Sheet API integration (đọc/ghi trực tiếp Google Sheet thay vì file Excel).
2. Telegram/Slack notification khi đăng xong hoặc lỗi.
3. Multi-account support (nhiều tài khoản cho 1 nền tảng).
4. AI content regeneration cho nền tảng chưa có nội dung.
5. Analytics dashboard (engagement tracking).
6. Bulk retry cho các bài bị lỗi.
7. A/B testing — đăng 2 version content khác nhau.
8. Image editing/branding overlay tự động.
9. Mobile-responsive Web UI hoàn chỉnh.
10. Docker deployment cho team sử dụng.

---

## 25. Brownfield Migration Notes

### v1 → v2 Key Changes

| Aspect | v1 | v2 |
|---|---|---|
| Input | Search Google/Bing → filter | File Excel đã có sẵn |
| Content | AI generate | Có sẵn trong Excel |
| Platforms | LinkedIn only | 8 nền tảng |
| Posting | Assisted (human click Post) | Full auto-post |
| Output | Markdown files + Excel | Link Post trong Excel |
| UI | CLI only | CLI + Web UI |
| Scheduling | None | APScheduler |
| Architecture | Monolith main.py | Modular platform plugins |

### Breaking Changes

- `NewsItem` model thay bằng `PostItem`.
- Excel schema hoàn toàn khác (input vs output columns).
- CLI commands thay đổi hoàn toàn.
- `src/searcher.py`, `src/filter.py`, `src/ai_writer.py` bị archive.

### Backward Compatibility

- v1 code được archive trong branch `v1-archive`.
- v1 output folder (`output/`) không bị xóa.
- v1 `.env` keys vẫn hoạt động nhưng thêm keys mới.
