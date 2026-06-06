# SPEC.md — Trillion News Auto Post System

## 1. Document Control

| Field | Value |
|---|---|
| Product name | Trillion News Auto Post System |
| Document type | Seed product specification for brownfield realignment |
| Version | 2.0 |
| Status | Approved for decomposition |
| Primary user | Content Admin / Marketing Operator |
| Runtime model | Local tool, operator-driven |
| Primary language | Vietnamese for operations, English for generated social drafts |

## 2. Purpose of This Spec

Tài liệu này tồn tại để chốt lại product contract cho repo brownfield hiện tại.

Mục tiêu của bản final này là:

- Phân biệt rõ đâu là năng lực đã có trong repo và đâu là target v2.
- Loại bỏ các mô tả bị lặp, mâu thuẫn, hoặc nói trước implementation.
- Chốt data contract đủ rõ để tiếp tục tách `docs/product/*`, `docs/stories/*`, validation, và implementation.

Theo Harness của repo, đây là seed specification. Sau khi tách xong thành product docs và story packets, các thay đổi tiếp theo không nên tiếp tục dồn ngược vào một spec lớn khác.

## 3. Brownfield Snapshot

### 3.1 Implemented Baseline in Repo

Repo hiện đã có các năng lực đã được thể hiện trong code và test:

- CLI `init`, `search`, `generate`, `run`, `post`.
- Tìm tin tức bằng Playwright từ search engine.
- Lọc tin liên quan đến chủ đề `trillion`.
- Loại bỏ trùng lặp theo URL/title đã chuẩn hóa.
- Chụp screenshot local cho bài giữ lại.
- Gọi Gemini để tạo social draft.
- Ghi dữ liệu vào workbook nội bộ 14 cột.
- Assisted posting cho LinkedIn theo luồng có người vận hành xác nhận.
- Test cho `excel_store`, `filter`, validation, và assisted posting mock.

### 3.2 Not Yet Implemented but Previously Described as Ready

Các hạng mục sau chưa được xem là implemented ở thời điểm chốt spec này:

- Đọc workbook business nhiều sheet theo schema `Trillion $ news.xlsx`.
- Tự động đăng thống nhất lên đủ 8 nền tảng từ một row business workbook.
- Cơ chế selective posting dựa trên `Link Post`.
- Lớp poster chung cho nhiều nền tảng với write-back kết quả riêng từng platform.
- Web UI FastAPI/Jinja2/HTMX.
- Scheduling local bền vững cho posting jobs.
- Dashboard lịch sử, thông báo, và vận hành đa luồng hoàn chỉnh.

### 3.3 Problems Found in the Previous SPEC

Các vấn đề chính đã được sửa trong bản final:

- File chứa conflict marker và hai phiên bản spec chồng lên nhau.
- Trộn lẫn current state với target state làm người đọc dễ hiểu nhầm repo đã có đủ v2.
- Đi quá sâu vào implementation detail theo platform thay vì chốt product contract.
- Không làm rõ sự khác nhau giữa workbook nội bộ hiện có và workbook business target.
- Cố định các giá trị nên để ở config, ví dụ giới hạn số bài mỗi lần chạy.

## 4. Product Vision

Xây dựng một local operations tool giúp team nội dung chạy đúng luồng nghiệp vụ mà khách hàng yêu cầu:

1. Nhập từ khóa.
2. Tìm kiếm và lọc tin tức bằng Playwright scraper.
3. Chụp ảnh màn hình tin tức và lưu local.
4. Dùng Gemini sinh 8 nội dung bài đăng cho 8 nền tảng.
5. Ghi tiêu đề, ảnh local, và 8 bài nháp vào workbook vận hành `Trillion $ news.xlsx`.
6. Cho phép người dùng mở Excel để xem trước hoặc chỉnh sửa nếu muốn.
7. Đọc lại workbook để tự động đăng lên 8 nền tảng bằng session đã lưu.
8. Lấy link bài đăng thực tế và ghi ngược lại vào cột `Link Post`.

Đây không phải là sản phẩm SaaS đa tenant. Đây là công cụ nội bộ chạy local, ưu tiên ổn định vận hành hơn là độ phức tạp hệ thống.

## 5. Users and Operating Model

### 5.1 Primary User

Người dùng chính là Content Admin / Marketing Operator:

- Biết thao tác file Excel và trình duyệt.
- Không cần biết lập trình.
- Có thể đăng nhập thủ công vào các nền tảng khi hệ thống yêu cầu.

### 5.2 Operating Model

Hệ thống chạy trên máy local của team:

- Dùng browser thật.
- Lưu session local theo từng nền tảng.
- Lưu workbook, ảnh, draft, và logs trên filesystem local.
- Chấp nhận có bước human-in-the-loop khi login, captcha, hoặc nền tảng thay đổi UI.

