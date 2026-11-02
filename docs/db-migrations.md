# Quy ước migration schema DB (REQ-008)

Phạm vi: thay đổi **schema** DB PostgreSQL bằng **Alembic** (SQLAlchemy). Alembic thay hoàn toàn
runner SQL cũ; dữ liệu cũ không được giữ và revision đầu (`0001`) được sinh lại từ model hiện tại.
Việc chuyển dữ liệu từ Excel nằm ngoài phạm vi tài liệu này.

## Bố cục (trong `backend/`)

```
backend/alembic.ini                         # cấu hình Alembic
backend/clinic_db/base.py                   # Base (DeclarativeBase), metadata cho autogenerate
backend/clinic_db/models.py                 # model SQLAlchemy (nguồn sự thật của schema)
backend/clinic_db/url.py                    # đọc DATABASE_URL, đổi sang driver asyncpg
backend/migrations/env.py                   # env Alembic (async)
backend/migrations/versions/<REV>_<mo_ta>.py
```

## Đặt tên revision

- Tên file: `<REV>_<mo_ta>.py`; `REV` là số thứ tự 4 chữ số, bắt đầu `0001`, tăng liên tục,
  **không nhảy số**, và trùng với `revision` trong file.
- `mo_ta`: `snake_case` chữ thường/số, động từ + đối tượng (`create_...`, `add_..._to_...`).
- Regex: `^\d{4}_[a-z0-9]+(_[a-z0-9]+)*\.py$`.
- Tạo revision mới (số kế tiếp, ví dụ `0002`):

```bash
cd backend
alembic revision --autogenerate -m create_users --rev-id 0002
```

Luôn đọc lại file sinh ra trước khi commit.

## Thứ tự áp dụng

- Các revision tạo thành **một chuỗi thẳng** (`down_revision` của `0002` là `0001`, ...). Không tạo nhiều head.
- Áp theo thứ tự chuỗi; Alembic ghi version hiện tại vào bảng `alembic_version`.
- Mỗi revision chạy trong một transaction (DDL của PostgreSQL có transaction); lỗi thì rollback revision đó và dừng.
- Hai nhánh cùng tạo cùng số: người merge sau đổi lại số và `down_revision` trước khi merge.

## Quy tắc

- **Không sửa revision đã merge/áp dụng**; muốn đổi thì thêm revision mới.
- Sửa model xong phải có revision tương ứng: `alembic check` không được báo thay đổi chưa có migration.
- Viết `downgrade()` cho mỗi revision (dùng chủ yếu cho dev/test; production ưu tiên roll forward).
- Khi thêm revision, cập nhật `EXPECTED_TABLES` trong `tests/integration/test_migrations_empty_db.py`.

## Cách áp dụng (một lệnh)

Cài phụ thuộc: `pip install -r backend/requirements.txt`. DB local: `docker compose up -d --wait` (xem README).

```bash
cd backend
export DATABASE_URL=postgresql://app:app@127.0.0.1:5442/app   # mặc định nếu không đặt
alembic upgrade head
```

Hoặc từ gốc repo: `make migrate`. Xem trạng thái: `alembic current` / `make migrate-status`.
`DATABASE_URL` dạng `postgresql://...` được tự đổi sang driver `asyncpg`.

## Rollback (dev/test)

```bash
cd backend
alembic downgrade -1      # lùi 1 revision
alembic downgrade base    # lùi hết
```

## Kiểm thử

```bash
python -m pytest tests
```

- Unit test: `tests/unit/test_db_config.py` (chuẩn hóa URL, đặt tên và thứ tự revision, model đăng ký).
- Integration test: `tests/integration/test_migrations_empty_db.py` tạo DB PostgreSQL trống, chạy
  `alembic upgrade head`, kiểm tra các bảng chính, `alembic check`, downgrade/upgrade lại. Dùng DB của
  docker compose (cổng `5442`) hoặc đặt `TEST_DATABASE_URL` (user cần quyền `CREATE DATABASE`); không kết nối được thì test bị bỏ qua.
- CI (đề xuất): chạy PostgreSQL service rồi `python -m pytest tests` để luôn kiểm tra `alembic upgrade head` trên DB trống.
