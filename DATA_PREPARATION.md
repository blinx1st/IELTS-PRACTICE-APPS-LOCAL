# Chuẩn bị và kiểm tra thư viện Reading

Thư viện hiện có **28 đề, 84 bài đọc và 1.120 câu** của Cambridge 13, 14, 15, 17, 18, 19 và 20. Cambridge 16 chưa có PDF trong thư mục nguồn, vì vậy chưa được nhập. Tài liệu này dành cho việc bảo trì nội dung; sử dụng app hằng ngày không cần chạy OCR, tải mô hình hoặc kết nối Internet.

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
.\.venv\Scripts\python.exe scripts/prepare_library.py extract --book 13 14 15 17 18 19 20 --workers 4
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
| Dựng lại đủ 28 đề giữ nguyên từng byte | `rebuild-verification.json` |

Ảnh nguồn có thể chứa dòng quảng bá của bản scan; chữ bài đọc chuẩn hóa đã loại các dòng này. Một số nội dung gây ngạc nhiên vẫn giữ đúng bản người dùng cung cấp, ví dụ WWFN/1990 trong Cambridge 19 Test 3 hoặc số 130 loài bướm trong Test 4. Các đính chính đối với lỗi của bản nguồn được ghi rõ ở biên bản tương ứng, không âm thầm sửa theo suy đoán.

## Bổ sung hoặc sửa một đề

1. Giữ PDF mới tại thư mục nguồn riêng và ghi hash. Nếu thêm Cambridge 16, bổ sung danh mục nguồn và vùng trang của sách trong importer.
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

`library/presentation.json` chứa layout cùng SHA-256 của nhóm gốc (không gồm field layout). Khi mở lượt làm cũ, backend chỉ thêm layout vào dữ liệu trả cho giao diện nếu fingerprint khớp; không sửa snapshot/khóa/kết quả trên SQLite. Giữ registry này khi chuyển máy. Bài mới lưu metadata ngay trong snapshot nên backup mang theo bố cục của nó.

Mỗi lượt làm có thể lưu `answerParts` để giữ vị trí các ô còn trống; đáp án ghép trong `answers` vẫn là chuỗi dùng để chấm. Annotation mới phân biệt `kind: highlight` (level 1–3) và `kind: note`. Giao diện đọc được annotation cũ thiếu kind và ZIP cũ, không cần di trú phá hủy dữ liệu.
