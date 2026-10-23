# UI/UX 2.1 — làm quen và điều hướng

## Cập nhật 22/10/2026 — inline, năm màu và hai cột

- Frontend: **25 kiểm thử qua**, gồm toàn bộ 82 nhóm Reading/414 ô, 17 nhóm dropdown ngân hàng từ, thứ tự hai cột chẵn/lẻ, matching có danh sách dùng chung, khóa sau nộp và dữ liệu highlight cũ/mới.
- Backend: **41 kiểm thử qua**, bao gồm năm màu/Note qua lưu và khôi phục ZIP, cùng kiểm tra thư viện chạy không cần cache. Build TypeScript/Vite và `npm audit --audit-level=moderate` thành công, không có lỗ hổng được báo cáo.
- Audit Reading: 32 đề, 96 passages, 1.280 câu, 0 lỗi/cảnh báo. Audit Listening: 32 đề, 128 Parts, 1.280 câu, 128 audio duy nhất, SHA-256 và tài nguyên hợp lệ. Kiểm tra 45 bảng/matrix và 82 nhóm inline đều qua.
- Chrome: thử câu 2 Stonehenge tại vị trí trống, dropdown tại câu 24, màu xanh biển qua tải lại, Listening chọn đáp án/cờ, đổi bố cục và fallback một cột ở chiều rộng CSS 1.000 px. Thử ở 1280 × 720; có đủ 40 nút footer và không tràn ngang toàn trang. Edge chưa được kiểm tra bằng trình duyệt riêng trong phiên này.
- Ảnh cập nhật: [Reading](docs/screenshots/reading-inline-1280.png), [Listening](docs/screenshots/listening-columns-1280.png). Các kết quả nghiệm thu cũ bên dưới được giữ làm lịch sử, không mô tả phiên bản mới.
- Bản sao đóng gói gồm 2.333 file / khoảng 1.037 MiB tại thời điểm kiểm tra, không PDF nguồn, mô hình hoặc cache OCR. Tạo mới `.venv`, chạy bộ cài, `npm ci` và build thành công. Với kết nối ngoài bị chặn trong tiến trình kiểm thử, cả Reading và Listening đều chọn đề → lưu/tải lại → nộp → chấm được; audio HTTP Range, transcript sau chấm và xuất ZIP khoảng 20 MB đều qua. Không đổi cấu hình mạng Windows.

20 kiểm thử frontend và 38 backend đạt; build và npm audit đạt. Các kiểm thử mới phủ lọc câu trống/cờ theo đúng phạm vi, số thứ tự không đổi, trước/sau ở biên, 40 nút câu, cỡ chữ/độ tương phản và bài mẫu không điểm. Kiểm tra bằng Chrome trên kho QA riêng; không tạo lượt QA trong dữ liệu học chính. Chi tiết, nguồn tham khảo và ảnh tại [UI_UX_REVIEW.md](UI_UX_REVIEW.md).

---

# Kiểm tra bản 2.0 — Reading và Listening Cambridge 13–20