## 6. Scope

### 6.1 In Scope

- Giữ ổn định pipeline baseline hiện có.
- Chuẩn hóa rõ hai pipeline: Harvesting/Draft Generation và Business Posting.
- Dùng `Trillion $ news.xlsx` làm workbook vận hành chính của v2.
- Hỗ trợ target 8 nền tảng: LinkedIn, Facebook, X, Instagram, Pinterest, Threads, TikTok, YouTube.
- Session login persistent theo từng nền tảng.
- Xử lý ảnh từ local path hoặc Google Drive sharing URL.
- Sinh đủ 8 draft social cho mỗi bài được giữ lại trong flow v2.
- Ghi kết quả đăng bài vào `Link Post`.
- Có CLI tiếp tục dùng được.
- Có Web UI cơ bản ở giai đoạn sau.
- Có scheduling local ở giai đoạn sau.

### 6.2 Out of Scope

- Mobile app.
- Quản lý nhiều account đồng thời cho cùng một nền tảng trong một lần chạy.
- Bypass captcha hoặc xác minh bảo mật phức tạp.
- Hệ thống cloud multi-user với phân quyền phức tạp.
- Đồng bộ trực tiếp với Google Sheets API trong MVP.
- Video editing hoặc media pipeline phức tạp.

### 6.3 Brownfield Guardrails

Refactor v2 phải giữ các nguyên tắc sau:

- Không làm vỡ CLI baseline hiện có nếu chưa có quyết định chấp thuận rõ ràng.
- Không xóa pipeline harvest + generate hiện có.
- Không bắt người dùng phải chuyển ngay sang UI mới.
- Không buộc người dùng tự sửa tay workbook để thích nghi với thay đổi schema nếu việc đó có thể xử lý bằng mapping trong hệ thống.

## 7. Product Model

### 7.1 Pipeline A — Harvesting and Draft Generation

Input:

- `keywords.txt` hoặc danh sách keyword do người vận hành cung cấp.

Output:

- News items đã lọc.
- Screenshot local.
- 8 social drafts cho 8 nền tảng target.
- Dữ liệu được ghi vào workbook vận hành chính `Trillion $ news.xlsx` theo contract business workbook của v2.

### 7.2 Pipeline B — Business Workbook Posting

Input:

- Workbook business nhiều sheet, mỗi row là một nội dung có thể đăng đa nền tảng.
- Ảnh local path hoặc Google Drive sharing URL.

Output:

- Kết quả đăng bài cho từng nền tảng.
- Permalink nếu lấy được.
- Trạng thái lỗi hoặc skip nếu không đăng được.
- `Link Post` được cập nhật tại đúng row.

### 7.3 End-to-End Golden Flow

Luồng chuẩn mà v2 phải phục vụ là:

```text
[Từ khóa / Keywords]
       │
       ▼
Pipeline A
1. Tìm kiếm tin tức bằng Playwright scraper
2. Lọc tin tức theo từ khóa/thesis đã nhập
3. Chụp ảnh màn hình tin tức và lưu local
4. Gemini sinh 8 nội dung bài đăng cho 8 nền tảng
5. Ghi title, ảnh local, draft của 8 nền tảng vào Trillion $ news.xlsx
       │
       ├─► Người dùng có thể mở Excel để xem trước hoặc chỉnh sửa
       │
       ▼
Pipeline B
6. Đọc draft từ Trillion $ news.xlsx và bỏ qua các platform đã có Link Post thành công
7. Đăng bài lên 8 nền tảng qua Playwright bằng session lưu sẵn
8. Capture link bài đăng thực tế và ghi ngược lại vào cột Link Post
```

### 7.4 Control Surfaces

- CLI là surface bắt buộc phải duy trì.
- Web UI là surface bổ sung cho vận hành non-tech.

### 7.5 Operator Review Gate

Giữa Pipeline A và Pipeline B phải có một review gate hợp lệ:

- Người dùng được phép mở `Trillion $ news.xlsx` để xem trước.
- Người dùng được phép sửa nội dung draft từng nền tảng trước khi post.
- Hệ thống phải xem nội dung trong Excel là dữ liệu cuối cùng để dùng cho posting.

### 7.6 Automation Layer

- Scheduling là lớp bổ sung sau posting core.
- Dashboard/lịch sử là lớp bổ sung sau khi đã có job model ổn định.

## 8. Source of Truth and Data Contracts

Đây là phần quan trọng nhất của bản final vì đây là nơi spec cũ mơ hồ nhất.

### 8.1 Contract A — Internal Harvest Workbook

Workbook nội bộ hiện có trong code là contract baseline cần được giữ tương thích. Schema hiện tại gồm 14 cột:

