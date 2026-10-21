# Hướng dẫn Reading Room

## Mở và dừng app

Thư mục app hiện tại: `D:\Học Ielts\App luyện Ielts`.

1. Nhấp đúp **MO_UNG_DUNG.cmd**. Trình duyệt sẽ mở app tại `http://127.0.0.1:8765`. Nếu cổng đang bận, công cụ tự chọn một cổng từ 8766 đến 8775 và mở đúng địa chỉ đó.
2. Lần đầu trên máy mới, cần Internet để chuẩn bị Python, Node.js và các gói phụ thuộc. Có thể chạy **CAI_DAT_LAN_DAU.cmd** riêng. Công cụ cài Python còn thiếu bằng Windows App Installer và tải Node LTS từ nguồn chính thức nếu cần; Node được lưu riêng trong `.runtime`. Nếu máy không có Windows App Installer, làm theo thông báo để cài Python rồi chạy lại.
3. Sau cài đặt, việc làm bài, chấm, lịch sử và sao lưu không cần Internet.
4. Để dừng dịch vụ, nhấp đúp **DUNG_UNG_DUNG.cmd**. Đóng tab trình duyệt không dừng dịch vụ. Mở công cụ nhiều lần sẽ dùng lại dịch vụ của app đang chạy.

Không cần mở file `frontend/index.html` trực tiếp. Dùng Chrome hoặc Edge; giữ nguyên địa chỉ local khi tiếp tục bài để trình duyệt tìm đúng bản nháp.

## Chọn đề và làm bài

Thư viện có Cambridge **13, 14, 15, 17, 18, 19, 20**, mỗi sách bốn đề. Cambridge 16 hiện **Chưa có tài liệu**.

- **Thi thử 60 phút:** ba passages, 40 câu; mặc định khi bắt đầu. Không có Pause, đồng hồ tiếp tục chạy khi đóng tab hoặc dừng dịch vụ. Hết giờ tự nộp với đáp án được lưu trước hạn.
- **Thi thử không giới hạn:** chọn Không giới hạn trong hộp bắt đầu. Đồng hồ **TIME ELAPSED** đếm thời gian đã làm; có **Pause / Resume**. Pause dừng đồng hồ và che nội dung. Đóng tab không tự Pause. Bạn chủ động nộp bài khi xong; bài đủ 40 câu vẫn có band tham khảo.
- **Chuyển bài đang làm:** nút **Switch to untimed** chuyển bài thi 60 phút còn đang làm sang không hạn giờ, giữ đáp án, cờ, ghi chú và cả thời gian đã làm. Không chuyển ngược về 60 phút. Bài đã hết giờ hoặc đã nộp vẫn được khóa. Chuyển chế độ hoặc Pause cần dịch vụ local xác nhận thành công.
- **Luyện passage:** chọn một bài đọc. Mặc định 20 phút, có thể đặt 1–180 phút hoặc nhập **0** để không giới hạn. Bấm **Pause** trước khi nghỉ; thời gian dừng và nội dung được che. Đóng tab không tự tạm dừng.

Passage ở bên trái, câu hỏi ở bên phải. Hai phần cuộn riêng; kéo thanh giữa để đổi độ rộng. Thanh giữa cũng hỗ trợ phím mũi tên khi được focus. **A− / A+** đổi cỡ chữ; nút Fullscreen mở chế độ toàn màn hình.

Chọn đáp án bằng radio/dropdown/checkbox hoặc gõ vào ô trống. Nhóm chọn nhiều chỉ cho chọn đúng số lượng yêu cầu. Sáu nhóm Complete the table dùng bảng chữ với ô nhập ngay tại chỗ trống. Cambridge 15 Test 4 câu 7 có hai ô riêng quanh chữ “and”; điền mỗi ô một phần, không nhập lại chữ “and”. App tự ghép hai phần để chấm một câu và một điểm, đồng thời giữ được trường hợp một ô còn trống. Các nhóm summary, notes và sơ đồ chưa chuyển bố cục vẫn có ảnh nguồn và phần nhập như trước.

Heading và matching đoạn được trình bày thành bảng chọn tròn: mỗi hàng là một câu, cột là A–G hoặc số La Mã. Chọn một ô, hoặc bấm dấu × cạnh câu để xóa lựa chọn. Với heading, đọc danh sách phía trên bảng. Khi bảng hẹp, cuộn ngang ngay trong bảng; cột câu hỏi được giữ ở bên trái. Matching người, ghép câu và summary giữ cách trình bày trước đây.

Thanh dưới hiển thị câu đã làm, chưa làm và được đánh dấu. Số câu đã trả lời có nền xanh biển và chữ trắng đậm; viền đậm chỉ câu đang chọn. Bấm số câu để chuyển tới câu đó; **Alt + ← / →** chuyển câu trước/sau. Cờ cạnh mỗi câu giúp ghi nhớ câu cần xem lại.

## Highlight và ghi chú

Bôi chọn chữ rồi chọn **Highlight**. Lần đầu có màu **vàng**; phần chồng lần hai chuyển **cam**, lần ba trở đi **đỏ**. Chỉ phần giao nhau tăng màu, phần mới vẫn vàng. Để xóa màu, chọn vùng chữ rồi bấm **Clear highlight**; có thể xóa một phần mà không ảnh hưởng phần còn lại.

**Note** độc lập với highlight: chọn chữ rồi bấm Note để nhập ghi chú. Vùng có note được gạch chân xanh; bấm vào đó để xem, sửa hoặc xóa note. Highlight không mở hộp note, và xóa màu không xóa ghi chú. Nút **Notes** chỉ liệt kê ghi chú. Highlight/ghi chú cũ vẫn được đọc và giữ lại.

