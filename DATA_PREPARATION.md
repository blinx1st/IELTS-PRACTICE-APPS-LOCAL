# Chuẩn bị và kiểm tra thư viện Reading / Listening

## Cập nhật bố cục trực tiếp — 22/10/2026

`scripts/prepare_reading_inline.py` dựng đủ **82 nhóm văn bản / 414 câu**. Có 39 nhóm được chép lại theo ảnh nguồn trong `library/preparation/reading-inline-texts.json`; 43 nhóm dùng chữ đã hiệu đính trước đó. Bố cục `flow` lưu các đoạn chữ và token `{number}` theo đúng thứ tự, thay việc đoán dấu chấm lúc chạy app. Nhóm summary có ngân hàng từ tiếp tục lưu chữ cái làm đáp án.

Chạy `python -X utf8 scripts/prepare_reading_inline.py --check` để kiểm tra số câu, nội dung metadata, overrides và registry mà không ghi file. Báo cáo là `library/preparation/reading-inline-review.json`. Bảy bảng và 38 matrix được kiểm tra bởi `scripts/prepare_question_layouts.py --check`; registry giữ đồng thời cả hai loại bố cục.

`backend/presentation.py` chỉ thêm layout cho snapshot cũ có fingerprint khớp. Snapshot, khóa và kết quả cũ không bị ghi lại. Các đoạn đã hỗ trợ highlight trước đây giữ anchor/offset tương thích; annotation cũ dùng mức 1–3 được đọc thành vàng/cam/đỏ, annotation mới dùng trường `color` với năm màu.

Repository nay giữ toàn bộ dữ liệu để chạy, overrides và biên bản JSON cần thiết; các cache OCR, mô hình, ảnh đối chiếu trung gian và audio chuẩn bị trùng vẫn ở máy gốc nhưng không được theo dõi trong Git. Bằng chứng JSON được audio manifest tham chiếu vẫn đi kèm. Clone không cần nguồn PDF hoặc Tesseract để làm bài. Dựng lại bằng OCR từ đầu vẫn cần tài liệu nguồn/cache riêng; kiểm tra bộ file chạy bằng `scripts/check_library.py`.

Thư viện hiện có **32 đề Reading, 32 đề Listening, 96 passages, 128 Parts và 2.560 câu** Cambridge 13–20. Cambridge 16 đã được nhập và đối chiếu. Tài liệu này dành cho việc bảo trì nội dung; sử dụng app hằng ngày không cần chạy OCR, tải mô hình hoặc kết nối Internet.

## Nguồn và cấu trúc

Các PDF người dùng cung cấp được đọc từ `Tài liệu Cambridge/CAMBRIDGE-*/BAN_GOC/`. Không sửa PDF nguồn. Danh sách đường dẫn, dung lượng, số trang và SHA-256 nằm trong [`library/preparation/sources.json`](library/preparation/sources.json).

| Thư mục / tệp | Vai trò |
| --- | --- |
| `library/tests/cam*-test*.json` | Đề đã chuẩn hóa, đoạn văn, nhóm câu, hướng dẫn, lựa chọn và tham chiếu nguồn |
| `library/keys/cam*-test*.json` | Khóa đáp án riêng của dịch vụ, gồm biến thể và nhóm đáp án không phụ thuộc thứ tự |
| `library/assets/*.webp` | Ảnh nguồn cục bộ cho bài đọc và các bố cục câu hỏi cần giữ nguyên |
| `library/preparation/cam*/pNNN.json` | Chữ OCR/embedded, tọa độ từ và khối chữ của từng trang PDF vật lý |
| `library/preparation/overrides/*.json` | Toàn bộ bản đề đã hiệu đính; được ưu tiên khi dựng lại thư viện |
| `library/preparation/*review*.json` | Biên bản đối chiếu trực quan, các sửa lỗi và dấu vết phiên bản |
| `library/preparation/reading-review/*.jpg` | Ảnh đối chiếu đầy đủ hai trang bài đọc của Cambridge 15, 18, 19 |
| `library/preparation/content-audit.json` | Kết quả kiểm tra tự động cấu trúc, số câu, lựa chọn, khóa và đường dẫn ảnh |