1. `ID`
2. `Found Date`
3. `Keyword`
4. `Title`
5. `Source`
6. `URL`
7. `Snippet`
8. `Published Text`
9. `Image File`
10. `Platform`
11. `Top Hashtags`
12. `Generated Post File`
13. `Status`
14. `Notes`

Workbook này phục vụ compatibility với baseline hiện có, không phải workbook vận hành chính mà khách hàng yêu cầu cho v2.

### 8.2 Contract B — Business Posting Workbook

Workbook business target, đồng thời là workbook vận hành chính của v2 cho cả Pipeline A và Pipeline B, là file `.xlsx` nhiều sheet:

```text
Trillion $ news.xlsx
```

Mỗi sheet là một category/chủ đề. Mỗi row là một bài có thể đăng lên nhiều nền tảng. Đây là nơi Pipeline A ghi draft và Pipeline B đọc lại để post.

Schema target:

| Col | Header | Meaning |
|---:|---|---|
| 1 | `#` | Row ID trong sheet |
| 2 | `Trillion $ news Title` | Tiêu đề tin tức |
| 3 | `Image link` | Google Drive URL hoặc local image path |
| 4 | `Linkedin` | Draft cho LinkedIn |
| 5 | `Facebook` | Draft cho Facebook |
| 6 | `X (Twitter)` | Draft cho X |
| 7 | `Instagram` | Draft cho Instagram |
| 8 | `Pinterest` | Draft cho Pinterest |
| 9 | `Threads` | Draft cho Threads |
| 10 | `TikTok` | Draft cho TikTok |
| 11 | `YouTube` | Draft cho YouTube |
| 12 | `Link Post` | Kết quả đăng bài theo từng nền tảng |

### 8.3 Brownfield Decision on the Two Contracts

v2 phải hỗ trợ đồng thời hai contract:

- Internal workbook cho compatibility của baseline hiện có.
- Business workbook `Trillion $ news.xlsx` làm source of truth vận hành chính cho customer flow.

Không được giả định rằng người dùng phải tự quản lý hai workbook riêng để chạy flow chính. Nếu cần mapping hoặc conversion từ legacy flow sang workbook business, đó là trách nhiệm của implementation, không phải của người dùng vận hành.

### 8.4 Header Normalization Rule

Khi đọc business workbook:

- Tất cả header phải được `strip()` khoảng trắng đầu/cuối.
- Mapping header không được fail chỉ vì sai khác whitespace.
- `TikTok ` và `TikTok` là một.
- ` X (Twitter)` và `X (Twitter)` là một.

### 8.5 Missing Column Rule

Nếu một sheet thiếu cột `Link Post`:

- Sheet vẫn được xem là hợp lệ để đọc.
- Mặc định mọi platform trên row đó được xem là chưa có kết quả đăng.
- Hệ thống phải tự tạo cột `Link Post` khi cần ghi kết quả.

### 8.6 Content Cell Rule

Một ô draft được xem là không có nội dung khi:

- Rỗng.
- Chỉ có whitespace.
- Chỉ chứa dấu `.`

Platform tương ứng phải được skip, không bị xem là lỗi hệ thống.

### 8.7 `Link Post` Format

`Link Post` là một text block, mỗi dòng ứng với một nền tảng:

```text
LinkedIn: https://...
Facebook: https://...
X: [posted-no-link]
Instagram: [error] upload failed
Pinterest: [skip] no content
Threads: [login-required]
```

Các trạng thái hợp lệ:

- URL thành công.
- `[pending]`
- `[skip] <reason>`
- `[error] <reason>`
- `[login-required]`
- `[posted-no-link]`

### 8.8 Selective Posting Rule

Hệ thống không được đăng trùng trên cùng row cho cùng platform.

Cho mỗi `row x platform`:

- Nếu `Link Post` đã có URL thành công hoặc `[posted-no-link]` thì phải bỏ qua.
- Nếu đang là `[pending]`, `[error]`, `[login-required]`, hoặc chưa có dòng nào cho platform đó thì được phép thử lại.
- Nếu không có draft content thì phải skip platform đó.

### 8.9 Posting Limits Rule

Theo yêu cầu khách hàng cho MVP vận hành:

- Mỗi nền tảng đăng `2 bài` trong mỗi lần chạy posting mặc định.
- Hệ thống phải ưu tiên chọn 2 row hợp lệ tiếp theo cho từng platform, sau khi đã áp dụng selective posting rule.
- Ở lớp nâng cao, giới hạn này nên có thể cấu hình qua CLI config hoặc UI/scheduler, nhưng mặc định nghiệp vụ ban đầu là `2`.

### 8.10 `Link Post` Customer Constraint and Parser Rule

Customer workbook hiện bị ràng buộc chỉ có một cột `Link Post` chung.

Quyết định chốt cho MVP:

