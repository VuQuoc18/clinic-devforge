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

## Đăng nhập nhân viên (/quan-tri)

```bash
make migrate
STAFF_PASSWORD='...' python3 -m app create-staff nhanvien@phongkham.vn --full-name "Tên"
AUTH_SECRET='<chuoi-bi-mat>' AUTH_COOKIE_SECURE=0 python3 -m app serve   # http://127.0.0.1:8000/quan-tri
```

- Trang: `/quan-tri/dang-nhap`, trang quản lý: `/quan-tri/quan-ly`, API: `POST /quan-tri/v1/auth/login`.
- Bệnh nhân (số điện thoại + OTP) dùng `POST /v1/auth/patient/login`. Hai miền xác thực dùng cookie và khóa ký riêng, không chấp nhận chéo.
- `AUTH_COOKIE_SECURE=0` chỉ dùng khi chạy local qua HTTP.

## Test

```bash
python -m pytest tests
```

Test tích hợp `tests/integration/test_local_env.py` tự bỏ qua nếu không có Docker.
