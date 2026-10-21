# Reading Room — IELTS Academic Reading local

Ứng dụng luyện Reading Cambridge cho một người học trên Windows. React + TypeScript + Vite, FastAPI, SQLite. Giao diện, đề, ảnh nguồn, font và biểu tượng chạy trên máy, không cần tài khoản hay Internet khi sử dụng.

**Bắt đầu:** nhấp đúp `MO_UNG_DUNG.cmd`. App mở ở địa chỉ local, thường là http://127.0.0.1:8765. Dùng `DUNG_UNG_DUNG.cmd` khi muốn dừng dịch vụ. Hướng dẫn chi tiết: [HƯỚNG_DẪN.md](HƯỚNG_DẪN.md).

**Bản mã nguồn trên GitHub:** không kèm PDF, thư viện Cambridge, ảnh đề, dữ liệu học và các script chứa bản chép câu hỏi/đáp án. Các file này vẫn được giữ trên máy hiện tại và được loại trừ bằng `.gitignore`. Khi chuyển sang máy khác, chép riêng thư mục `library/` của bạn vào cùng cấp với `backend/` để có đề làm bài; chuyển lịch sử bằng chức năng xuất/khôi phục ZIP. Cài đặt lần đầu chỉ cài phần mềm, không tự tải thư viện đề. Các bước đưa mã nguồn lên GitHub: [GITHUB.md](GITHUB.md).

Thư viện: Cambridge 13–15 và 17–20, gồm **28 đề, 84 passages, 1.120 câu**. Cambridge 16 chờ PDF. Nội dung được chuẩn bị từ tài liệu người dùng cung cấp; chỉ đề đã đối chiếu mới được mở làm bài. Ảnh gốc đi kèm từng passage/nhóm câu để tra lại. Sáu bảng Complete the table có ô nhập trực tiếp; 34 nhóm heading/matching đoạn dùng bảng chọn tròn. Thi thử hỗ trợ 60 phút hoặc không giới hạn có Pause; highlight vàng/cam/đỏ độc lập với Note.

## Phát triển

```powershell
python -X utf8 scripts/setup.py
.venv\Scripts\python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
# Terminal khác, nếu cần giao diện có hot reload:
npm run dev
```

```powershell
.venv\Scripts\python.exe -X utf8 -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -X utf8 -m pytest -q
python -X utf8 scripts/audit_library.py
npm run build
npm run test:ui
python -X utf8 scripts/prepare_question_layouts.py --check
```

`frontend/` chứa giao diện; `backend/` chứa API/chấm điểm; `library/tests/` chứa đề; `library/keys/` chứa khóa đáp án riêng; `library/assets/` chứa ảnh nguồn; `library/preparation/` lưu nguồn gốc và kết quả đối chiếu. Quy trình nhập lại/bổ sung sách: [DATA_PREPARATION.md](DATA_PREPARATION.md).

Dữ liệu học nằm trong `data/reading-room.sqlite3`. Mỗi lượt làm lưu bản chụp đề và đáp án riêng, nên chỉnh thư viện không đổi kết quả cũ. Xuất/khôi phục ZIP tại **Sao lưu**; ZIP chứa lịch sử, nội dung gắn với lượt làm và ảnh tham chiếu. Dịch vụ chỉ lắng nghe tại `127.0.0.1`.

Font Noto Sans và Noto Serif được đóng gói kèm giấy phép SIL OFL trong `frontend/public/fonts/`. Biểu tượng Lucide nằm trong bundle. Không dùng CDN hoặc gọi dịch vụ chấm điểm bên ngoài.
