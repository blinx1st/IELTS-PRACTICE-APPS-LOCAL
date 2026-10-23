# Đưa mã nguồn lên GitHub

Repository: https://github.com/blinx1st/IELTS-PRACTICE-APPS-LOCAL

Repository chứa mã nguồn, thư viện đã chuẩn hóa (đề, khóa, transcript, ảnh Source, 128 audio, manifest và overrides) và **PDF/audio gốc trong `Tài liệu Cambridge/`** theo lựa chọn cập nhật ngày 24/10/2026. Dùng Git thông thường, không cần Git LFS. Bộ file đang theo dõi khoảng 2,94 GiB, gồm khoảng 1 GiB dữ liệu chạy app, 1,68 GiB tài liệu nguồn và 258 MiB dữ liệu chuẩn bị. Dependencies, build, SQLite, ZIP và file môi trường không đưa lên Git.

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

Clone repository rồi chạy `CAI_DAT_LAN_DAU.cmd` khi có Internet. Không cần chép `library/` riêng hoặc có PDF nguồn. Bộ cài kiểm tra đủ tài nguyên trước khi cài; `MO_UNG_DUNG.cmd` kiểm tra lại khi mở app. Sau thiết lập, việc học hoạt động offline. Dữ liệu học cá nhân được chuyển qua ZIP trong app.

```powershell
git clone https://github.com/blinx1st/IELTS-PRACTICE-APPS-LOCAL.git
Set-Location -LiteralPath 'IELTS-PRACTICE-APPS-LOCAL'
.\CAI_DAT_LAN_DAU.cmd
```

Cache đã được theo dõi vẫn còn trong index; lần kiểm tra này không tự bỏ file khỏi Git. `.gitignore` chỉ ngăn cache mới. Tài liệu nguồn vẫn được giữ cả trên Git lẫn ổ đĩa. Lịch sử commit giữ nguyên nên dung lượng tải lần đầu có thể lớn hơn bộ file hiện tại. Không dùng `git clean` để dọn tài liệu local.

## Cập nhật bản đã clone

1. Dừng app bằng `DUNG_UNG_DUNG.cmd` của đúng thư mục.
2. Chạy `git pull --ff-only`.
3. Chạy `CAI_DAT_LAN_DAU.cmd` khi có Internet, rồi `MO_UNG_DUNG.cmd`.
4. Mở đúng URL launcher in ra; cổng có thể là 8766–8775 nếu 8765 đang bận. Không mở lại bookmark của bản clone khác.

`dist/` không đưa lên Git. Bản mới lưu fingerprint của mã nguồn khi build; launcher phát hiện build cũ và yêu cầu cập nhật. Nó cũng từ chối dùng lại backend cũ sau khi cập nhật code, để tránh giao diện mới gọi dịch vụ cũ. Logo và favicon có URL kèm hash nội dung để trình duyệt lấy đúng ảnh mới.

Nếu còn lỗi, chạy **CHAN_DOAN.cmd** trên máy gặp lỗi, gửi kết quả gồm commit, `buildCurrent`, fingerprint, logo hash, tài nguyên thiếu và danh sách URL dịch vụ. Công cụ không mở bài làm hay thay đổi đồng hồ. Xem [biên bản kiểm tra bản clone](docs/GITHUB_CLONE_AUDIT.md).

Việc đẩy mã nguồn lên GitHub không đưa backend local lên Internet. App vẫn chạy tại `127.0.0.1` trên máy dùng app.
