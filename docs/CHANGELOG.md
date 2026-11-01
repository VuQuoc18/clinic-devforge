# Changelog

Mỗi dòng trỏ về PR, ADR hoặc PRD liên quan. Mới nhất ở trên.

| Ngày | Loại | Mô tả | Liên quan |
| --- | --- | --- | --- |
| 2026-11-01 | added | Thêm cấu hình tách theo môi trường dev/test/prod đọc từ biến môi trường, gồm địa chỉ và khóa cổng SMS; có `.env.example`, `.gitignore` cho file env thật và mô tả trong README. | TASK-0032, REQ-003 |
| 2026-11-01 | added | Bổ sung quy ước migration schema DB và lệnh chạy migration bằng một lệnh, đã kiểm tra áp toàn bộ migration lên DB trống ở môi trường test. | TASK-0037, PR #6, PRD-0004 |
| 2026-11-01 | added | Bổ sung tài liệu quy ước API cho các API mới: định dạng lỗi, phân trang, đặt tên route, kèm ví dụ request/response cho từng mục. | TASK-0036, PR #5, PRD-0004 |
| 2026-11-01 | added | Thêm lệnh duy nhất để dựng DB và các dịch vụ phụ ở môi trường local; README có hướng dẫn chạy, dừng và dọn dẹp. | TASK-0031, PR #3, PRD-0004 |
| 2026-11-01 | added | Bổ sung tài liệu khảo sát hiện trạng repo Clinic (stack, kiểu repo, lint/test/migration/CI) và trạng thái các câu hỏi mở để chốt phạm vi chuẩn hóa hay dựng mới. | TASK-0029, PR #2, PRD-0004 |