- Giữ một cột `Link Post` để tương thích workbook customer hiện tại.
- Hệ thống phải có parser và writer an toàn cho từng dòng `Platform: value`.
- Khi ghi kết quả cho một platform, hệ thống không được làm hỏng hoặc xóa trạng thái của các platform khác.
- Nếu người dùng sửa tay sai format, hệ thống phải báo lỗi parse rõ ràng thay vì silently overwrite.

### 8.11 Google Drive Accessibility Rule

Với `Image link` là Google Drive URL, hệ thống chỉ được xem là tải thành công khi có thể truy cập trực tiếp mà không cần login Google bổ sung trong luồng tải ảnh.

Các rule bắt buộc:

- Nếu file không public hoặc không tải được, platform yêu cầu ảnh phải nhận trạng thái `[error] image inaccessible`.
- Nếu file không tải được nhưng platform cho phép text-only, hệ thống được phép tiếp tục text-only.
- Nếu link không trỏ tới ảnh hợp lệ hoặc định dạng file không hỗ trợ, xử lý như lỗi ảnh không hợp lệ.
- Nếu file quá lớn hoặc tải timeout, lỗi phải được ghi rõ để operator biết nguyên nhân.

### 8.12 Platform Capability Matrix for MVP

| Platform | Text-only allowed | Image/video required for MVP | MVP posting mode notes |
|---|---|---|---|
| LinkedIn | Yes | No | Standard feed post, image optional |
| Facebook | Yes | No | Feed post, image optional |
| X (Twitter) | Yes | No | Standard post, image optional |
| Instagram | No | Yes | Image-first post |
| Pinterest | No | Yes | Pin/image-first post |
| Threads | Yes | No | Standard thread post, image optional |
| TikTok | No | Yes | MVP scope là photo/image post nếu account và UI hỗ trợ; video upload chưa thuộc MVP |
| YouTube | No | Yes | MVP scope là Community Post nếu channel hỗ trợ; video upload và Shorts chưa thuộc MVP |

Matrix này là contract để quyết định khi nào được phép text-only và khi nào phải trả lỗi ảnh.

## 9. User Requirements

### UR-01 — Keyword Intake

Người vận hành muốn nhập keyword để hệ thống tự tìm tin liên quan đến chủ đề `trillion`.

### UR-02 — Automatic Draft Generation

Người vận hành muốn hệ thống tự sinh 8 draft social cho 8 nền tảng từ các tin đã lọc.

### UR-03 — Excel Review Before Posting

Người vận hành muốn xem và sửa draft trong `Trillion $ news.xlsx` trước khi hệ thống đăng bài.

### UR-04 — Selective Posting

Người vận hành muốn hệ thống đọc lại Excel và chỉ đăng các platform chưa có kết quả thành công.

### UR-05 — Visible Per-Platform Status

Người vận hành muốn biết platform nào đăng thành công, platform nào lỗi, platform nào cần login lại, và platform nào bị skip.

### UR-06 — Safe Posting Limit

Người vận hành muốn mỗi lần chạy chỉ đăng tối đa 2 bài mỗi platform để giảm spam và rủi ro anti-bot.

### UR-07 — Non-Technical Operation

Người vận hành không chuyên kỹ thuật muốn có thể chạy flow chính bằng giao diện dễ dùng thay vì chỉ dựa vào CLI.

### UR-08 — Scheduled Posting

Người vận hành muốn có khả năng hẹn giờ đăng bài ở giai đoạn nâng cao.

## 10. Functional Requirements

### FR-01 — Baseline CLI Compatibility

Hệ thống phải tiếp tục hỗ trợ các lệnh baseline hiện có:

- `init`
- `search`
- `generate`
- `run`
- `post`

Refactor được phép thay đổi module nội bộ, nhưng không được làm vỡ contract vận hành bên ngoài của các lệnh này nếu chưa có quyết định thay đổi rõ ràng.

Acceptance Criteria:

- Given repo baseline hiện tại, when refactor v2 được áp dụng, then các lệnh `init/search/generate/run/post` vẫn còn callable.
- Given không có quyết định thay đổi CLI được chấp thuận, when release được bàn giao, then không có lệnh baseline nào bị remove âm thầm.

### FR-02 — Keyword-Based Harvesting

Pipeline A phải:

- Đọc keyword từ file hoặc input tương đương.
- Tìm tin bằng browser automation trên search engine đã cấu hình.
- Tôn trọng cấu hình headless, provider, và giới hạn kết quả.
- Dừng an toàn hoặc báo lại rõ ràng khi gặp captcha/xác minh.

Acceptance Criteria:

- Given một danh sách keyword hợp lệ, when chạy harvesting, then hệ thống thử tìm theo từng keyword thay vì chỉ keyword đầu tiên.
- Given gặp captcha hoặc xác minh, when scraper không thể tiếp tục an toàn, then run trả về cảnh báo/lỗi rõ ràng thay vì treo im lặng.

