# Cải thiện UI/UX 2.1 — làm quen trước khi thi

## Cập nhật 22/10/2026

- Listening tự chia hai nửa cho nhóm câu hỏi rời dài; có Auto/1/2 cột, một vùng cuộn, thứ tự Tab theo số câu và ngưỡng rộng 1.100 px. Bảng, đoạn điền, flow-chart, sơ đồ và nhóm chọn nhiều giữ liền mạch.
- Reading đặt ô nhập/dropdown vào 82 nhóm văn bản (414 câu), giữ Source và bài đang làm. Các nhóm mới không còn ảnh kèm một dãy ô nhập riêng bên dưới.
- Highlight chọn trực tiếp vàng/cam/đỏ/xanh lá/xanh biển, thay màu đúng vùng giao nhau; Note riêng. Giữ màu và anchor của dữ liệu cũ, đồng bộ Help và bài làm quen.
- Logo mèo dùng cùng một asset local cho nhận diện và favicon. Hướng dẫn clone nay phù hợp thư viện được đóng gói trong GitHub.

Mục tiêu là giúp người học dùng thành thạo các thao tác thi trên máy: đọc và trả lời song song, theo dõi thời gian, đi đến từng câu, đánh dấu để quay lại và nộp bài có kiểm tra. Giữ màu xanh biển–trắng và các tiện ích ôn luyện đã có.

Đã đối chiếu với [IELTS Academic sample tests và practice experience](https://ielts.org/take-a-test/preparation-resources/sample-test-questions/academic-test) và [IDP familiarisation](https://ielts.idp.com/about/ielts-familiarisation-tests). Tài liệu chính thức cũng lưu ý thời gian, highlight và note trong bản làm quen có thể khác bài thi thực tế. App mô phỏng thao tác chính; không khẳng định giống từng pixel với mọi nền tảng tại điểm thi.

| Vấn đề tìm thấy | Thay đổi |
| --- | --- |
| Người mới phải đoán cách sử dụng cờ/footer/ghi chú | Thêm **Làm quen giao diện**: bốn thao tác thử có hướng dẫn, thêm Highlight/Note, Help, Display, xem bố cục Reading/Listening và âm thử tai nghe. Dùng chung bảng/matrix/footer với đề thật. |
| Thư viện dùng nhiều nhãn 8–11 px, phần giới thiệu đẩy đề xuống dưới | Tăng cỡ chữ và tương phản; rút gọn phần giới thiệu, chỉ hiện thẻ tiếp tục khi có bài dở. Đưa lời mời làm quen và cách chọn đề vào vị trí dễ thấy. |
| Người học khó tìm câu còn thiếu hoặc đã đánh dấu | Footer đủ 40 câu, chia theo Part, có tiến độ, bộ lọc All/Unanswered/For review, cờ riêng và nút trước/sau. Câu có đáp án xanh; câu hiện tại có viền rõ. |
| Thiếu hướng dẫn trong lúc làm bài | **Help** giải thích điều hướng, phím tắt, đáp án, highlight/note và thời gian/audio. Nêu rõ mở Help không dừng đồng hồ. |
| Cỡ chữ nhỏ hoặc tương phản không phù hợp | **Display** chọn 14–24 px, nền trắng/nền dịu/tương phản cao; lưu lựa chọn trong trình duyệt cho lượt tiếp theo. Reading dùng chữ sans serif, khoảng dòng rõ. |
| Nút nghe không thể hiện rõ đang phát/dừng | Gộp Play/Pause theo trạng thái. Giữ giới hạn điều khiển của thi sát thật; thêm xác nhận trước chuyển sang luyện tập. |
| Bấm lại kỹ năng đang chọn có thể làm mất danh sách đang hiển thị | Không tải lại khi chọn cùng kỹ năng; bỏ phản hồi cũ khi đổi kỹ năng nhanh. Ghi nhớ cuốn Cambridge gần nhất. |
| Nhảy câu đôi khi focus vào cờ thay vì ô trả lời | Ưu tiên ô nhập/select/radio; hỗ trợ Alt + ←/→ và điều hướng tab bằng mũi tên. |
| Nộp bài còn câu trống nhưng khó quay lại | Bước nộp cho chọn **Review unanswered** hoặc **Review flagged**; chỉ Submit answers mới khóa bài. |

## Dữ liệu và tương thích

Không sửa thư viện, khóa, cách chấm, snapshot hay SQLite. Bài làm quen là nội dung minh họa tự viết, chỉ có trạng thái trong phiên; không tạo lượt học hoặc điểm. Trình duyệt chỉ lưu tùy chọn hiển thị, cuốn sách gần nhất và trạng thái đã làm quen. Nội dung và lịch sử cũ vẫn dùng luồng API hiện có.

Không thêm gói runtime hoặc CDN. Help, bài làm quen và cài đặt hiển thị đều dùng được offline. Giữ nguyên highlight vàng/cam/đỏ, Note độc lập, Pause và các chế độ Reading/Listening.

## Kiểm tra

- Frontend: 20 kiểm thử gồm bộ lọc, số câu, cờ ngoài phạm vi, trước/sau ở biên, chuẩn hóa tùy chọn, bài làm quen, 40 nút câu và các kiểm thử table/matrix/highlight/Listening hiện có.
- Backend: 38 kiểm thử hồi quy đạt. TypeScript/Vite build đạt; npm audit không có lỗ hổng.
- Kiểm tra trình duyệt trên dữ liệu QA riêng: bốn thao tác làm quen, Highlight/Note độc lập, Help bằng bàn phím, Display lưu sang đề thật, Reading đủ 40 câu, lưu/tải lại và quay về câu trống trước nộp.
- Kích thước CSS 1280 × 720: không tràn toàn trang, 40 câu có trong footer; hai cột và từng bảng cuộn trong vùng riêng. Kiểm tra bổ sung ở 1024 × 576 cho thấy cần cuộn nội dung nhiều hơn; 1280 × 720 là kích thước khuyến nghị.
- Chưa kiểm tra trực tiếp Edge; trình duyệt kết nối của phiên này là Chrome.

Ảnh local: [Reading](docs/screenshots/ux-reading-1280x720.png), [Listening](docs/screenshots/ux-listening-1280x720.png), [làm quen](docs/screenshots/ux-familiarisation-1280x720.png).