- **38 kiểm thử backend và 16 kiểm thử frontend đạt**. Build TypeScript/Vite thành công; npm audit: 0 lỗ hổng. Frontend kiểm tra tất cả 127 nhóm Listening có flow/table/diagram hoặc matching, đủ ô theo số câu, khóa sau nộp và không có kết quả trước chấm.
- Reading: **32 đề / 96 passages / 1.280 câu / 0 lỗi / 0 cảnh báo**, gồm 4 đề Cambridge 16. Dựng lại 32 full overrides giữ nguyên byte. Reading có 7 bảng, 38 matrix (7 heading, 31 matching đoạn).
- Listening: **32 đề / 128 Parts / 1.280 câu / 128 audio hash duy nhất / 0 lỗi cấu trúc**. 75 nhóm completion gồm 11 table và 64 flow; 10 diagram, 52 matching, 48 choice, 63 multi. Canonical và đảo thứ tự nhóm multi chấm đủ 40/40. Audio đối chiếu mẫu nội dung và timeline; bằng chứng nằm riêng trong preparation.
- **160 luồng API offline** (32 đề × cả đề và 4 Parts) tạo → lưu đáp án chuẩn → nộp → chấm → transcript đạt; đủ đề có band, Part không có band. Chặn kết nối socket ngoài trong tiến trình kiểm tra. Không thay đổi cấu hình Internet Windows.
- Test backend: lease hai tab; heartbeat/revision độc lập; freeze checkpoint khi quá hạn; tải lại; đổi chế độ; loại Pause/tua/tốc độ khi thi; phát 4 Parts và 120 giây; chuyển luyện trong lúc kiểm tra cuối; lặp A–B mới; Range206; thiếu audio khóa đề; transcript/khóa ẩn trước chấm; backup cũ/mới.
- Chrome: phát audio 1,5×, điền/cờ, Pause che nội dung, reload giữ vị trí và tốc độ, Resume đúng mốc. Nộp khóa ô; chấm kết quả1/40 phân biệt đúng/sai/trống; transcript có player nghe lại trong cửa sổ. Map Cambridge20T3 có ô chọn trên hình; không tràn trang. CSS viewport đo trực tiếp 1280×720, footer đủ40 câu. Có kiểm tra bổ sung ở1600×900.
- Bộ dữ liệu QA riêng rút mỗi track còn2 giây: tự nối đủ4 tracks1×, không tua/Pause/speed, vào120 giây kiểm tra và tự nộp trên trình duyệt. Đã sửa lỗi coi buffering bình thường lúc đổi track là sự cố.
- Dừng/mở dịch vụ khi đang nghe: audio dừng, giữ mốc38,248s; Resume tiếp tục đúng mốc, nhãn Đã gián đoạn(1). Không bỏ qua đoạn audio khi lỗi. Hai tab bị chặn bằng lease trong kiểm thử backend.
- ZIP thực tế **18.967.979 byte**, 4 audio: khôi phục đủ4 lượt QA; xác nhận SHA-256, transcript và player dừng. ZIP cũ khôi phục đủ4 lượt. Giới hạn2 GB / 4 GB kiểm tra ở mã và test giới hạn; chưa tạo file2 GB thực tế.
- Hai lượt học thật trước cập nhật **giữ nguyên toàn bộ payload từng byte**, gồm snapshot/khóa/đáp án/highlight. Dữ liệu QA ởtmp, không ghi vào lịch sử chính. SQLitebackup trước cập nhật: data/pre-listening-upgrade.sqlite3.

Giới hạn kiểm tra: trình duyệt kết nối hiện có là Chrome; chưa chạy trực tiếp Edge. Luồng offline dùng ASGI chặn socket ngoài và tài nguyên local, không rút mạng vật lý Windows. Transcript Cambridge13 và đoạn thiếu20T1 được khôi phục có hỗ trợ ASR, có thông báo chất lượng; không xác nhận bản chép in nguyên văn từng từ. Ảnh và bằng chứng nguồn giữ local, không lênGitHub.

Ảnh: [Listening](docs/screenshots/listening-1280x720.png), [bản đồ](docs/screenshots/listening-map.png).

---

# Kiểm tra bản 1.1 — giao diện xanh biển và bố cục tương tác

