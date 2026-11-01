# Clinic DevForge

> **Trạng thái hiện tại (đọc trước):** repo mới có DB/migration, môi trường local (Docker) và tài liệu.
> **Chưa có mã ứng dụng backend (web server/API) và chưa có frontend**, nên chưa có lệnh "chạy backend"
> hay "chạy frontend". Stack chính thức và kiểu repo (monorepo hay tách repo) **đang chờ tech lead xác nhận**
> (Q1, Q2 trong [khảo sát hiện trạng](docs/khao-sat-hien-trang-repo.md), liên quan DEC-0001).
> README này chỉ ghi những bước **thực sự chạy được hôm nay**. Vì vậy tiêu chí "chạy được cả backend lẫn
> frontend chỉ bằng README" của REQ-001 **chưa đạt**, và task chỉ hoàn thành phần README + mục lục tài liệu
> (cần PM/tech lead xác nhận tách phạm vi); mục
> [Backend và frontend](#backend-và-frontend-chờ-xác-nhận-stack) sẽ được bổ sung khi stack được chốt.

## Cấu trúc repo

```
.
├── README.md                  # tài liệu này
├── docs/                      # thư mục tài liệu (xem docs/README.md)
├── db/                        # runner migration (db/migrate.py) và db/migrations/*.sql
├── tests/                     # unit/ và integration/ + script kiểm tra tài liệu
├── docker-compose.yml         # DB (PostgreSQL) cho môi trường local
├── Makefile                   # make migrate / migrate-status / test
├── .github/                   # mẫu PR
├── pytest.ini
└── (backend/, frontend/)      # CHƯA có: sẽ tạo khi chốt stack và kiểu repo
```

Chi tiết và lý do chưa tách `backend/`, `frontend/`: [docs/README.md](docs/README.md).

## Yêu cầu cài đặt

| Công cụ | Dùng cho | Ghi chú |
|---|---|---|
| Git | clone repo | |
| Python 3.9+ (đã kiểm tra với 3.12) | migration runner, test | `pip install -r requirements-dev.txt` (nên dùng venv, xem Bắt đầu nhanh) |
| Docker kèm Docker Compose v2 | DB local | Tùy chọn; test tích hợp liên quan Docker tự bỏ qua nếu thiếu |
| make | lệnh tắt | Tùy chọn |

Node.js **chưa cần** (chưa có frontend).

## Bắt đầu nhanh

```bash
git clone https://github.com/VuQuoc18/clinic-devforge.git
cd clinic-devforge
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python3 -m pytest tests
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

## Migration schema DB

Runner hiện tại chỉ dùng thư viện chuẩn Python và áp migration lên **SQLite** (mặc định `app.db`):

> `make migrate` chỉ tạo hoặc cập nhật file **SQLite cục bộ** (`app.db`), **không** áp lên
> PostgreSQL trong container `db` của Docker.

```bash
make migrate            # áp mọi migration chưa chạy
make migrate-status     # xem applied / pending
```

> Việc thống nhất DB (PostgreSQL hay SQLite) đang chờ xác nhận stack (Q1); chưa có bước áp
> migration lên PostgreSQL.

Quy ước và các lệnh khác (rollback, `--target`): [docs/db-migrations.md](docs/db-migrations.md).

## Backend và frontend (chờ xác nhận stack)

| Phần | Hiện trạng | Việc cần để README có bước chạy |
|---|---|---|
| Backend (web server/API) | Chưa có mã, entrypoint | Tech lead xác nhận stack (Q1); task dựng khung backend |
| Frontend | Chưa có thư mục | Tech lead xác nhận stack và kiểu repo (Q1, Q2); task dựng khung frontend |

Khi hai phần này có mã, task tương ứng phải thêm vào README các bước cài đặt/chạy và cập nhật
tiêu chí "người mới chạy được cả backend lẫn frontend chỉ bằng README" (REQ-001).

## Test

```bash
python -m pytest tests
```

Test tích hợp `tests/integration/test_local_env.py` tự bỏ qua nếu không có Docker.
Cũng chạy được `make test` (unittest) và các script kiểm tra tài liệu:

```bash
sh tests/check_conventions.sh
sh tests/check_api_conventions.sh
```

## Tài liệu và convention

Mục lục: [docs/README.md](docs/README.md).

- [Quy ước nhánh, commit message và PR](docs/conventions.md) (mẫu PR: [.github/pull_request_template.md](.github/pull_request_template.md))
- [Quy ước API](docs/api-conventions.md) (bản nháp, chờ review)
- [Quy ước migration schema DB](docs/db-migrations.md)
- [Khảo sát hiện trạng repo và câu hỏi mở](docs/khao-sat-hien-trang-repo.md)
- [Changelog](docs/CHANGELOG.md)
