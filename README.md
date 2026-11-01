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

## Truy vết test theo mã BR/FR/REQ

Mã BR/FR/REQ (giữ nguyên dạng, ví dụ `BR-TD-01`, `FR-TD-01`, `REQ-009`) được ghi trong tên/docstring test. Quy ước và ví dụ: `docs/test-traceability.md`. Tìm test theo mã:

```bash
grep -rn --include="*.py" "BR-TD-01" tests
```