Số `page` trong dữ liệu là **trang PDF vật lý, bắt đầu từ 1**, có thể khác số trang in trên sách. `sourcePages` ghi toàn bộ phần đề; `sourceImages` của passage ghi các trang bài đọc, còn của group ghi ảnh vùng câu hỏi.

## Cách dựng lại

Mở PowerShell tại thư mục app. Môi trường Python cần các gói trong `requirements.txt`; bộ cài lần đầu đã cài chúng. Các ví dụ dưới đây dùng Python của app:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_library.py provenance
.\.venv\Scripts\python.exe scripts/prepare_library.py extract --book 13 14 15 16 17 18 19 20 --workers 4
.\.venv\Scripts\python.exe scripts/prepare_library.py assemble
.\.venv\Scripts\python.exe scripts/audit_library.py
```

Lệnh `extract` lưu bộ nhớ đệm trang và tái sử dụng khi đã có dữ liệu phù hợp. Với sách 13–19, mặc định đọc đến trang vật lý 104 để bao phủ toàn bộ phần Reading; sách 20 dùng PDF Reading/Listening 80 trang. Có thể giới hạn một lần thử:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_library.py extract --book 18 --first 63 --last 76 --workers 2
.\.venv\Scripts\python.exe scripts/prepare_library.py assemble --book 18 --test 3
```

`assemble` dựng dữ liệu cơ sở rồi nạp **full override đã hiệu đính** nếu có. Bản override là kết quả cuối dùng để tái tạo chính xác đề đã bàn giao; không xóa nó khi chạy lại OCR. Các helper `review_remaining.py`, `review20.py`, `review18_19_questions.py` và `scripts/review_cam15_questions.py`, `scripts/review_cam17.py` lưu dấu vết hiệu đính trong đợt chuẩn bị ban đầu. Không chạy tất cả helper cũ chồng lên nhau: một helper cũ có thể không bao gồm hiệu đính mới hơn. Luồng dựng lại thông thường chỉ cần raw cache + `assemble` + overrides hiện có.

Khóa đáp án có quy trình riêng:

```powershell
.\.venv\Scripts\python.exe scripts/extract_keys.py
# Tùy chọn: render lại các trang đáp án để người bảo trì kiểm tra.
.\.venv\Scripts\python.exe scripts/extract_keys.py --render
```

`extract_keys.py` dựng lại bản chép đã đối chiếu bằng mắt, không tự tin cậy chữ OCR của đáp án. Khóa sách 20 lấy từ PDF bản gõ lại 144 trang. Các trường hợp đính chính nguồn được ghi trong `errata` của khóa và `keys-report.json`. Không đưa thư mục `library/keys` vào bundle giao diện hoặc thư mục static.

## OCR và các xử lý bố cục

PyMuPDF ưu tiên chữ sẵn trong PDF. Trang scan dùng Tesseract tiếng Anh ở 200 dpi. Mô hình `tessdata_fast/eng.traineddata` đã lưu tại `library/preparation/tessdata/`; nguồn tải chính thức và SHA-256 có trong `sources.json`. Chỉ khi thiếu mô hình, lần chuẩn bị đầu tiên mới cần tải từ kho Tesseract. Máy dùng app sau đó không cần Tesseract/OCR riêng; ảnh và JSON đã được đóng gói.

Các trường hợp đã xử lý trong importer:

- Đường dẫn Windows có dấu: Tesseract nhận đường dẫn mô hình tương đối ASCII; script tự chuyển thư mục làm việc về gốc app.
- OCR chạy bằng các tiến trình riêng, tránh gọi Leptonica đồng thời trong nhiều luồng.
- Cambridge 15 có đầu mục xám khó đọc: ảnh được tăng tương phản và nhị phân hóa trước OCR.
- Một số trang Cambridge 18 bị xoay: tọa độ chữ được đổi về hướng hiển thị của trang.
- Một số trang Cambridge 19 chỉ có lớp chữ quảng bá bên trên ảnh: importer vẫn OCR phần đề.
- Các bài hai cột được đọc hết cột trái rồi mới sang cột phải; ghép lại đoạn tiếp tục qua trang và giữ nhãn A, B, C… đúng với nguồn.
- Ảnh bài đọc giữ toàn bộ mép trang, tránh cắt mất dòng cuối. Ảnh câu hỏi giữ đủ chiều ngang và giới hạn theo nhóm câu; bảng/sơ đồ khó chuẩn hóa giữ bố cục ảnh gốc cùng ô đáp án tương tác.

