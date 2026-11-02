"""Integration: Makefile gốc giữ nguyên vị trí DB mặc định (app.db ở gốc repo)."""
import os
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.skipif(shutil.which("make") is None, reason="không có make")


def _make(target, *args, cwd=ROOT):
    env = {k: v for k, v in os.environ.items() if k != "DATABASE_PATH"}
    return subprocess.run(["make", target, *args], cwd=cwd, env=env,
                          capture_output=True, text=True)


def test_root_make_migrate_uses_absolute_given_path():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "x.db")
        r = _make("migrate", f"DATABASE_PATH={db}")
        assert r.returncode == 0, r.stderr
        assert os.path.exists(db)
        con = sqlite3.connect(db)
        assert con.execute("select count(*) from schema_migrations").fetchone()[0] >= 1
        con.close()


def test_root_make_default_db_is_at_repo_root_not_backend():
    root_db, backend_db = ROOT / "app.db", ROOT / "backend" / "app.db"
    if root_db.exists() or backend_db.exists():
        pytest.skip("app.db có sẵn, không ghi đè DB dev")
    try:
        r = _make("migrate")
        assert r.returncode == 0, r.stderr
        assert root_db.exists()
        assert not backend_db.exists()
    finally:
        root_db.unlink(missing_ok=True)


def test_root_make_relative_path_is_relative_to_repo_root():
    with tempfile.TemporaryDirectory(dir=ROOT) as d:
        rel = os.path.relpath(os.path.join(d, "rel.db"), ROOT)
        r = _make("migrate", f"DATABASE_PATH={rel}")
        assert r.returncode == 0, r.stderr
        assert os.path.exists(os.path.join(d, "rel.db"))
        assert not (ROOT / "backend" / rel).exists()