### FR-03 — Filtering and De-duplication

Pipeline A phải:

- Lọc theo thesis `trillion`.
- Loại bỏ bài trùng theo URL hoặc title đã normalize.
- Hỗ trợ domain exclusion theo config.

Acceptance Criteria:

- Given tập kết quả có bài trùng URL hoặc title đã normalize, when filter hoàn tất, then chỉ còn một bản ghi hợp lệ.
- Given domain nằm trong danh sách exclude, when filter chạy, then bài từ domain đó không đi tiếp sang bước generate.

### FR-04 — Screenshot Capture

Pipeline A phải:

- Chụp screenshot local cho các bài được giữ lại.
- Đổi tên file temp thành tên ổn định khi lưu.
- Không làm fail toàn bộ run nếu một ảnh chụp lỗi.

Acceptance Criteria:

- Given bài đã qua filter, when screenshot thành công, then file ảnh local tồn tại và có tên ổn định để ghi vào workbook.
- Given một bài screenshot lỗi, when run tiếp tục, then các bài khác vẫn được xử lý tiếp.

### FR-05 — AI Draft Generation

Pipeline A phải:

- Gọi Gemini để tạo draft tiếng Anh cho đủ 8 nền tảng target.
- Validate tối thiểu trước khi chấp nhận kết quả.
- Ghi title, ảnh local, và draft của 8 nền tảng vào `Trillion $ news.xlsx`.

Draft hợp lệ tối thiểu:

- Không chứa placeholder chưa thay thế.
- Có cấu trúc phù hợp với rule đang áp dụng cho platform.

Acceptance Criteria:

- Given một news item hợp lệ, when generate hoàn tất, then workbook nhận đủ 8 ô draft cho 8 nền tảng target hoặc trạng thái lỗi rõ ràng cho bài đó.
- Given draft chứa placeholder hoặc sai format tối thiểu, when validate chạy, then draft đó không được xem là thành công.

### FR-06 — Business Workbook Ingestion

Pipeline B phải:

- Đọc tất cả sheet hợp lệ trong workbook business.
- Giữ lại `sheet name` như category vận hành.
- Bỏ qua row không có title hợp lệ.
- Trim header và trim content.
- Xác định platform cần đăng dựa trên draft content và `Link Post`.
- Xem nội dung đang có trong Excel (hoặc nội dung trong file Markdown được trỏ tới bởi đường dẫn file local trong ô) là nội dung cuối cùng để post, kể cả khi người dùng đã sửa tay.
- Tự động phân giải (resolve) đường dẫn file draft Markdown trong các cột nền tảng thành nội dung bài viết hoàn chỉnh trên ổ đĩa.

Acceptance Criteria:

- Given workbook có nhiều sheet hợp lệ, when ingest chạy, then hệ thống đọc được tất cả row có title hợp lệ.
- Given header có whitespace thừa, when parse workbook, then mapping header vẫn thành công.
- Given row có content là `.`, when xác định platform cần đăng, then platform đó bị skip.
- Given operator sửa draft trong Excel hoặc ghi đường dẫn file draft Markdown, when posting bắt đầu, then hệ thống phân giải và sử dụng nội dung bài viết tương ứng.

### FR-07 — Image Resolution

Pipeline B phải hỗ trợ hai nguồn ảnh:

1. Local image path.
2. Google Drive sharing URL.

Nếu là Google Drive URL, hệ thống phải:

- Tách được `file_id`.
- Chuyển được sang direct download URL.
- Tải/caching ảnh local trước khi đăng.

Nếu không tải được ảnh:

- Với platform cho phép text-only: được tiếp tục text-only.
- Với platform bắt buộc có ảnh: phải ghi lỗi rõ cho đúng platform đó.

Acceptance Criteria:

- Given `Image link` là local path hợp lệ, when posting chuẩn bị media, then hệ thống dùng được file local đó.
- Given Google Drive URL public hợp lệ, when resolve ảnh, then hệ thống tải được về local cache.
- Given Google Drive URL không truy cập được, when platform yêu cầu ảnh, then platform đó nhận `[error] image inaccessible`.

### FR-08 — Platform Session Management

Hệ thống phải:

- Dùng persistent session riêng cho từng nền tảng.
- Hỗ trợ login thủ công lần đầu.
- Tái sử dụng session ở các lần sau.
- Báo trạng thái `login-required` khi session không còn hợp lệ.

Acceptance Criteria:

- Given operator đã login thành công trước đó, when run posting mới bắt đầu, then hệ thống thử tái sử dụng session đã lưu.
- Given session hết hạn hoặc logout, when kiểm tra session thất bại, then platform đó nhận trạng thái `login-required`.

### FR-09 — Multi-Platform Posting Core

