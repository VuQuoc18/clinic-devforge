# Khảo sát hiện trạng repo Clinic (TASK-0029)

- Phạm vi: REQ-001 (cấu trúc repo + README), REQ-005 (lint/format/pre-commit), REQ-010 (CI cho mỗi PR). Liên quan DEC-0001.
- Ngày khảo sát: theo commit `3077e24` trên `origin/master`/nhánh task và nhánh `origin/devforge/task-0001-...`.
- Trạng thái tài liệu: **chờ tech lead review** (chưa được duyệt).
- Nguyên tắc: tài liệu này chỉ ghi nhận hiện trạng. **Không chọn stack thay cho team**; mọi mục "chờ xác nhận" phải được người chịu trách nhiệm trả lời trước khi task sau triển khai.

## 1. Phương pháp

Đã rà `git ls-files`, `git log --all`, danh sách nhánh remote và nội dung các file cấu hình ở mọi nhánh. Không có tài liệu, issue hay cấu hình CI nằm ngoài git để đối chiếu.

## 2. Hiện trạng theo nhánh

| Nhánh | Nội dung |
|---|---|
| `origin/master` (commit `6414ad0 init`) | Chỉ có `README.md` **rỗng (0 byte)**. Không có mã nguồn, cấu hình hay test. |
| `origin/devforge/task-0001-luoc-do-du-lieu-tk-tai-khoan-benh-nhan-h` (commit `3077e24`, **chưa merge vào master**) | Lược đồ dữ liệu TK (REQ-026): models SQLAlchemy, migration Alembic, pytest. Chi tiết ở mục 3. |

Kết luận: trên `master` **chưa có nền nào**. Mã duy nhất là nhánh TASK-0001 chưa merge; nếu được merge, đó là nền backend ban đầu.

## 3. Những gì có ngầm trong code (nhánh TASK-0001)

Đây là dấu vết kỹ thuật, **không phải quyết định stack đã được xác nhận**.

| Hạng mục | Quan sát | Bằng chứng |
|---|---|---|
| Ngôn ngữ backend | Python | `app/models.py`, `requirements.txt` |
| ORM / DB layer | SQLAlchemy >= 2.0 (kiểu `Mapped`/`DeclarativeBase`) | `requirements.txt`, `app/models.py` |
| Web framework | **Chưa có** (chưa có API, entrypoint, server) | không có file tương ứng |
| DB | SQLite mặc định cho dev/test (`sqlite:///app.db`); ghi đè bằng biến `DATABASE_URL`. DB production **chưa xác định**. | `alembic.ini`, `migrations/env.py` |
| Migration | Alembic >= 1.12; `migrations/versions/0001_initial_schema.py`; `render_as_batch=True` (để tương thích SQLite) | `alembic.ini`, `migrations/env.py` |
| Test | pytest >= 7; `tests/unit`, `tests/integration`; fixture migrate DB tạm | `pytest.ini`, `tests/conftest.py` |
| Frontend | **Không có** | không có thư mục/`package.json` |
| Lint / format | **Không có** (không ruff/flake8/black/isort, không ESLint/Prettier) | không có file cấu hình |
| Pre-commit | **Không có** (`.pre-commit-config.yaml` không tồn tại) | — |
| CI | **Không có** (không `.github/workflows`, GitLab CI, v.v.) | — |
| Docker / triển khai | **Không có** (không Dockerfile, compose, IaC) | — |
| Quản lý phụ thuộc | `requirements.txt` không pin chặt (`>=`); không lockfile | `requirements.txt` |
| README | Rỗng trên master; nhánh TASK-0001 cũng không hướng dẫn chạy | — |
| `.gitignore` | Tối thiểu: `app.db`, `__pycache__/`, `.pytest_cache/` | `.gitignore` |
| Kiểu repo | Hiện là một repo đơn, bố cục phẳng (`app/`, `migrations/`, `tests/` ở gốc). Chưa có `backend/`, `frontend/`. **Chưa kết luận monorepo hay tách repo** | — |
| Thư mục tài liệu | Chưa có trước task này; `docs/` được tạo bởi tài liệu này | — |

## 4. Đã có / còn thiếu theo REQ

