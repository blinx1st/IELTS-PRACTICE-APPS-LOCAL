# Hướng dẫn Reading Room

## Mở và dừng app

Thư mục app hiện tại: `D:\Học Ielts\App luyện Ielts`.

1. Nhấp đúp **MO_UNG_DUNG.cmd**. Trình duyệt sẽ mở app tại `http://127.0.0.1:8765`. Nếu cổng đang bận, công cụ tự chọn một cổng từ 8766 đến 8775 và mở đúng địa chỉ đó.
2. Lần đầu trên máy mới, cần Internet để chuẩn bị Python, Node.js và các gói phụ thuộc. Có thể chạy **CAI_DAT_LAN_DAU.cmd** riêng. Công cụ cài Python còn thiếu bằng Windows App Installer và tải Node LTS từ nguồn chính thức nếu cần; Node được lưu riêng trong `.runtime`. Nếu máy không có Windows App Installer, làm theo thông báo để cài Python rồi chạy lại.
3. Sau cài đặt, việc làm bài, chấm, lịch sử và sao lưu không cần Internet.
4. Để dừng dịch vụ, nhấp đúp **DUNG_UNG_DUNG.cmd**. Đóng tab trình duyệt không dừng dịch vụ. Mở công cụ nhiều lần sẽ dùng lại dịch vụ của app đang chạy.

Không cần mở file `frontend/index.html` trực tiếp. Dùng Chrome hoặc Edge; giữ nguyên địa chỉ local khi tiếp tục bài để trình duyệt tìm đúng bản nháp.

## Làm quen giao diện — nên thử trước lượt thi đầu tiên

Bấm **Làm quen giao diện** ở thanh bên, hoặc trong hộp chọn chế độ trước khi bắt đầu. Bài mẫu gồm bốn thao tác: nhập một từ vào bảng, chọn đáp án, cắm cờ và chuyển Part để matching. Có thể thử Highlight, Note, đọc Help và đổi Display. Chọn Reading/Listening để xem bố cục; âm trong phần Sound check chỉ là âm thử tai nghe.

Bài này không tính giờ, không chấm điểm và không tạo lượt trong lịch sử. **Finish practice → Tôi đã sẵn sàng** hoàn thành hướng dẫn; có thể làm quen lại bất kỳ lúc nào.

Trong đề Cambridge, **Display** chỉnh cỡ chữ 14–24 px và nền trắng/nền dịu/tương phản cao. App nhớ tùy chọn trên trình duyệt. **Help** giải thích thao tác và phím tắt; mở Help hoặc Display **không dừng đồng hồ** của bài đang chạy.

Footer mới có **All questions**, **Unanswered**, **For review**. Số nền xanh đã có đáp án; cờ vàng đánh dấu cần xem lại, không phải kết quả đúng/sai. Mũi tên trước/sau đi qua các câu trong bộ lọc đang chọn. **Alt + ←/→** đi câu trước/sau trong toàn bài. Chọn All questions để hiện lại đủ câu. Nút Part ở footer và tab Passage/Part phía trên đều chuyển trang câu hỏi.

Trước nộp, **Review unanswered** quay về câu trống đầu tiên; **Review flagged** quay về câu đánh dấu đầu tiên. Bài chỉ bị khóa sau **Submit answers**. Khi đang nghe luyện tập, nút audio đổi giữa **Play / Resume** và **Pause** theo trạng thái; khi Pause, dùng **Resume** ở vùng che nội dung để nghe tiếp. Chuyển từ thi có giới hạn sang luyện tập có hộp xác nhận, giữ bài làm.

## Chọn đề và làm bài

Thư viện có Cambridge **13–20**, mỗi sách bốn đề Reading và bốn đề Listening. Chọn kỹ năng bằng nút Reading / Listening phía trên thư viện. Lịch sử và tiến độ lọc theo kỹ năng đang chọn. Cambridge 16 đã đủ tài liệu.

