# Clinic backend

## Chạy môi trường local (DB và dịch vụ phụ)

Yêu cầu: Docker kèm Docker Compose v2.

Khởi động (một lệnh, từ repo sạch; chờ tới khi các dịch vụ healthy):

```bash
docker compose up -d --wait
```

Backend kết nối DB bằng:

```
DATABASE_URL=postgresql://app:app@127.0.0.1:5442/app
```

Giá trị mặc định (user/password/db `app`, cổng `5442`) đổi được bằng biến môi trường
`DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`.

Dừng (giữ dữ liệu):

```bash
docker compose down
```

Dọn dẹp (xóa container, volume dữ liệu và mạng):

```bash
docker compose down -v
```

Kiểm tra nhanh DB đã nhận kết nối:

```bash
docker compose exec db pg_isready -U app -d app
```

## Test

```bash
python -m pytest tests
```

Test tích hợp `tests/integration/test_local_env.py` tự bỏ qua nếu không có Docker.

## Múi giờ mặc định (REQ-004)

Múi giờ mặc định của hệ thống là `Asia/Ho_Chi_Minh` cho dev, test và prod, **không phụ thuộc
múi giờ máy chủ**. Nguồn duy nhất: `config/timezone.json`.

- Backend: `app/config.py` (`get_settings()`, chọn môi trường bằng `APP_ENV=dev|test|prod`).
- Tiện ích thời gian: `app/timeutil.py` lấy múi giờ từ `app.config`; luôn trả datetime có múi giờ.
- DB: `app/db.py` lưu/đọc `TIMESTAMP` kèm offset `+07:00`; Postgres chạy với `timezone=Asia/Ho_Chi_Minh`
  (`docker-compose.yml`), phiên kết nối dùng `app.db.postgres_connect_kwargs()`.
- Frontend: đọc `config/timezone.json` (chưa có mã frontend trong repo) và truyền làm `timeZone` khi định dạng giờ.