| REQ | Đã có | Còn thiếu |
|---|---|---|
| REQ-001 cấu trúc repo + README chạy local | Bố cục backend phẳng và `docs/` (nhánh TASK-0001, chưa merge) | Thư mục frontend; quyết định kiểu repo; README hướng dẫn chạy backend và frontend; web framework/entrypoint để chạy được |
| REQ-005 lint/format/pre-commit | Không có gì | Chọn công cụ cho backend và frontend (phụ thuộc stack); cấu hình dùng chung cho pre-commit và CI |
| REQ-010 CI mỗi PR | Không có gì. Có sẵn lệnh test (`pytest`) và migration (`alembic upgrade head`) để CI gọi | Chọn nền tảng CI; pipeline build/lint/test; branch protection bắt buộc pipeline pass |

## 5. Quyết định phạm vi: chuẩn hóa hay dựng mới

| Phần | Đề xuất | Điều kiện |
|---|---|---|
| Backend (Python, SQLAlchemy, Alembic, pytest) | **Chuẩn hóa nền có sẵn** của TASK-0001: merge, bổ sung README, lint, CI. **Không dựng lại.** | Chờ xác nhận Q1: Python/SQLAlchemy có phải stack chính thức không. Nếu không thì phải dựng mới. |
| Web framework backend | **Dựng mới** | Chờ Q1 |
| Frontend | **Dựng mới** (hoàn toàn chưa có) | Chờ Q1 |
| Lint/format/pre-commit | **Dựng mới** | Chờ Q1 |
| CI | **Dựng mới** | Chờ Q3 |
| Cấu trúc thư mục | Phụ thuộc kiểu repo | Chờ Q2 |

Đề xuất này chỉ là đề xuất. Các task sau (REQ-001/005/010) **không được bắt đầu chọn công cụ** cho tới khi các câu hỏi chặn tương ứng ở mục 6 được trả lời. Task độc lập với stack (ví dụ README khung, `docs/`) có thể làm trước.

## 6. Đối chiếu Câu hỏi mở

Cột "Người chịu trách nhiệm" là **vai trò đề xuất**. Repo và brief không nêu tên người; cần tech lead chỉ định tên cụ thể khi review.

| # | Câu hỏi mở | Trạng thái | Người chịu trách nhiệm (đề xuất) | Dữ kiện hiện có / ảnh hưởng |
|---|---|---|---|---|
| Q1 | Stack backend / frontend / DB chính thức là gì? | **Còn chờ** (chưa có xác nhận). Chỉ có dấu vết ngầm: Python + SQLAlchemy + Alembic + SQLite dev. Frontend chưa có gì. | Tech lead | Chặn REQ-005 (công cụ lint) và phần dựng mới của REQ-001. Liên quan DEC-0001. |
| Q2 | Kiểu repo: monorepo hay tách backend/frontend? | **Còn chờ** | Tech lead | Chặn bố cục thư mục và cách CI chạy (REQ-001, REQ-010). Hiện là một repo `clinic-devforge`, bố cục phẳng. |
| Q3 | Nơi triển khai và nền tảng CI? | **Còn chờ**. Remote là GitHub (`VuQuoc18/clinic-devforge`) nhưng chưa có xác nhận dùng GitHub Actions và chưa có thông tin môi trường chạy. | Tech lead phối hợp DevOps/chủ dự án | Chặn REQ-010; DB production chưa rõ. |
| Q4 | Convention sẵn có (code style, đặt tên, commit/branch, quy trình PR)? | **Còn chờ**. Trong repo chỉ thấy quy ước ngầm: nhánh `devforge/task-NNNN-<slug>`, commit `TASK-NNNN: <mô tả>`, test chia `unit`/`integration`. Chưa có tài liệu convention hay cấu hình formatter. | Tech lead | Chặn bộ quy tắc REQ-005. |

Không câu nào ở trạng thái "đã trả lời". Không câu nào được tự trả lời trong tài liệu này.

## 7. Việc cần tech lead quyết định khi review

1. Xác nhận hoặc thay đổi stack (Q1) và kiểu repo (Q2).
2. Chọn nền tảng CI và nơi triển khai (Q3).
3. Xác nhận hoặc bổ sung convention (Q4).
4. Quyết định có merge nhánh TASK-0001 làm nền backend không.
5. Chỉ định tên người chịu trách nhiệm cho từng câu hỏi.

## 8. Rủi ro

- Làm lint/CI trước khi chốt stack dễ phải làm lại.
- `master` đang trống nên người mới clone chưa chạy được gì. Nhánh TASK-0001 phải được merge thì mới có nền.
- Dependency chưa pin có thể làm CI không tái lập được.
- SQLite dev khác DB production (nếu khác) về kiểu dữ liệu và ràng buộc; cần kiểm tra khi chốt DB.