Chữ trong các bảng tương tác mới có thể bôi chọn. Chữ nằm trong ảnh nguồn hoặc sơ đồ chưa chuyển đổi không bôi chọn được; dùng **Source** để phóng xem trang gốc.

## Lưu bài và tiếp tục

App tự lưu sau khi nhập. **Saved on this device** nghĩa là dữ liệu đã được ghi vào SQLite trên ổ đĩa. Có thể tiếp tục từ thẻ đề hoặc **Lịch sử**.

Nếu dịch vụ bị dừng khi tab vẫn mở, app giữ đáp án mới trong bộ nhớ trình duyệt và hiện **Draft saved in browser**. Chạy lại **MO_UNG_DUNG.cmd**, giữ tab cũ mở; app sẽ thử đồng bộ lại sau vài giây. Tránh xóa dữ liệu trình duyệt khi vẫn còn bản nháp chưa đồng bộ.

Chỉ nên mở một tab cho mỗi lượt làm. Khi phát hiện hai tab cùng sửa, app giữ bản nháp và báo xung đột để tránh ghi đè. Bấm **Xuất bản nháp** để giữ lại các đáp án chưa đồng bộ trước khi mở lại bài từ Lịch sử; file JSON này là bản tham chiếu cá nhân, khác với ZIP sao lưu toàn bộ dữ liệu.

## Nộp, xem lại và chấm

1. Bấm **Finish test**, xem số câu còn trống, rồi **Submit answers**.
2. Bài được khóa chỉnh sửa. Trước tiên app hiển thị nguyên đáp án bạn đã điền; đáp án đúng và điểm chưa xuất hiện.
3. Bấm **Chấm bài** khi đã sẵn sàng. App hiện đúng/sai/bỏ trống từng câu, thống kê theo passage và dạng câu hỏi. Bấm một dòng kết quả để quay về câu tương ứng.

Chấm điểm bỏ qua hoa/thường và khoảng trắng thừa, chấp nhận các biến thể đã ghi trong khóa đáp án; vẫn yêu cầu đúng chính tả và giới hạn từ. Nhóm chọn nhiều không xét thứ tự và không cộng điểm lặp một lựa chọn.

Chỉ bài đủ 40 câu có **band tham khảo**. Thang điểm này không phải điểm IELTS chính thức; ngưỡng thực tế có thể thay đổi theo đề. Bài luyện một passage hiển thị số câu đúng, không suy ra band. Cấu trúc 60 phút/40 câu theo [IELTS Academic Reading](https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-reading); cách diễn giải điểm theo [IELTS scoring](https://ielts.org/take-a-test/your-results/ielts-scoring-in-detail).

## Sao lưu và khôi phục

Mở **Sao lưu → Xuất dữ liệu** để tải ZIP. Tệp chứa toàn bộ lượt làm, ghi chú, highlight, đề/đáp án của từng phiên bản và ảnh được các lượt làm tham chiếu. Nên xuất định kỳ và giữ bản sao ngoài thư mục app.

Để phục hồi, chọn **Khôi phục bản sao lưu → Chọn tệp ZIP**. App ghép các lượt làm, giữ lại bản trên máy nếu bản đó mới hơn. Không cần xóa lịch sử trước khi khôi phục.

Để chuyển toàn bộ app sang máy khác, chép mã nguồn và thư mục `library`, chạy thiết lập lần đầu trên máy mới, rồi khôi phục ZIP. Không cần chép `node_modules` hoặc `.venv`. Các lượt thi thử đang chạy vẫn giữ hạn nộp ban đầu sau khôi phục.

Nếu sao chép trực tiếp SQLite thay cho ZIP, hãy dừng app trước và chép cả thư mục `data`; không chỉ chép riêng `.sqlite3` khi dịch vụ đang chạy vì còn tệp WAL.

## Tài liệu và xử lý sự cố

Nút **Source** dùng ảnh đã lưu local, số trang là thứ tự trang trong PDF. Thư viện đã được đối chiếu với bản PDF cung cấp; các sửa OCR và trường hợp nguồn thiếu/sai được ghi trong `library/preparation/`. Sáu bảng điền từ đã chuyển sang bố cục tương tác; ảnh gốc vẫn giữ trong Source để đối chiếu. Cách thêm Cambridge 16 hoặc sửa đề: [DATA_PREPARATION.md](DATA_PREPARATION.md). Đề sửa sau này không âm thầm đổi bài làm cũ.

- **Trình duyệt không mở:** chạy lại MO_UNG_DUNG; đọc địa chỉ được in trong cửa sổ. Xem `data/server.log` nếu dịch vụ không khởi động.
- **Thiếu gói hoặc giao diện:** chạy CAI_DAT_LAN_DAU khi có Internet.
- **App báo chưa kết nối local:** chạy MO_UNG_DUNG và chờ đồng bộ. Đồng hồ thi thử vẫn tiếp tục.
- **Lỗi in nguồn:** Cambridge 15 Test 4 phần summary 27–31 ghi A–J nhưng bản PDF chỉ liệt kê A–I; app giữ chín lựa chọn thực tế. Một số lỗi bản Cambridge 20 được đối chiếu thêm và ghi trong báo cáo chuẩn bị dữ liệu.

Đây là công cụ tự học cá nhân, chưa có giải thích tiếng Việt cho từng câu và chưa mô phỏng các phần Listening/Writing/Speaking.
