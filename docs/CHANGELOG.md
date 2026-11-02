# Changelog

Mỗi dòng trỏ về PR, ADR hoặc PRD liên quan. Mới nhất ở trên.

| Ngày | Loại | Mô tả | Liên quan |
| --- | --- | --- | --- |
| 2026-11-02 | changed | Repo chuyển sang monorepo `backend/`, `frontend/`, `docs/`; `common/`, `db/`, `tests/` (cùng `Makefile`, `pytest.ini`) dời vào `backend/` trong một PR. Các nhánh `devforge/task-00xx` cần rebase sau PR này. **Lưu ý:** thư mục đích của `common/`, `db/`, `tests/` là giả định ban đầu, CHƯA có DEC/PRD xác nhận của PM/tech lead; cần bổ sung tham chiếu DEC trước khi merge. Việc chuyển Alembic (cùng PR theo task) chưa nằm trong thay đổi này. | TASK-0042, REQ-001 |
| 2026-11-01 | added | Thời gian trong mô-đun tài khoản hiển thị thống nhất theo giờ Việt Nam (Asia/Ho_Chi_Minh) và mốc chốt hằng ngày được tính đúng lúc 23:59. | TASK-0002, PR #7, PRD-0001 |
| 2026-11-01 | added | Thêm module `common/vn_time.py`: đồng hồ giả lập được, cộng khoảng thời gian, định dạng hiển thị Asia/Ho_Chi_Minh, mốc 23:59 hằng ngày; thời điểm lưu UTC. | TASK-0002, REQ-027 |
| 2026-11-01 | added | Bổ sung quy ước migration schema DB và lệnh chạy migration bằng một lệnh, đã kiểm tra áp toàn bộ migration lên DB trống ở môi trường test. | TASK-0037, PR #6, PRD-0004 |
| 2026-11-01 | added | Bổ sung tài liệu quy ước API cho các API mới: định dạng lỗi, phân trang, đặt tên route, kèm ví dụ request/response cho từng mục. | TASK-0036, PR #5, PRD-0004 |
| 2026-11-01 | added | Thêm lệnh duy nhất để dựng DB và các dịch vụ phụ ở môi trường local; README có hướng dẫn chạy, dừng và dọn dẹp. | TASK-0031, PR #3, PRD-0004 |
| 2026-11-01 | added | Bổ sung tài liệu khảo sát hiện trạng repo Clinic (stack, kiểu repo, lint/test/migration/CI) và trạng thái các câu hỏi mở để chốt phạm vi chuẩn hóa hay dựng mới. | TASK-0029, PR #2, PRD-0004 |
