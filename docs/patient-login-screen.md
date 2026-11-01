# MH-TK-01 Đăng nhập bệnh nhân (frontend)

REQ-001, REQ-005, REQ-007, REQ-022. Mã nguồn: `frontend/src/login-screen.js`.

## Hành vi

- Ô số điện thoại + nút "Gửi mã". Số phải gồm 10 chữ số, bắt đầu bằng 0 (`^0[0-9]{9}$`).
  Sai định dạng: nút "Gửi mã" bị khóa, lỗi hiện ngay dưới ô nhập.
- Sau khi gửi: hiện 6 ô OTP (mỗi ô một chữ số), đồng hồ đếm ngược, liên kết "Gửi lại mã"
  chỉ mở khi đếm về 0. Nhập đủ 6 số thì tự xác thực.
- OTP sai: "Mã không đúng" kèm số lần còn lại, thời điểm được thử lại, giờ được gửi lại
  (định dạng `HH:mm:ss dd/MM/yyyy`, giờ Việt Nam UTC+7).
- Không có ô mật khẩu, không có nút Google/Zalo.
- Điều hướng sau đăng nhập theo cờ `is_new_patient`: `true` -> `/ho-so/tao-moi` (form hồ sơ),
  `false` -> `/lich-hen-cua-toi` (Lịch hẹn của tôi).

## Hợp đồng API (giả định tạm, chờ backend xác nhận)

Repo chưa có backend cho đăng nhập OTP; frontend dựa trên hợp đồng sau (theo `docs/api-conventions.md`).
Các route, tên trường và đường dẫn điều hướng cần đối chiếu lại khi backend có.

`POST /v1/patient-otp-requests` `{ "phone": "0912345678" }` -> `200`
`{ "data": { "resend_after_seconds": 60, "resend_available_at": "<ISO UTC>", "expires_at": "<ISO UTC>" } }`

`POST /v1/patient-sessions` `{ "phone": "...", "otp": "123456" }` -> `200`
`{ "data": { "access_token": "...", "is_new_patient": true } }`

OTP sai -> `401`:
`{ "error": { "code": "OTP_INVALID", "message": "...", "meta": { "attempts_remaining": 2, "retry_at": "<ISO UTC>", "resend_available_at": "<ISO UTC>" } } }`

## Test

```bash
cd frontend && npm install && npm test
```

- Unit: `frontend/tests/unit` (jsdom + node:test).
- Integration: `frontend/tests/integration` (màn hình + client API thật + máy chủ HTTP giả).