Hệ thống phải có một posting core chung và module riêng cho từng nền tảng target:

- LinkedIn
- Facebook
- X
- Instagram
- Pinterest
- Threads
- TikTok
- YouTube

Một platform chỉ được xem là "supported" khi đã có đủ:

- Cơ chế kiểm tra session.
- Luồng mở composer/create-post.
- Điền draft content.
- Gắn ảnh nếu cần.
- Submit bài.
- Thử capture permalink hoặc trạng thái sau đăng.
- Ghi write-back vào `Link Post`.

Lưu ý:

- LinkedIn là baseline platform đã có assisted posting.
- Các platform khác là target capability và có thể được triển khai theo đợt.
- TikTok và YouTube được phép best-effort cho permalink capture.
- Trong mỗi lần chạy posting theo contract customer MVP, mỗi platform xử lý tối đa 2 bài hợp lệ tiếp theo.

Acceptance Criteria:

- Given workbook có nhiều row hợp lệ, when posting run bắt đầu, then mỗi platform chỉ lấy tối đa 2 row hợp lệ tiếp theo cho lần chạy đó.
- Given một platform được gắn nhãn supported trong release hiện tại, when post chạy, then platform đó có đủ check session, điền content, gắn media nếu cần, submit, và write-back kết quả.

### FR-10 — Result Write-Back

Khi posting xong, hệ thống phải:

- Ghi kết quả theo đúng platform vào `Link Post`.
- Không xóa kết quả đã có của platform khác trên cùng row.
- Cho phép cập nhật lại đúng dòng của cùng platform khi retry.
- Nên tạo backup workbook theo timestamp trước khi write-back, trừ khi bị tắt bằng config.
- Có biện pháp an toàn khi workbook đang mở/locked.

Acceptance Criteria:

- Given một platform post thành công, when write-back chạy, then `Link Post` chứa đúng dòng của platform đó.
- Given row đã có kết quả của platform khác, when cập nhật một platform mới, then dữ liệu cũ của platform khác vẫn được giữ nguyên.
- Given backup mode đang bật, when bắt đầu write-back, then hệ thống tạo được một bản backup timestamped trước khi ghi workbook chính.
- Given workbook đang bị lock, when ghi thất bại, then hệ thống trả lỗi rõ ràng thay vì ghi dở dang.

### FR-11 — Failure Isolation and Retry

Hệ thống phải:

- Không để lỗi một platform làm fail toàn bộ run nếu không có lý do nghiêm trọng.
- Cho phép retry có kiểm soát cho các trạng thái `error` và `login-required`.
- Ghi lý do fail đủ rõ để người vận hành biết cần login lại, sửa draft, hay kiểm tra ảnh.

Acceptance Criteria:

- Given một platform thất bại trên một row, when run còn row/platform khác hợp lệ, then các phần còn lại vẫn tiếp tục.
- Given row có trạng thái `error` hoặc `login-required`, when operator chạy lại, then row đó có thể được retry theo selective posting rule.

### FR-12 — CLI Surface for Pipeline B

CLI tương lai cho Pipeline B phải cho phép ít nhất:

- Chạy full flow từ keyword đến workbook business.
- Chọn workbook business.
- Chọn sheet hoặc phạm vi row.
- Chọn platform hoặc tập platform.
- Chạy selective posting.
- Chạy dry-run để xem row/platform nào sẽ được post mà chưa submit thật.
- Kiểm tra trạng thái session/login.

Tên lệnh cụ thể có thể khác, nhưng contract vận hành phải bao phủ được các luồng trên.

Acceptance Criteria:

- Given operator dùng CLI בלבד, when cần chạy flow chính, then CLI bao phủ được từ keyword đến workbook và posting chọn lọc.
- Given operator chỉ muốn post lại một tập row/platform, when dùng CLI, then có cách giới hạn phạm vi posting.
- Given operator chạy dry-run, when hệ thống xử lý workbook, then hệ thống hiển thị danh sách row/platform sẽ đăng nhưng không submit bài thật.

### FR-13 — Web UI Surface

Web UI là target của v2, chưa được xem là baseline hiện có.

Web UI MVP phải cho phép:

- Chọn hoặc nạp workbook.
- Xem danh sách sheet và rows.
- Xem trạng thái session/login theo platform.
- Trigger posting jobs.
- Xem kết quả posting theo row và platform.

Preview và chỉnh sửa draft trong UI là desirable, nhưng không phải điều kiện tối thiểu để xem posting UI là usable.

Acceptance Criteria:

- Given operator non-tech, when dùng UI, then họ có thể chọn workbook, chạy job, và xem trạng thái chính mà không cần CLI.
- Given posting job đã chạy, when mở UI, then operator xem được kết quả theo row/platform.

### FR-14 — Scheduling

