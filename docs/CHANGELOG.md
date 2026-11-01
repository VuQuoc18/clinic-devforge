# Changelog

Mỗi dòng trỏ về PR, ADR hoặc PRD liên quan. Mới nhất ở trên.

| Ngày | Loại | Mô tả | Liên quan |
| --- | --- | --- | --- |
| 2026-11-01 | added | Giới hạn gửi lại OTP theo số điện thoại: chờ 60 giây giữa hai lần gửi, tối đa 5 mã trong 60 phút; từ chối kèm giờ được gửi lại (Asia/Ho_Chi_Minh) và số giây còn lại cho đồng hồ đếm ngược (`POST /v1/otp-codes`, `GET /v1/otp-resend-status`). | TASK-0005, REQ-003, REQ-027 |
| 2026-11-01 | added | Bổ sung quy ước migration schema DB và lệnh chạy migration bằng một lệnh, đã kiểm tra áp toàn bộ migration lên DB trống ở môi trường test. | TASK-0037, PR #6, PRD-0004 |
| 2026-11-01 | added | Bổ sung tài liệu quy ước API cho các API mới: định dạng lỗi, phân trang, đặt tên route, kèm ví dụ request/response cho từng mục. | TASK-0036, PR #5, PRD-0004 |
| 2026-11-01 | added | Thêm lệnh duy nhất để dựng DB và các dịch vụ phụ ở môi trường local; README có hướng dẫn chạy, dừng và dọn dẹp. | TASK-0031, PR #3, PRD-0004 |
| 2026-11-01 | added | Bổ sung tài liệu khảo sát hiện trạng repo Clinic (stack, kiểu repo, lint/test/migration/CI) và trạng thái các câu hỏi mở để chốt phạm vi chuẩn hóa hay dựng mới. | TASK-0029, PR #2, PRD-0004 |