- **Thi thử 60 phút:** ba passages, 40 câu; mặc định khi bắt đầu. Không có Pause, đồng hồ tiếp tục chạy khi đóng tab hoặc dừng dịch vụ. Hết giờ tự nộp với đáp án được lưu trước hạn.
- **Thi thử không giới hạn:** chọn Không giới hạn trong hộp bắt đầu. Đồng hồ **TIME ELAPSED** đếm thời gian đã làm; có **Pause / Resume**. Pause dừng đồng hồ và che nội dung. Đóng tab không tự Pause. Bạn chủ động nộp bài khi xong; bài đủ 40 câu vẫn có band tham khảo.
- **Chuyển bài đang làm:** nút **Switch to untimed** chuyển bài thi 60 phút còn đang làm sang không hạn giờ, giữ đáp án, cờ, ghi chú và cả thời gian đã làm. Không chuyển ngược về 60 phút. Bài đã hết giờ hoặc đã nộp vẫn được khóa. Chuyển chế độ hoặc Pause cần dịch vụ local xác nhận thành công.
- **Luyện passage:** chọn một bài đọc. Mặc định 20 phút, có thể đặt 1–180 phút hoặc nhập **0** để không giới hạn. Bấm **Pause** trước khi nghỉ; thời gian dừng và nội dung được che. Đóng tab không tự tạm dừng.

Passage ở bên trái, câu hỏi ở bên phải. Hai phần cuộn riêng; kéo thanh giữa để đổi độ rộng. Thanh giữa cũng hỗ trợ phím mũi tên khi được focus. **A− / A+** đổi cỡ chữ; nút Fullscreen mở chế độ toàn màn hình.

Chọn đáp án bằng radio/dropdown/checkbox hoặc gõ vào ô trống. Nhóm chọn nhiều chỉ cho chọn đúng số lượng yêu cầu. Bảy nhóm Reading Complete the table dùng bảng chữ với ô nhập ngay tại chỗ trống. Cambridge 15 Test 4 câu 7 có hai ô riêng quanh chữ “and”; điền mỗi ô một phần, không nhập lại chữ “and”. App tự ghép hai phần để chấm một câu và một điểm, đồng thời giữ được trường hợp một ô còn trống. Các nhóm summary, notes và sơ đồ chưa chuyển bố cục vẫn có ảnh nguồn và phần nhập như trước.

Heading và matching đoạn được trình bày thành bảng chọn tròn: mỗi hàng là một câu, cột là A–G hoặc số La Mã. Chọn một ô, hoặc bấm dấu × cạnh câu để xóa lựa chọn. Với heading, đọc danh sách phía trên bảng. Khi bảng hẹp, cuộn ngang ngay trong bảng; cột câu hỏi được giữ ở bên trái. Matching người, ghép câu và summary giữ cách trình bày trước đây.

Thanh dưới hiển thị câu đã làm, chưa làm và được đánh dấu. Số câu đã trả lời có nền xanh biển và chữ trắng đậm; viền đậm chỉ câu đang chọn. Bấm số câu để chuyển tới câu đó; **Alt + ← / →** chuyển câu trước/sau. Cờ cạnh mỗi câu giúp ghi nhớ câu cần xem lại.

## Listening: nghe và làm bài

Chọn Listening → sách → Làm bài. Có ba chế độ:

| Chế độ | Cách hoạt động |
| --- | --- |
| Thi sát thật | 40 câu; sau Test sound và Start listening, audio chạy 1× lần lượt 4 Parts, không tua/Pause thủ công. Cuối bài có đúng 2 phút kiểm tra rồi tự nộp. |
| Luyện cả đề | 40 câu, đồng hồ đếm lên, tự nộp. Đổi Part dừng track cũ và mở track của Part mới. |
| Luyện từng Part | Chọn một Part, 10 câu, đồng hồ đếm lên, chấm riêng và không quy đổi band. |

