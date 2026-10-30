# Telegram Auto-Forward (link)

Tin nhắn mới có **link** → kiểm tra filter → forward sang chat đích.

- Không cài nguồn → nghe **tất cả** chat.
- Không cài filter link → **có link là forward**.
- Tin không có link → bỏ qua.
- Hỗ trợ link trong text, caption ảnh/video, link ẩn sau chữ, nút bấm; album forward nguyên nhóm.

## Cài đặt

1. Lấy `API_ID`, `API_HASH` tại https://my.telegram.org → *API development tools*.
2. Copy `.env.example` thành `.env` rồi điền vào.
3. Cài thư viện:
   ```
   pip install -r requirements.txt
   ```
4. Chạy:
   ```
   python main.py
   ```
   Lần đầu sẽ hỏi số điện thoại + mã OTP (+ mật khẩu 2 lớp nếu có). Sau đó lưu vào file `forwarder.session` — **không chia sẻ file này**.

## Cấu hình

Sửa `config.yaml` (cần chạy lại) **hoặc** gõ lệnh trong **Saved Messages** (áp dụng ngay):

```
/help                       xem tất cả lệnh
/addtarget -1001234567890   thêm nơi nhận tin (bắt buộc)
/addsource @channel_a       chỉ nghe kênh này (bỏ trống = nghe tất cả)
/adddomain shopee.vn t.me   chỉ forward link shopee / t.me
/addexdomain bit.ly         bỏ link bit.ly
/addkw ref=                 link chứa "ref="
/mode copy                  ẩn nguồn (forward = giữ tên nguồn)
/blockbots on|off           chặn / cho phép tin từ bot (mặc định: chặn)
/status                     xem cấu hình
/test https://shopee.vn/x   thử xem có forward không
```

Lấy id chat: forward 1 tin từ chat đó cho `@userinfobot`, hoặc dùng `@username` của kênh.

### Cách filter hoạt động
1. Link thuộc `exclude_domains` bị loại.
2. Nếu `domains`, `keywords`, `regex` đều trống → còn link là forward.
3. Ngược lại, chỉ cần **1 link khớp 1 filter bất kỳ** là forward.

## Lưu ý
- Đây là **userbot** (chạy bằng tài khoản của bạn). Forward quá dày có thể bị Telegram giới hạn → tăng `/delay` nếu thấy FloodWait trong log.
- Chat đích và Saved Messages luôn được bỏ qua để tránh forward vòng lặp.
- Kênh bật "Restrict saving content" không forward/copy được (log sẽ báo lỗi).
- Log nằm ở `logs/forward.log`.