Scheduling là target mở rộng sau posting core.

Khi được triển khai, scheduling phải cho phép:

- Tạo lịch chạy local.
- Lưu cấu hình lịch.
- Trigger posting jobs theo giờ.
- Lưu log từng lần chạy.

Nếu scheduling chưa có, spec không được mô tả nó như một capability đã sẵn sàng.

Acceptance Criteria:

- Given operator tạo một lịch hợp lệ, when tới thời điểm chạy, then job posting được trigger tự động.
- Given scheduled run hoàn tất hoặc lỗi, when operator xem lịch sử, then có log kết quả của lần chạy đó.

## 11. Non-Functional Requirements

### 11.1 Reliability

- Lỗi ở một keyword, row, hoặc platform không được làm crash toàn bộ hệ thống.
- Mọi kết quả lỗi phải có message đủ dùng để debug vận hành.

### 11.2 Recoverability

- Session hết hạn phải có luồng login lại rõ ràng.
- Workbook đang bị lock phải được phát hiện và thông báo rõ.

### 11.3 Operability

- Người dùng non-tech có thể vận hành qua workbook và CLI/UI tối thiểu.
- Browser visible phải khả dụng khi cần login hoặc xác nhận thủ công.

### 11.4 Maintainability

- Mỗi platform phải là module riêng.
- Posting core không được trộn chặt vào UI hoặc harvest pipeline.
- Data contract parsing phải tách khỏi selector/UI detail.

### 11.5 Observability

- Có log theo run.
- Có trạng thái per row/per platform.
- Có dấu vết `skip`, `error`, `login-required`, `posted-no-link`.

### 11.6 Performance

- Ưu tiên ổn định hơn tốc độ.
- Không bắt buộc parallel posting tất cả platform trong MVP nếu điều đó làm tăng rủi ro anti-bot hoặc hỏng session.

## 12. Approved Technical Direction

Phần này chỉ chốt các assumption công nghệ đã được repo và quyết định hiện có hỗ trợ:

- Runtime: Python 3.11+.
- Browser automation: Playwright.
- Workbook I/O: `openpyxl`.
- AI provider mặc định: Google Gemini.
- Storage: local filesystem; có thể có SQLite cục bộ nếu scheduling/history cần.

Các chi tiết kiến trúc cụ thể thuộc `docs/ARCHITECTURE.md`, không nên tiếp tục nở ra trong spec này.

## 13. Assumptions

- Operator có quyền đăng bài trên các account social tương ứng.
- Các account có thể được login thủ công ít nhất một lần khi cần khởi tạo session.
- Workbook customer giữ nguyên schema 12 cột trong MVP, trừ trường hợp hệ thống tự bổ sung `Link Post` khi bị thiếu.
- Google Drive image link phải public hoặc truy cập được mà không cần login Google bổ sung trong luồng tải ảnh.
- Browser automation có thể bị ảnh hưởng bởi UI thay đổi, captcha, rate limit, account restriction, hoặc thay đổi chính sách nền tảng.

## 14. Open Questions

- YouTube Community Post có khả dụng trên channel khách hàng hay không?
- TikTok photo/image post có khả dụng trên account khách hàng hay không?
- Có cần hỗ trợ nhiều workbook cùng lúc hay chỉ một workbook vận hành tại một thời điểm?
- Backup workbook có được bật mặc định trong môi trường production nội bộ hay chỉ bật theo config?
- Dry-run có cần xuất ra file/report ngoài console hay chỉ cần hiển thị trong CLI/UI là đủ?

## 15. Workbook Backup and Dry-Run Safety

### 15.1 Workbook Backup Safety

- Trước khi ghi `Link Post`, hệ thống nên tạo bản backup workbook theo timestamp để có thể khôi phục khi write-back lỗi.
- Backup path, retention, và quyền bật/tắt backup nên được cấu hình được.
- Nếu backup thất bại và policy yêu cầu backup bắt buộc, hệ thống không nên tiếp tục write-back thật.

### 15.2 Dry-Run Safety

- Dry-run là chế độ kiểm tra trước khi post thật cho Pipeline B.
- Dry-run phải cho biết sheet nào, row nào, platform nào sẽ được post sau khi áp dụng selective posting rule và posting limits.
- Dry-run không được submit bài, không được thay đổi session, và không được ghi `Link Post` thật vào workbook chính.

## 16. Minimum Logging Contract

Mỗi log event quan trọng trong Pipeline A hoặc Pipeline B nên có tối thiểu các field sau:

- `run_id`
- `timestamp`
- `sheet_name`
- `row_id`
- `platform`
- `action`
- `status`
- `message`

Contract log tối thiểu này tồn tại để:

- Hỗ trợ debug khi posting lỗi.
- Làm nền cho dashboard/history về sau.
- Giúp reviewer và operator truy lại đúng row/platform/action của từng run.

