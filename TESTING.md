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
