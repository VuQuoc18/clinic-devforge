"""Unit: bố cục monorepo (TASK-0042, REQ-001)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_monorepo_top_level_dirs_exist():
    for d in ("backend", "frontend", "docs"):
        assert (ROOT / d).is_dir(), f"thiếu thư mục {d}/"


def test_moved_dirs_live_in_backend():
    for d in ("common", "db", "tests"):
        assert (ROOT / "backend" / d).is_dir(), f"thiếu backend/{d}/"


def test_moved_dirs_not_recreated_at_root():
    # Nhánh cũ sau rebase có thể vô tình tạo lại thư mục ở gốc.
    for d in ("common", "db", "tests"):
        assert not (ROOT / d).exists(), f"{d}/ không được nằm ở gốc repo"