## 17. Security, Session, and Platform Risk

### 17.1 Security Rules

- Hệ thống không được lưu raw password vào workbook, log, hoặc source code.
- Session local phải được xem là dữ liệu nhạy cảm và chỉ lưu trên máy vận hành được kiểm soát.
- Log không được vô tình lộ secrets, cookie, hoặc token đăng nhập.

### 17.2 Platform Automation Rules

- Hệ thống không có mục tiêu bypass captcha hoặc né anti-bot.
- Khi nền tảng yêu cầu xác minh, hệ thống phải dừng ở mức an toàn hoặc yêu cầu operator can thiệp.
- Operator chịu trách nhiệm tuân thủ ToS và chính sách sử dụng của từng nền tảng.

### 17.3 Operational Risk Controls

- Mặc định giới hạn posting là 2 bài mỗi platform mỗi lần chạy để giảm rủi ro.
- Session hết hạn, selector thay đổi, captcha, rate limit, hoặc account restriction phải được xem là rủi ro vận hành bình thường của hệ thống này.
- TikTok và YouTube là hai nền tảng rủi ro cao hơn, nên scope MVP của chúng bị giới hạn hơn các platform còn lại.

## 18. Release Boundaries

### Release A — Brownfield Stabilization

Bao gồm:

- Giữ ổn định `init`, `search`, `generate`, `run`, `post`.
- Chốt lại contract workbook nội bộ.
- Chuẩn hóa logging, config, và error handling tối thiểu.

Done khi:

- Baseline tests còn pass.
- Không có hiểu nhầm giữa baseline đã có và target chưa làm.

### Release B1 — Business Workbook + Shared Posting Core

Bao gồm:

- Ghi kết quả Pipeline A trực tiếp vào `Trillion $ news.xlsx`.
- Đọc workbook business nhiều sheet.
- Header normalization.
- Selective posting.
- Image resolution.
- Shared posting core.
- Write-back `Link Post`.
- Hỗ trợ end-to-end trước cho LinkedIn, Facebook, và X.

Done khi:

- Có thể đi từ keyword đến `Trillion $ news.xlsx` mà không cần sửa tay schema.
- Excel đóng vai trò review gate trước khi post.
- LinkedIn, Facebook, và X chạy được theo selective posting rule và write-back `Link Post`.

### Release B2 — Image-First and Mid-Risk Platforms

Bao gồm:

- Instagram.
- Pinterest.
- Threads.
- Ổn định thêm các rule media handling và login/session cho nhóm platform này.

Done khi:

- Instagram, Pinterest, và Threads chạy được theo capability matrix đã chốt.
- Không đăng trùng khi `Link Post` đã có kết quả thành công.

### Release B3 — High-Risk / Best-Effort Platforms

Bao gồm:

- TikTok photo/image posting mode nếu account/UI hỗ trợ.
- YouTube Community Post mode nếu channel hỗ trợ.
- Best-effort permalink capture cho hai nền tảng này.

Done khi:

- Scope của TikTok và YouTube được chốt rõ theo mode MVP, không bị hiểu thành video upload tổng quát.
- Có thể chứng minh flow customer từ keyword → draft Excel → posting → write-back `Link Post` cho các mode đã chốt.

### Release C — Web UI and Scheduling

Bao gồm:

- Web UI cho vận hành non-tech.
- Scheduling local.
- Dashboard và history cơ bản.

Done khi:

- Người vận hành non-tech có thể chạy các flow chính qua UI.
- Có thể cấu hình hoặc hẹn giờ các đợt post thay cho thao tác CLI thuần.

## 19. Final Acceptance Statement

SPEC này được xem là final cho mục đích brownfield realignment khi thỏa đồng thời các điều sau:

- Không còn conflict marker, section lặp, hoặc hai product truth mâu thuẫn trong cùng file.
- Baseline hiện có và target v2 được tách bạch rõ ràng.
- Hai workbook contract được mô tả rõ và không xung đột.
- Các phần chưa implemented không bị mô tả như đã sẵn sàng.
- Các giá trị đáng ra thuộc config không còn bị hard-code thành product truth.
- Có `User Requirements`, platform capability matrix, acceptance criteria theo FR, và phần security/risk đủ rõ để dev/reviewer dùng làm chuẩn.
- Có `Assumptions`, `Open Questions`, `Workbook Backup and Dry-Run Safety`, và `Minimum Logging Contract` để implementation không bị thiếu guardrails vận hành.

Từ thời điểm này, công việc tiếp theo nên ưu tiên:

1. Tách product docs nhỏ hơn từ spec này.
2. Tạo story packets theo release boundary.
3. Triển khai và chứng minh dần từng năng lực thay vì tiếp tục mở rộng một spec đơn khối.
