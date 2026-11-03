"""Integration: Makefile gốc giữ nguyên vị trí DB mặc định (app.db ở gốc repo).

Chạy trên bản sao repo tạm (Makefile, backend/Makefile, db, common) để không ghi vào
repo thật và không xoá nhầm app.db của dev.
"""
import os
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import pytest

REAL_ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.skipif(shutil.which("make") is None, reason="không có make")

# Biến do make cha (vd. `make test` ở gốc) truyền xuống, có thể làm lệch kết quả.
_MAKE_ENV = {"DATABASE_PATH", "MAKEFLAGS", "MAKELEVEL", "MFLAGS", "MAKEOVERRIDES"}


@pytest.fixture()
def repo_copy():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "repo"
        (root / "backend").mkdir(parents=True)
        shutil.copy(REAL_ROOT / "Makefile", root / "Makefile")
        shutil.copy(REAL_ROOT / "backend" / "Makefile", root / "backend" / "Makefile")
        for name in ("db", "common"):
            shutil.copytree(REAL_ROOT / "backend" / name, root / "backend" / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        yield root


def _make(root, target, *args):
    env = {k: v for k, v in os.environ.items() if k not in _MAKE_ENV}
    return subprocess.run(["make", target, *args], cwd=root, env=env,
                          capture_output=True, text=True)


def test_root_make_migrate_uses_absolute_given_path(repo_copy):
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "x.db")
        r = _make(repo_copy, "migrate", f"DATABASE_PATH={db}")
        assert r.returncode == 0, r.stderr
        assert os.path.exists(db)
        con = sqlite3.connect(db)
        assert con.execute("select count(*) from schema_migrations").fetchone()[0] >= 1
        con.close()


def test_root_make_default_db_is_at_repo_root_not_backend(repo_copy):
    r = _make(repo_copy, "migrate")
    assert r.returncode == 0, r.stderr
    assert (repo_copy / "app.db").exists()
    assert not (repo_copy / "backend" / "app.db").exists()


def test_backend_make_default_db_is_in_backend(repo_copy):
    env = {k: v for k, v in os.environ.items() if k not in _MAKE_ENV}
    r = subprocess.run(["make", "migrate"], cwd=repo_copy / "backend", env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (repo_copy / "backend" / "app.db").exists()
    assert not (repo_copy / "app.db").exists()


def test_root_make_relative_path_is_relative_to_repo_root(repo_copy):
    (repo_copy / "sub").mkdir()
    r = _make(repo_copy, "migrate", "DATABASE_PATH=sub/rel.db")
    assert r.returncode == 0, r.stderr
    assert (repo_copy / "sub" / "rel.db").exists()
    assert not (repo_copy / "backend" / "sub").exists()


def test_root_make_migrate_supports_path_with_spaces(repo_copy):
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "thu muc co dau cach", "x y.db")
        os.makedirs(os.path.dirname(db))
        r = _make(repo_copy, "migrate", f"DATABASE_PATH={db}")
        assert r.returncode == 0, r.stderr
        assert os.path.exists(db)
