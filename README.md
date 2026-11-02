# Clinic

## Cấu trúc repo (monorepo)

```
backend/    # mã backend: common/, db/ (migration), tests/, Makefile, pytest.ini
frontend/   # frontend (React, Vite, TypeScript, shadcn/ui, pnpm) - chưa có mã nguồn
docs/       # tài liệu
docker-compose.yml   # DB và dịch vụ phụ cho môi trường local
```


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
cd backend && python -m pytest tests
```

Test tích hợp `backend/tests/integration/test_local_env.py` tự bỏ qua nếu không có Docker.