Trong luyện tập, dùng Play / Resume, Pause audio, thanh tua, ±5s, âm lượng và tốc độ **0,5; 0,75; 1; 1,25; 1,5; 1,75; 2×**. Đổi tốc độ giữ cao độ giọng. Đặt **A** ở đầu đoạn, **B** ở cuối để lặp; nút mũi tên vòng xóa vòng lặp. Pause dừng audio, đồng hồ và che câu hỏi. Thi sát thật có **Switch to practice**, chuyển một chiều và giữ đáp án.

Trong thi sát thật, chọn Part câu hỏi chỉ đổi trang, audio vẫn chạy liên tục. Đồng hồ lấy từ các đoạn audio đã kiểm tra cộng 120 giây; khoảng kiểm tra cuối trong recording và lời hướng dẫn chuyển đáp án trên giấy đã loại để không cộng trùng. Tham khảo [cấu trúc Listening](https://ielts.org/take-a-test/test-types/ielts-academic-test/ielts-academic-format-listening) và [2 phút kiểm tra trên máy tính](https://ielts.idp.com/uae/about/ielts-on-computer).

App lưu vị trí mỗi **2 giây** và khi tua, Pause, đổi tốc độ/Part. Đóng tab, tải lại, lỗi audio hoặc mất dịch vụ dừng tại checkpoint gần nhất; bấm **Resume** để tiếp tục. Lượt thi sát thật có nhãn **Đã gián đoạn**. Chỉ một tab điều khiển cùng lượt nghe; nếu báo đang mở ở tab khác, đóng tab đó, chờ 8 giây rồi Retry audio connection. Giữ dữ liệu trình duyệt khi còn bản nháp chưa đồng bộ.

Notes/form/summary/sentence có ô nhập trong câu; bảng dùng ô gộp. Matching có câu dẫn trái và lựa chọn phải; dùng Tab và phím mũi tên cho dropdown. Map/diagram có điều khiển trên ảnh; **Zoom diagram** phóng to, cuộn trong vùng hình. **Source** mở trang nguồn local.

Sau nộp chỉ xem bài đã làm. Sau **Chấm bài**, **Transcript** mở bản chép theo Part; player cho nghe lại, đổi tốc độ và lặp A–B. Cambridge 13 Test 3 Parts 1–2 có đoạn khôi phục từ audio do PDF thiếu một trang; app thông báo và bản chép có thể còn sai khác nhỏ về từ ngữ. Cambridge 20 Test 3 lấy lại map từ PDF gốc khác; Test 4 câu 11–12 dùng cặp B/C đối chiếu với audio vì bản gõ khóa thiếu câu 12.

Listening có thang band riêng: 16/18/23/26/30/32/35/37/39 câu tương ứng band 5/5,5/6/6,5/7/7,5/8/8,5/9. Chỉ bài 40 câu có band tham khảo.

## Highlight và ghi chú

Bôi chọn chữ rồi bấm một trong năm nút màu: **Yellow (vàng), Orange (cam), Red (đỏ), Green (xanh lá), Blue (xanh biển)**. Bôi lại bằng màu khác chỉ thay màu trong vùng đang chọn, không tự tăng mức. Chọn chữ rồi bấm **Clear highlight** để xóa toàn bộ hoặc một phần màu. Highlight cũ vẫn giữ màu vàng/cam/đỏ tương ứng.

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

Mở **Sao lưu → Xuất dữ liệu** để tải ZIP. Tệp chứa toàn bộ lượt làm, ghi chú, highlight, đề/đáp án của từng phiên bản và ảnh/audio được các lượt làm tham chiếu, cùng transcript và checkpoint Listening. ZIP mới là phiên bản 2, vẫn khôi phục ZIP phiên bản 1. Giới hạn ZIP 2 GB và tổng giải nén 4 GB; audio được xử lý qua tệp tạm. Nên xuất định kỳ và giữ bản sao ngoài thư mục app.

Để phục hồi, chọn **Khôi phục bản sao lưu → Chọn tệp ZIP**. App ghép các lượt làm, giữ lại bản trên máy nếu bản đó mới hơn. Không cần xóa lịch sử trước khi khôi phục.

Để dùng trên máy khác, clone repository đã có đủ `library`, chạy `CAI_DAT_LAN_DAU.cmd` khi có Internet, rồi khôi phục ZIP nếu muốn chuyển lịch sử học. Không cần PDF nguồn, cache OCR, `node_modules` hoặc `.venv` từ máy cũ. Reading có hạn nộp giữ hạn ban đầu sau khôi phục. Listening dừng và chờ Resume, không tự phát.

## Chọn bố cục Listening và điền Reading

Thanh công cụ Listening có **Layout: Auto / 1 column / 2 columns**, ghi nhớ trên trình duyệt. Auto chia nhóm chọn đáp án/matching từ bốn câu trở lên thành hai nửa: nửa đầu bên trái, nửa sau bên phải. Các nhóm có bảng, đoạn điền liên tục, flow-chart, bản đồ hoặc lựa chọn chung nhiều đáp án giữ nguyên. Dưới 1.100 px, app dùng một cột và khôi phục hai cột khi đủ rộng. Đổi bố cục không đổi vị trí audio hoặc đáp án.

Reading có ô nhập ngay trong chỗ trống của notes, summary và sentences. Nếu đề cung cấp ngân hàng từ/cụm từ, chọn ngay trong dropdown tại chỗ trống. Đọc giới hạn từ trong hướng dẫn; nút **Source** mở ảnh gốc. Số câu, cờ, tự lưu và bước chấm vẫn hoạt động như trước.

Nếu sao chép trực tiếp SQLite thay cho ZIP, hãy dừng app trước và chép cả thư mục `data`; không chỉ chép riêng `.sqlite3` khi dịch vụ đang chạy vì còn tệp WAL.

## Tài liệu và xử lý sự cố

Nút **Source** dùng ảnh đã lưu local, số trang là thứ tự trang trong PDF. Thư viện đã được đối chiếu với bản PDF cung cấp; các sửa OCR và trường hợp nguồn thiếu/sai được ghi trong `library/preparation/`. Bảy bảng Reading điền từ đã chuyển sang bố cục tương tác; ảnh gốc vẫn giữ trong Source để đối chiếu. Cách bổ sung hoặc sửa đề: [DATA_PREPARATION.md](DATA_PREPARATION.md). Đề sửa sau này không âm thầm đổi bài làm cũ.

- **Trình duyệt không mở:** chạy lại MO_UNG_DUNG; đọc địa chỉ được in trong cửa sổ. Xem `data/server.log` nếu dịch vụ không khởi động.
- **Thiếu gói hoặc giao diện:** chạy CAI_DAT_LAN_DAU khi có Internet.
- **App báo chưa kết nối local:** chạy MO_UNG_DUNG và chờ đồng bộ. Đồng hồ thi thử vẫn tiếp tục.
- **Lỗi in nguồn:** Cambridge 15 Test 4 phần summary 27–31 ghi A–J nhưng bản PDF chỉ liệt kê A–I; app giữ chín lựa chọn thực tế. Một số lỗi bản Cambridge 20 được đối chiếu thêm và ghi trong báo cáo chuẩn bị dữ liệu.

Đây là công cụ tự học cá nhân, chưa có giải thích tiếng Việt từng câu, Writing hoặc Speaking.


Lưu ý transcript: Cambridge 13 có nhiều dòng gạch chân bị OCR bỏ sót, nên bản chép dùng hỗ trợ nhận dạng audio local và có thể còn sai khác nhỏ về từ ngữ/tên riêng. Cambridge 20 Test 1 Part 1 có đoạn cuối thiếu trong PDF được khôi phục từ audio. App hiển thị thông báo tại các transcript này; khóa chấm và nội dung câu hỏi được giữ riêng.
