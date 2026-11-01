# Tài liệu

Thư mục tài liệu của repo. README gốc: [../README.md](../README.md).

## Mục lục

| Tài liệu | Nội dung | Trạng thái |
|---|---|---|
| [conventions.md](conventions.md) | Quy ước nhánh, commit message, PR (REQ-006) | Có hiệu lực |
| [api-conventions.md](api-conventions.md) | Quy ước API: lỗi, phân trang, route (REQ-007) | Bản nháp, chờ DEC-0001 và tech lead review |
| [db-migrations.md](db-migrations.md) | Quy ước và cách chạy migration (REQ-008) | Có hiệu lực |
| [khao-sat-hien-trang-repo.md](khao-sat-hien-trang-repo.md) | Khảo sát hiện trạng, câu hỏi mở Q1–Q4 | Chờ tech lead review |
| [CHANGELOG.md](CHANGELOG.md) | Nhật ký thay đổi tài liệu/repo | Cập nhật theo task |

## Bố cục repo hiện tại

| Thư mục/file | Vai trò |
|---|---|
| `db/` | Runner migration và migration SQL (phần dữ liệu của backend) |
| `tests/unit`, `tests/integration` | Test; `tests/check_*.sh` kiểm tra tài liệu |
| `docker-compose.yml` | DB local |
| `docs/` | Tài liệu (thư mục này) |
| `.github/` | Mẫu PR |

## Về `backend/` và `frontend/` (REQ-001)

Chưa tạo `backend/` và `frontend/`, vì:

- Chưa có mã backend ứng dụng hay frontend để đặt vào đó.
- Kiểu repo (monorepo hay tách) và stack chưa được xác nhận (Q1, Q2 trong
  [khảo sát](khao-sat-hien-trang-repo.md); DEC-0001). Di chuyển `db/`, `tests/` sang `backend/` bây giờ
  sẽ phải làm lại nếu quyết định khác, và làm vỡ đường dẫn trong Makefile, test và tài liệu.

Khi tech lead xác nhận, task tiếp theo sẽ: tạo `backend/` và `frontend/` (nếu monorepo), chuyển các
phần liên quan, và bổ sung bước chạy vào README gốc.

## Quy tắc ghi tài liệu

- Thêm tài liệu mới thì thêm vào bảng mục lục trên và `CHANGELOG.md`.
- Mục chưa được xác nhận phải ghi rõ "chờ xác nhận" kèm mã câu hỏi/DEC liên quan.
