# Kiểm tra GitHub và bản clone — 24/10/2026

## Những gì đã được đẩy

`git ls-remote origin HEAD refs/heads/main` xác nhận nhánh GitHub `main` ở commit `08041f877bbc425b5206a6d10469e786c773f1c9`, trùng HEAD máy gốc trước sửa. Kiểm kê bằng Git tree, không dựa trên file chỉ có trong working directory:

| Nội dung | Số file | Dung lượng file chưa nén |
|---|---:|---:|
| `Tài liệu Cambridge/` — PDF/audio nguồn | 192 | 1.716,9 MiB |
| `library/assets/` — ảnh Source | 1.662 | 188,8 MiB |
| `library/audio/` — audio chạy app | 128 | 834,5 MiB |
| Đề Reading/Listening, khóa, transcript, manifest, registry | 162 | khoảng 4,9 MiB |
| `library/preparation/` — overrides, báo cáo và cache | 2.649 | 258,1 MiB |
| Mã nguồn, font, logo, công cụ, kiểm thử và hướng dẫn | còn lại | khoảng 6 MiB |

Tổng commit gồm 4.900 file, khoảng 2,94 GiB. Đây là tổng kích thước file hiện tại, không phải kích thước pack tải từ GitHub. Không có `.env`, dependencies, SQLite hay `dist/` trong commit. Không dùng Git LFS.

Theo xác nhận của chủ repository, **tiếp tục giữ tài liệu nguồn trên GitHub**. `.gitignore` đã bổ sung lại bảo vệ `.env` và cache mới; không untrack hoặc xóa tài liệu/cache đã có. Những cache đã tracked tiếp tục được tải khi clone.

## Kiểm tra clone

Đã tạo bản clone riêng từ đúng commit bằng Git shared object store (không tải lại object từ Internet), checkout toàn bộ tài liệu và cài `.venv`, `node_modules`, `dist` mới. Nó không dùng môi trường Python, dependencies Node, `dist` hoặc SQLite của máy gốc.

Môi trường thử: Windows x64, Python 3.13.7, Node 22.19.0, Chrome. Bộ cài `scripts/setup.py` cài dependency và build thành công. Chưa thử trên máy tính thứ hai hoặc nhánh tự tải Python/Node khi chưa có runtime.

Kiểm tra tài nguyên: đủ 32 Reading, 32 Listening, 128 audio và toàn bộ ảnh được tham chiếu. Logo `Quyt sad.png`, `frontend/public/app-logo.png` và logo build đều có SHA-256 `ecd368bfbafc98b2014c5603ae2adefb147c27401125d6cb700e12a355d3e43b`. Không thiếu dữ liệu dropdown Cambridge 13 Test 4 câu 30–34: đủ A–G, khóa vẫn lưu chữ cái.

## Phát hiện và sửa

1. Launcher trước đây chỉ kiểm tra có `dist/index.html`, không kiểm tra build còn khớp mã nguồn sau `git pull`. Cũng có thể dùng lại backend đã chạy trước cập nhật. Đây là thiếu sót xác nhận được trong code; chưa đủ bằng chứng kết luận đó chính là nguyên nhân trên máy kia, nơi bộ cài đã được chạy lại.
2. Logo/favicon trước đây dùng URL cố định `/app-logo.png`. Đã thêm hash nội dung vào URL và yêu cầu revalidate HTML/logo, giảm khả năng trình duyệt dùng ảnh cũ. Tài nguyên logo thực tế đã có trên GitHub.
3. Với lỗi không mở được dropdown theo phản hồi người dùng, ô ngân hàng từ giữ control/giá trị gốc nhưng mở danh sách HTML trong trang, không phụ thuộc cửa sổ chọn native của Windows. Danh sách đặt qua portal để không bị cắt bởi hai vùng cuộn. Đã tách thao tác chọn đáp án khỏi toolbar highlight và bỏ cuộn mượt khi nhảy câu để tránh cửa sổ chọn bị đóng trong lúc cuộn.
4. Thêm `CHAN_DOAN.cmd` để xác định commit, build, logo hash, tài nguyên thiếu và dịch vụ của đúng/sai thư mục. Không đọc hoặc thay đổi bài đang làm.
5. So sánh SHA-256 của 191 PDF/audio nguồn giữa máy gốc và checkout phát hiện **6 PDF khác byte sau checkout** do quy tắc text/CRLF. Các blob đã commit trên GitHub vẫn khớp file gốc. Thêm `.gitattributes` đánh dấu PDF/audio/ảnh/font là binary để checkout giữ nguyên byte. Không cần sửa nội dung PDF trong index, không sửa PDF gốc hoặc viết lại lịch sử commit. Những PDF bị ảnh hưởng là PDF_ANH Cambridge 14, 15, 17, 19 và hai PDF_ANH Cambridge 20. Đây là lỗi checkout tài liệu nguồn, không phải đường dữ liệu JSON dùng cho dropdown.

Trên bản clone có bản sửa, Chrome mở danh sách câu 31 sau một lần bấm, chọn `B. security` bằng chuột, chọn `G` cho câu 32 bằng bàn phím, tải lại giữ nguyên đáp án. Không thay đổi khóa chấm, snapshot hoặc lịch sử cá nhân. Đã kiểm tra API chấm và audio Range trên dữ liệu kiểm thử riêng.

Đã xác nhận danh sách HTML hiển thị đầy đủ A–G và chọn/lưu đáp án bằng thao tác trình duyệt. Công cụ chụp ảnh Chrome bị timeout, nên chưa có ảnh mới cho báo cáo này.

## Giới hạn kết luận

Chưa truy cập được trình duyệt hoặc log của máy kia. Lỗi dropdown/logo không phải do hai tài nguyên này bị `.gitignore` loại khỏi commit hiện tại. Muốn xác định chính xác bản nào đang chạy trên máy kia, chạy `CHAN_DOAN.cmd` sau khi đưa bản sửa này lên GitHub, pull và cài lại. Thay đổi đang ở working tree máy gốc, chưa tự commit hoặc push.
