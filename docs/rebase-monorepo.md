# Hướng dẫn rebase nhánh `devforge/task-00xx` sau PR monorepo (TASK-0042)

Mốc: PR TASK-0042 (REQ-001) là mốc rebase duy nhất. Chủ nhánh `devforge/task-00xx`
rebase lên `master` sau khi PR này merge.

## Ánh xạ đường dẫn

| Cũ (gốc repo) | Mới |
| --- | --- |
| `common/` | `backend/common/` |
| `db/` | `backend/db/` |
| `tests/` | `backend/tests/` |
| `Makefile` | `Makefile` (chuyển tiếp) + `backend/Makefile` (lệnh thật) |
| `pytest.ini` | `backend/pytest.ini` |

## Các bước

```bash
git fetch origin
git rebase origin/master   # git phát hiện rename nên thường tự áp thay đổi vào backend/
```

- Nếu git báo conflict dạng "rename/modify" hoặc "file location": giữ phiên bản của bạn
  nhưng đặt file ở đường dẫn mới `backend/...` (`git mv` rồi `git add`).
- File mới thêm vào `common/`, `db/`, `tests/` ở nhánh cũ: chuyển vào `backend/` tương ứng.
  Test `backend/tests/unit/test_repo_layout.py` sẽ fail nếu còn thư mục này ở gốc.
- Import (`from common...`, `from db...`) giữ nguyên; chạy test từ `backend/`
  (`cd backend && python -m pytest tests` hoặc `make test` ở gốc).
- Đường dẫn trong lệnh/CI: `python3 db/migrate.py` → `python3 backend/db/migrate.py`.

## DB dev mặc định

`make migrate` ở gốc vẫn dùng `app.db` ở gốc repo (đường dẫn tương đối tính từ gốc).
Chạy `make migrate` trực tiếp trong `backend/` sẽ dùng `backend/app.db`.