- Build TypeScript/Vite thành công. **28 kiểm thử backend và 11 kiểm thử frontend đạt** (`pytest -q`, `npm run test:ui`). Frontend dùng bộ chạy test có sẵn của Node và Vite SSR, không thêm phụ thuộc runtime.
- Audit thư viện: 28 đề / 84 passages / 1.120 câu / 0 lỗi / 0 cảnh báo. Kiểm tra layout: **6 bảng, 5 heading matrix, 29 paragraph matrix; 40 nhóm, 0 lỗi**. Dựng lại đủ 28 đề giữ nguyên từng byte và overrides.
- Các test frontend phủ đủ 36 ô nhập của 35 câu table, 34 matrix cùng lựa chọn, khóa sau nộp, không lộ đáp án trước chấm, thứ tự hai ô của một câu, mức highlight/giao một phần/xóa một phần/nhiều anchor/đọc annotation cũ. Một câu hai ô vẫn chấm đúng một điểm.
- Test backend bổ sung full exam không hạn giờ, đồng hồ tích lũy, Pause/Resume, tiếp tục khi mở lại, chuyển timed→untimed giữ bài và không đặt lại thời gian, từ chối bài đã hết hạn/nộp, backup thời gian và annotation mới, overlay bố cục không sửa snapshot.
- Trên Chrome tại **1280 × 720**: footer đủ 40 số, số đã trả lời có nền xanh và chữ trắng đậm; bảng nhập trực tiếp; heading/paragraph radio grid chọn, xóa và chọn cùng cột độc lập; bảng hẹp cuộn ngang nhưng giữ cột câu hỏi, không tràn trang. Thử bằng bàn phím cả điều hướng và chỉnh độ rộng hai cột.
- Đã thử thực tế highlight vàng/cam/đỏ theo vùng giao nhau, Note riêng có gạch chân, click highlight không mở note, Clear highlight không xóa note; lưu/tải lại giữ nguyên. Pause che nội dung, tải lại vẫn dừng đồng hồ, Resume tiếp tục.
- Cambridge 15 Test 4 Q7: chỉ điền ô thứ hai rồi tải lại vẫn giữ ô đầu trống; ngắt dịch vụ và điền ô đầu, bản nháp lưu trên trình duyệt; mở dịch vụ tự đồng bộ cả hai ô. Chấm `leaves bark` được 1/13 khi những câu khác bỏ trống.
- ZIP thực tế mới: **3 lượt làm, 45 ảnh** khôi phục vào kho riêng và giữ đầy đủ đáp án/answerParts/annotations/examTiming/elapsed. ZIP cũ khôi phục đủ 4 lượt. Toàn bộ kiểm thử trình duyệt dùng dữ liệu riêng tại `tmp/ui-upgrade-qa`, không ghi các lượt QA vào lịch sử học chính.
- Đã đối chiếu lượt học thật với bản trước cập nhật: **snapshot đề/khóa, đáp án và highlight giữ nguyên**. Table và heading của lượt Cambridge 13 Test 1 khớp fingerprint nên có thể nhận bố cục mới mà không sửa snapshot. Bài cũ không tự chuyển thời gian; hết hạn vẫn theo quy tắc nộp ban đầu.

Ảnh giao diện: [bảng trực tiếp và highlight](docs/screenshots/blue-table.png), [matching chọn tròn](docs/screenshots/blue-matrix.png).

## Kiểm tra bản bàn giao ban đầu — 21/10/2026

## Kết quả

- `npm run build`: thành công, TypeScript và Vite tạo bundle local.
- `.venv\Scripts\python.exe -X utf8 -m pytest -q`: **22 passed**. Có một cảnh báo deprecation từ lớp TestClient/httpx; không ảnh hưởng app chạy bằng Uvicorn.
- `python -X utf8 scripts/audit_library.py`: **28 đề, 84 passages, 1.120 câu, 237 nhóm, 417 tham chiếu ảnh; 0 lỗi, 0 cảnh báo**. Toàn bộ đề đã `verified`. Các khóa chuẩn đều chấm 40/40, nhóm chọn nhiều không phụ thuộc thứ tự.
- `python -X utf8 scripts/verify_rebuild.py`: dựng lại đủ 28 đề không thay đổi byte nào; 28 overrides khớp hoàn toàn.

## Phạm vi kiểm thử tự động

Chuẩn hóa đáp án, giới hạn từ, biến thể, bảy dạng câu, chọn nhiều một phần/đảo thứ tự/trùng lựa chọn, các mốc band, thống kê passage, lưu/đọc lại đáp án và ghi chú, ẩn khóa trước chấm, khóa bài sau nộp, giữ nguyên phiên bản đề/khóa, xung đột revision, hết giờ và mở lại, pause/resume, luyện không giới hạn, chỉ chấm passage đã chọn, đề chưa verified, kiểm tra Origin, ZIP sao lưu/khôi phục/ghép bản mới hơn/ảnh/path traversal.

Luồng API chọn đề → làm → nộp → chấm → thống kê → sao lưu được chạy với kết nối mạng ngoài bị chặn trong tiến trình kiểm thử. Giao diện dùng font, biểu tượng và ảnh trên máy; không có CDN. Không thay đổi cấu hình mạng của Windows.

## Kiểm tra trên Chrome của máy hiện tại

