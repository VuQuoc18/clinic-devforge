"""Unit: bố cục monorepo (TASK-0042, REQ-001, DEC-0112).

LƯU Ý: thư mục đích `backend/` cho common/, db/, tests/ là GIẢ ĐỊNH ban đầu, CHƯA có
DEC/PRD xác nhận riêng cho đích này (DEC-0112 chỉ chốt việc gộp cùng PR Alembic).
Khi PM/tech lead chốt đích, chỉ cần sửa MOVED_DEST (và dẫn mã DEC vào đây); các test
bên dưới đọc đích từ hằng số này nên không cứng `backend/` rải rác.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MOVED_DEST = "backend"  # TODO: xác nhận bằng DEC/PRD trước khi merge


def test_monorepo_top_level_dirs_exist():
    for d in ("backend", "frontend", "docs"):
        assert (ROOT / d).is_dir(), f"thiếu thư mục {d}/"


def test_moved_dirs_live_in_decided_destination():
    for d in ("common", "db", "tests"):
        assert (ROOT / MOVED_DEST / d).is_dir(), f"thiếu {MOVED_DEST}/{d}/"


def test_moved_dirs_not_recreated_at_root():
    # Nhánh cũ sau rebase có thể vô tình tạo lại thư mục ở gốc.
    for d in ("common", "db", "tests"):
        assert not (ROOT / d).exists(), f"{d}/ không được nằm ở gốc repo"
