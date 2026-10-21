# Đưa mã nguồn lên GitHub

Repository: https://github.com/blinx1st/IELTS-PRACTICE-APPS-LOCAL

Mã nguồn ứng dụng được quản lý bằng Git. PDF, thư viện đề Cambridge, ảnh chụp có nội dung đề, SQLite, bản sao lưu, file môi trường và các script chứa bản chép câu hỏi/đáp án được giữ riêng trên máy theo `.gitignore`.

## Lần đầu chuẩn bị Git

Chỉ thực hiện phần này nếu thư mục dự án chưa có Git. Repository trên GitHub đã có README, nên lấy lịch sử hiện có trước khi tạo commit mã nguồn:

```powershell
Set-Location -LiteralPath 'D:\Học Ielts\App luyện Ielts'
git init -b main
git remote add origin https://github.com/blinx1st/IELTS-PRACTICE-APPS-LOCAL.git
git fetch origin main
git reset --mixed origin/main
git branch --set-upstream-to=origin/main main
```

Lệnh `reset --mixed` ở trên chỉ dùng trong lần thiết lập này khi chưa có commit local: đặt nhánh theo lịch sử README trên GitHub và giữ nguyên nội dung file trên ổ đĩa.

## Đưa code lên

Mở Terminal PowerShell tại thư mục dự án:

```powershell
git add .
git diff --cached --stat
git commit -m "Add local IELTS Reading app"
git push -u origin main
```

Nếu Git báo thiếu danh tính, điền tên và email GitHub của chính bạn rồi chạy lại lệnh commit:

```powershell
git config user.name "Tên của bạn"
git config user.email "Email GitHub của bạn"
```

Nếu xuất hiện cửa sổ đăng nhập GitHub, đăng nhập bằng tài khoản có quyền ghi repository. Không đưa mật khẩu hoặc token vào mã nguồn hay URL remote.

## Các lần cập nhật tiếp theo

```powershell
git add .
git diff --cached --stat
git commit -m "Update IELTS app"
git push
```

Nếu GitHub có commit mới từ máy khác, commit thay đổi của bạn, chạy `git pull --rebase origin main`, giải quyết xung đột nếu có rồi push. Không cần force push.

## Dùng trên máy khác

Clone repository, chép riêng thư mục `library/` từ máy đang có đề, rồi chạy `CAI_DAT_LAN_DAU.cmd`. Dữ liệu học được chuyển qua chức năng sao lưu ZIP trong app; không được tự động tải từ GitHub.

Việc đẩy mã nguồn lên GitHub không đưa backend local lên Internet. App vẫn chạy tại `127.0.0.1` trên máy dùng app.