`renderMode: "source"` cho biết nhóm câu đang dùng bố cục ảnh nguồn làm nội dung hiển thị chính. Các nhóm khác dùng chữ và lựa chọn tương tác đã hiệu đính. Bài đọc vẫn có ảnh gốc để đối chiếu. Không suy ra văn bản đúng chỉ vì OCR tạo đủ 40 số câu.

Để cập nhật ảnh sau khi thay đổi quy tắc crop mà không thay nội dung đã sửa:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_library.py refresh-images --book 13
```

Lệnh này chỉ đổi tham chiếu ảnh của JSON và override tương ứng, giữ chữ/đáp án/nhãn câu. Phải kiểm tra lại ảnh mới và cập nhật hash biên bản sau đó. Với Cambridge 20 Test 1, ảnh bổ sung từ bản 144 trang được giữ riêng vì bản 80 trang thiếu một mệnh đề ở đoạn cuối passage 3.

## Bằng chứng kiểm tra

Kiểm tra tự động và đối chiếu bằng mắt được lưu riêng; trạng thái `verified` chỉ đặt sau khi đã đối chiếu bài đọc, câu hỏi và khóa.

| Phạm vi | Biên bản chính |
| --- | --- |
| Cambridge 13–14 | `content-audit.json`, các mẫu visual review và full overrides |
| Cambridge 15 | `cam15-reading-review.json`, `cam15-editorial-review.json`, `cam15-questions-review.json` |
| Cambridge 17 | `cam17-review.json`, `cam17-questions-review.json` |
| Cambridge 18–19 | `cam18-reading-review.json`, `cam19-reading-review.json`, `cam18-19-questions-review.json` |
| Cambridge 20 | `pilot20-review.json`, `cam20-test2-review.json`, `cam20-test3-review.json`, `cam20-test4-review.json` |
| Toàn bộ khóa | `keys-report.json` và provenance trong từng khóa |
| Toàn bộ cấu trúc | `content-audit.json` |
| Danh mục và hash cuối | `library-verification.json` |
| Dựng lại đủ 32 đề giữ nguyên từng byte | `rebuild-verification.json` |

Ảnh nguồn có thể chứa dòng quảng bá của bản scan; chữ bài đọc chuẩn hóa đã loại các dòng này. Một số nội dung gây ngạc nhiên vẫn giữ đúng bản người dùng cung cấp, ví dụ WWFN/1990 trong Cambridge 19 Test 3 hoặc số 130 loài bướm trong Test 4. Các đính chính đối với lỗi của bản nguồn được ghi rõ ở biên bản tương ứng, không âm thầm sửa theo suy đoán.

## Bổ sung hoặc sửa một đề

1. Giữ PDF mới tại thư mục nguồn riêng và ghi hash. Với sách mới, bổ sung danh mục nguồn và vùng trang trong importer.
2. Trích xuất và dựng bản cơ sở; đề mới bắt đầu bằng `needs_review`.
3. Đối chiếu toàn bộ bài đọc và nhãn đoạn. Kiểm tra thứ tự cột, đầu/cuối trang, phụ đề và chú thích.
4. Đối chiếu đủ 40 vị trí câu, hướng dẫn, giới hạn từ/số, toàn bộ lựa chọn và bố cục bảng/sơ đồ. Xem trực tiếp từng ảnh crop được dùng trong giao diện.
5. Chép và kiểm tra khóa riêng; ghi biến thể được nguồn chấp nhận và nhóm nhiều đáp án theo tập hợp không lặp.
6. Lưu full override, tăng `version`, lập biên bản có trang nguồn/hash, rồi mới đặt `verified`. Chạy audit và kiểm tra bài trong app.

Mỗi lượt làm giữ phiên bản đề và khóa tại thời điểm tạo. Không sửa một phiên bản đã dùng mà giữ nguyên số phiên bản. **Không xóa ảnh chỉ vì thư viện hiện tại không còn tham chiếu**: các lượt làm cũ và bản sao lưu có thể vẫn cần chúng. Lệnh sau chỉ thống kê và không xóa:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_library.py asset-report
```

