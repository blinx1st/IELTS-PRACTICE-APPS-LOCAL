# Reading Room — IELTS Reading & Listening local

Ứng dụng luyện Cambridge **13–20** trên Windows, dùng offline cho một người học. Thư viện gồm **32 đề Reading, 32 đề Listening, 96 passages, 128 Parts và 2.560 câu hỏi**; Cambridge 16 đã được bổ sung.

Nhấp đúp **MO_UNG_DUNG.cmd** để mở app tại http://127.0.0.1:8765. Dùng **DUNG_UNG_DUNG.cmd** để dừng dịch vụ. Máy mới chạy **CAI_DAT_LAN_DAU.cmd** khi có Internet; sau thiết lập, việc học và chấm bài hoạt động offline. Xem [hướng dẫn sử dụng](HƯỚNG_DẪN.md).

- **Reading:** hai cột cuộn độc lập, thi 60 phút hoặc không hạn giờ, luyện passage, bảng điền trực tiếp và matching chọn tròn.
- **Listening:** thi sát thật, luyện cả đề hoặc từng Part. Audio local ghép theo sách/test/Part. Thi sát thật nghe một lần 1×, phát liên tiếp và có 2 phút kiểm tra cuối bài. Luyện tập có tốc độ 0,5–2×, tua ±5 giây, âm lượng và lặp A–B.
- Tự lưu đáp án, cờ, highlight vàng/cam/đỏ và Note riêng. Listening giữ checkpoint mỗi 2 giây; gặp sự cố dừng và chờ Resume, ghi nhận gián đoạn.
- Nộp bài khóa đáp án; chỉ **Chấm bài** mới hiện điểm và đáp án đúng. Listening mở transcript theo Part sau chấm. Thống kê/lịch sử tách theo kỹ năng; đủ 40 câu mới có band tham khảo.
- SQLite giữ phiên bản đề/khóa/audio/transcript theo lượt làm. ZIP v2 sao lưu cả audio được tham chiếu, đọc được ZIP cũ; giới hạn 2 GB ZIP và 4 GB tổng giải nén.

**Mã nguồn GitHub không kèm tài liệu Cambridge:** PDF, audio, đề, khóa, ảnh nguồn, dữ liệu học và script có bản chép nội dung được loại bằng `.gitignore`. Chúng vẫn nằm trên máy này. Khi chuyển máy, chép riêng **`library/`** rồi khôi phục ZIP lịch sử. Bộ cài không tự tải tài liệu Cambridge. Xem [GITHUB.md](GITHUB.md).

## Làm quen giao diện trước khi thi

Bản UI 2.1 có **Làm quen giao diện** trong thanh bên và hộp chọn chế độ. Bài thao tác thử không tính giờ, không chấm điểm và không ghi lịch sử. Màn hình thi có **Help**, **Display**, bộ lọc câu chưa làm/câu đánh dấu và bước xem lại trước nộp. Thanh audio hiển thị một nút Play/Pause theo trạng thái. Xem [báo cáo UI/UX](UI_UX_REVIEW.md).

## Phát triển và kiểm tra

React + TypeScript + Vite, Python FastAPI tại `127.0.0.1`, SQLite. Font Noto và biểu tượng Lucide đóng gói local; không CDN hoặc dịch vụ chấm bên ngoài.

```powershell
python -X utf8 scripts/setup.py
.venv\Scripts\python.exe -X utf8 -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -X utf8 -m pytest -q
.venv\Scripts\python.exe -X utf8 scripts/audit_library.py
.venv\Scripts\python.exe -X utf8 scripts/audit_listening.py
npm run test:ui
npm run build
npm audit --audit-level=moderate
```

Dữ liệu học: **`data/reading-room.sqlite3`**. Reading: `library/tests`, `library/keys`. Listening: `library/listening/tests`, `keys`, `transcripts`; audio: `library/audio`; manifest: `library/listening/audio-manifest.json`. Xem [DATA_PREPARATION.md](DATA_PREPARATION.md) để dựng lại nội dung đã hiệu đính và [TESTING.md](TESTING.md) để biết phạm vi nghiệm thu.

Một trang transcript Cambridge 13 Test 3 bị thiếu trong PDF nguồn đã được khôi phục từ audio; app thông báo tại transcript. Các đính chính tài liệu nguồn được ghi trong báo cáo chuẩn bị local. Band là tham khảo, ngưỡng thực tế có thể thay đổi theo đề.


Lưu ý transcript: Cambridge 13 có nhiều dòng gạch chân bị OCR bỏ sót, nên bản chép dùng hỗ trợ nhận dạng audio local và có thể còn sai khác nhỏ về từ ngữ/tên riêng. Cambridge 20 Test 1 Part 1 có đoạn cuối thiếu trong PDF được khôi phục từ audio. App hiển thị thông báo tại các transcript này; khóa chấm và nội dung câu hỏi được giữ riêng.
