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

## Cấu hình theo môi trường (dev / test / prod)

Cấu hình đọc từ biến môi trường qua `config.load_settings()`. Chọn môi trường bằng
`APP_ENV` (`dev`, `test`, `prod`; mặc định `dev`, giá trị khác bị từ chối).

Bắt đầu: `cp .env.example .env`, điền giá trị thật rồi nạp vào shell
(`set -a; . ./.env; set +a`). File `.env` và `.env.*` (trừ `.env.example`) đã nằm trong
`.gitignore`; không commit khóa thật.

| Biến | dev | test | prod |
| --- | --- | --- | --- |
| `SMS_API_URL` (địa chỉ cổng SMS) | bắt buộc | bắt buộc | bắt buộc, phải là `https` |
| `SMS_API_KEY` (khóa cổng SMS) | bắt buộc | bắt buộc | bắt buộc |
| `DATABASE_URL` | mặc định `postgresql://app:app@127.0.0.1:5442/app` | mặc định `postgresql://app:app@127.0.0.1:5442/app_test` | bắt buộc |
| `LOG_LEVEL` | mặc định `DEBUG` | mặc định `INFO` | mặc định `WARNING` |

Thiếu biến bắt buộc thì `load_settings()` ném `ConfigError` nêu rõ tên biến và môi trường.
Đổi địa chỉ hoặc khóa SMS chỉ cần đổi `SMS_API_URL` / `SMS_API_KEY`, không sửa code.
Client cổng SMS dùng `load_settings().sms_api_url` và `.sms_api_key`.