Khi chuyển app sang máy khác hoặc phục hồi dữ liệu học, giữ kèm `library/tests`, `library/keys`, toàn bộ `library/assets` và dữ liệu học. Nên giữ cả nguồn PDF, overrides và biên bản để có thể kiểm tra hay dựng lại về sau. Các PDF riêng không cần được tải lên dịch vụ bên ngoài để thực hiện quy trình này.


## Bố cục bảng và matching tương tác (bản 1.1)

`group.layout` bổ sung phần trình bày cho 6 bảng và 34 nhóm matching (5 heading, 29 ghép đoạn). Các field nội dung gốc, nguồn ảnh và khóa không bị thay đổi. `scripts/prepare_question_layouts.py` tạo metadata từ bản chép đã đối chiếu và ghi full overrides. Chạy `--check` để kiểm đủ vị trí câu, part index, ô gộp và fingerprint; chạy `scripts/verify_rebuild.py` để chứng minh assemble không làm mất metadata.

Table chứa hàng, ô, `rowSpan`/`colSpan`, chuỗi chữ và tham chiếu số câu; riêng Cambridge 15 Test 4 câu 7 có `part: 0` và `part: 1`. Không đánh số hai phần thành hai câu. Matrix giữ danh sách lựa chọn gốc và thêm các hàng câu dẫn phục vụ radio grid.

`library/presentation.json` chứa layout cùng SHA-256 của nhóm gốc (không gồm field layout). Khi mở lượt làm cũ, backend chỉ thêm layout nếu chưa có, hoặc nâng cấp layout đã có khi cả fingerprint nội dung và hash layout cũ nằm trong danh sách đã kiểm tra. Layout tự sửa hoặc nội dung khác được giữ nguyên. Backend không sửa snapshot/khóa/kết quả trên SQLite. Giữ registry này khi chuyển máy. Bài mới lưu metadata ngay trong snapshot nên backup mang theo bố cục của nó.

Mỗi lượt làm có thể lưu `answerParts` để giữ vị trí các ô còn trống; đáp án ghép trong `answers` vẫn là chuỗi dùng để chấm. Annotation mới phân biệt `kind: highlight` (level 1–3) và `kind: note`. Giao diện đọc được annotation cũ thiếu kind và ZIP cũ, không cần di trú phá hủy dữ liệu.


## Listening và Cambridge 16 — bản 2.0

Reading Cambridge 16 dùng cache `library/preparation/cam16`, bốn full overrides và báo cáo `cam16/reading-review.json`. Khóa Reading giữ riêng trong `library/keys`. Không dùng script khóa cũ ghi đè nội dung mới đã kiểm tra.

Listening dùng `library/listening/tests`, `keys`, `transcripts`, `audio-manifest.json`; 128 audio sao chép theo SHA-256 vào `library/audio`. Manifest ghi sách/test/Part, nguồn, thời lượng, start/end và bằng chứng đối chiếu. Bản trùng 15/17 và file macOS không nhập. Ba track Cambridge 17 Test 4 Part 2–4 bổ sung từ nguồn ứng viên được duyệt và so với audioscript nguồn.

Reading giữ `passages`; Listening dùng `parts` và cấu trúc nhóm câu chung. Layout table/flow/diagram chứa vị trí câu; giới hạn từ là số nguyên `wordLimit`, cho phép số bằng `allowNumber`. Khóa giữ các biến thể riêng. Không đưa khóa/transcript vào test public; API transcript chỉ mở sau chấm.