- Làm bài hai cột, cuộn riêng, đổi độ rộng, font, highlight, ghi chú, cờ và khôi phục sau tải lại.
- Practice với thời lượng 20 phút và không giới hạn; Pause che nội dung, tải lại vẫn giữ trạng thái/ghi chú.
- Thi thử 60 phút, đủ 40 nút điều hướng. Giao diện được kiểm tra tại viewport CSS **1280 × 720**, footer và hai cột nằm trong khung hình. Ảnh phần app: [exam-1280x720.png](docs/screenshots/exam-1280x720.png).
- Footer câu thứ hai của nhóm chọn nhiều cuộn đến đúng nhóm; matching có câu dẫn và danh sách lựa chọn đọc được.
- Dừng dịch vụ bằng công cụ Windows, nhập đáp án trong tab cũ: hiện **Draft saved in browser**. Mở lại dịch vụ: tự trở về **Saved on this device**, hết thông báo lỗi; tải lại vẫn có đáp án và cờ.
- Nộp bài khóa điều khiển và chưa hiện feedback đúng/sai; bấm **Chấm bài** mới hiện đáp án, thống kê theo passage/dạng câu. Bài passage không có band. Hai lựa chọn D rồi C vẫn được chấm đúng cả hai.
- `DUNG_UNG_DUNG.cmd` và `MO_UNG_DUNG.cmd` chạy thành công tại đường dẫn có dấu/khoảng trắng. Khởi động lặp dùng lại dịch vụ. Bộ kiểm tra bootstrap tìm được Python và Node trên máy; nhánh tải/cài thành phần thiếu không cần chạy trên máy đã có đủ phụ thuộc.

ZIP thực tế đã được khôi phục vào một kho kiểm thử riêng: **3 lượt làm, 34 ảnh**, SHA-256 ảnh khớp, đáp án và ghi chú giữ nguyên. API xuất ZIP trả thành công. Thao tác chọn file/tải file của công cụ tự động Chrome bị giới hạn bởi quyền truy cập file của extension, nên phần trao đổi file thực tế được nghiệm thu trực tiếp qua API; không thay đổi quyền extension.

Bốn lượt làm do quá trình kiểm thử tạo đã chuyển vào `data/qa-archive-2026-10-21.zip` để không lẫn với tiến độ học. Có thể khôi phục ZIP này qua chức năng Sao lưu nếu cần xem lại dữ liệu kiểm thử. Các lượt này giữ nguyên nội dung đề/khóa tại thời điểm tạo.

Cambridge 16 chưa có nguồn, đúng phạm vi bản đầu. Band là tham khảo; một số bảng/sơ đồ dùng ảnh nguồn với ô đáp án riêng. Các lỗi trong bản gõ lại Cambridge 20 và typo A–J ở Cambridge 15 Test 4 được ghi trong báo cáo chuẩn bị dữ liệu.


## Bố cục theo sách — 22/10/2026

Đã bổ sung kiểm thử đủ 18 bảng và 146 nhóm văn bản: thứ tự ô, độ rộng theo giới hạn từ, hai ô/một câu, phân cấp Stonehenge, ngân hàng từ sau summary, khóa sau nộp và highlight/Note trên anchor cũ. Backend kiểm tra nâng cấp layout cũ chỉ khi khớp cả nội dung và hash layout. Kết quả: 45 backend, 30 frontend; build, npm audit và audit thư viện đạt. Xem [phạm vi kiểm tra trực tiếp và ảnh trước/sau](docs/BOOK_LAYOUT_REVIEW.md).


## Bản clone và cập nhật — 24/10/2026

50 kiểm thử backend, 30 frontend và build đạt. Đã cài dependencies/build mới trong một bản clone riêng của commit 08041f8; không sử dụng `.venv`, `node_modules`, `dist` hay SQLite của máy gốc. Bản sửa được áp vào clone và kiểm tra lại với launcher thật, Chrome, dropdown Cambridge 13 Test 4, giữ đáp án sau tải lại, logo và API audio Range. Công cụ fingerprint có kiểm thử khác biệt CRLF/LF giữa Git checkout, dist cũ, logo cũ, bundle thiếu và backend cũ. Xem [biên bản và giới hạn kết luận](docs/GITHUB_CLONE_AUDIT.md).