Bản hiệu đính cuối nằm trong `library/preparation/listening/overrides/{tests,keys,transcripts}`. Dựng lại bằng:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/rebuild_listening.py
.venv\Scripts\python.exe -X utf8 scripts/rebuild_listening.py --check
.venv\Scripts\python.exe -X utf8 scripts/audit_listening.py
```

Không chạy importer OCR cũ chồng lên bản đã hiệu đính. Các helper private prepare_listening_13_16.py, prepare_listening_17_20.py, finalize_listening.py chỉ lưu local vì chứa bản chép Cambridge. Sửa đề cần đối chiếu nguồn, thay override có chủ đích; không sửa snapshot lịch sử.

Bằng chứng audio ở `library/preparation/listening/cam*/`: mẫu đầu/cuối và timestamp ASR local. So với 16 scripts mỗi sách; không chỉ dựa tên file. 127/128 track có script đúng đạt điểm so khớp cao nhất; Cambridge 19 Test 1 Part 1 có ít lời trong mẫu nên bổ sung 115–175 giây, xác nhận Hinchingbrooke/69 hectares/stream. Chi tiết ở audio-content-comparison.json và final-review.json.

`scripts/verify_audio_timeline.py` là công cụ chuẩn bị tùy chọn dùng faster-whisper tiny.en CPU local, không gửi audio ra ngoài và không phải phụ thuộc runtime. Model nằm trong preparation. Timestamp giúp loại publisher/paper instructions và khoảng kiểm tra cuối Part 4 trước khi app cộng đúng 120 giây. Các khoảng đọc/kiểm tra giữa Parts giữ nguyên. Cambridge 14 Test 2 Part 4 có bài khác nối đuôi, bị loại bằng boundary; file gốc không sửa.

Nguồn thiếu/sai được ghi rõ: Cambridge 13 Test 3 PDF thiếu trang audioscript 109, đoạn thiếu khôi phục từ audio và có thông báo UI; Cambridge 20 Test 3 bản gõ lại thiếu map, dùng trang 46 PDF gốc khác; map có G dù ghi A–F; Cambridge 20 Test 4 khóa câu 12 trống, cặp B/C xác nhận qua audio/script. Không coi ASR là bản chép in chính thức.

Audit kiểm tra 32 đề/128 Parts/1.280 câu, SHA-256, ảnh/audio, native blanks, lựa chọn, canonical 40/40 và nhóm nhiều đáp án đảo thứ tự. Kiểm tra cấu trúc không thay thế đối chiếu nội dung; bằng chứng editorial lưu riêng trong preparation.


Lưu ý transcript: Cambridge 13 có nhiều dòng gạch chân bị OCR bỏ sót, nên bản chép dùng hỗ trợ nhận dạng audio local và có thể còn sai khác nhỏ về từ ngữ/tên riêng. Cambridge 20 Test 1 Part 1 có đoạn cuối thiếu trong PDF được khôi phục từ audio. App hiển thị thông báo tại các transcript này; khóa chấm và nội dung câu hỏi được giữ riêng.


## Metadata trình bày theo sách (presentationVersion 3)

Sau các importer và công cụ inline/matrix, chạy `scripts/prepare_book_layouts.py`; thêm `--check` để kiểm tra mà không ghi file. Công cụ giữ nguyên layout v3 đã duyệt, ghi đồng thời thư viện chạy app, full overrides và registry. Chạy lại `prepare_reading_inline.py --check`, `prepare_question_layouts.py --check`, `verify_rebuild.py` và `rebuild_listening.py --check` để kiểm tra khả năng dựng lại.

Field tùy chọn: table có `columnWidths`, `minWidthCh`, `variant` (`grid`, `boxed-notes`, `plain`), `cell.blocks`, `scope`; flow có `variant`, `frame`, `optionsPosition`; block có `role`, `depth`, `marker`, `align`, `labelEnd`, `anchors`, `offsets`; table/flow có `answerWidths`. `cell.content` vẫn được giữ cho importer và bản cũ. Khi tách block, anchor trỏ tới chuỗi cũ và offset cộng vị trí cắt, không đặt lại bằng 0. Không sửa chữ hoặc chèn lại số câu trong metadata mới.

Registry ghi `previousLayoutSha256`: chỉ thêm hash của layout cũ đã đối chiếu, cùng fingerprint nội dung gốc. Không tự đưa mọi snapshot hoặc layout tùy chỉnh vào danh sách. Không sửa snapshot SQLite để áp bố cục. Xem [biên bản](docs/BOOK_LAYOUT_REVIEW.md) và `library/preparation/book-layout-review.json`.
