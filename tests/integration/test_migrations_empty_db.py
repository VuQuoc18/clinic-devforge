"""REQ-008: `alembic upgrade head` trên PostgreSQL trống tạo đúng các bảng chính.

Cần một PostgreSQL có quyền CREATE DATABASE. Mặc định dùng DB của docker compose local
(`docker compose up -d --wait`); đổi bằng biến TEST_DATABASE_URL. Không kết nối được thì bỏ qua.
"""
import asyncio
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from clinic_db.url import to_async_url  # noqa: E402

ADMIN_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://app:app@127.0.0.1:5442/postgres")

# Bảng chính -> danh sách cột. Cập nhật cùng revision mới.
EXPECTED_TABLES = {
    "app_info": ["key", "value"],
    "alembic_version": ["version_num"],
}


def _admin_engine():
    return create_async_engine(to_async_url(ADMIN_URL), isolation_level="AUTOCOMMIT")


async def _admin_exec(sql):
    engine = _admin_engine()
    try:
        async with engine.connect() as conn:
            await conn.execute(text(sql))
    finally:
        await engine.dispose()


def _reachable():
    try:
        asyncio.run(_admin_exec("SELECT 1"))
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="Không có PostgreSQL để test")


@pytest.fixture
def empty_db_url():
    name = "alembic_it_" + uuid.uuid4().hex[:12]
    asyncio.run(_admin_exec('CREATE DATABASE "%s"' % name))
    url = make_url(ADMIN_URL).set(database=name).render_as_string(hide_password=False)
    yield url
    asyncio.run(_admin_exec('DROP DATABASE IF EXISTS "%s" WITH (FORCE)' % name))


def alembic(url, *args):
    env = {**os.environ, "DATABASE_URL": url}
    return subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND, env=env,
                          capture_output=True, text=True, timeout=120)


async def _schema(url):
    engine = create_async_engine(to_async_url(url))
    try:
        async with engine.connect() as conn:
            def read(sync_conn):
                insp = inspect(sync_conn)
                return {t: [c["name"] for c in insp.get_columns(t)] for t in insp.get_table_names()}
            tables = await conn.run_sync(read)
            versions = []
            if "alembic_version" in tables:
                versions = [r[0] for r in await conn.execute(text("SELECT version_num FROM alembic_version"))]
            return tables, versions
    finally:
        await engine.dispose()


def schema(url):
    return asyncio.run(_schema(url))


def test_upgrade_head_on_empty_db_creates_tables(empty_db_url):
    assert schema(empty_db_url)[0] == {}
    r = alembic(empty_db_url, "upgrade", "head")
    assert r.returncode == 0, r.stderr
    tables, versions = schema(empty_db_url)
    assert tables == EXPECTED_TABLES
    heads = alembic(empty_db_url, "heads").stdout.split()[0]
    assert versions == [heads]


def test_upgrade_head_is_idempotent(empty_db_url):
    assert alembic(empty_db_url, "upgrade", "head").returncode == 0
    r = alembic(empty_db_url, "upgrade", "head")
    assert r.returncode == 0, r.stderr
    assert schema(empty_db_url)[0] == EXPECTED_TABLES


def test_models_match_migrations(empty_db_url):
    assert alembic(empty_db_url, "upgrade", "head").returncode == 0
    r = alembic(empty_db_url, "check")
    assert r.returncode == 0, r.stderr + r.stdout


def test_downgrade_base_then_reapply(empty_db_url):
    assert alembic(empty_db_url, "upgrade", "head").returncode == 0
    assert alembic(empty_db_url, "downgrade", "base").returncode == 0
    assert list(schema(empty_db_url)[0]) == ["alembic_version"]
    assert alembic(empty_db_url, "upgrade", "head").returncode == 0
    assert schema(empty_db_url)[0] == EXPECTED_TABLES


def test_legacy_runner_removed_and_unreferenced():
    legacy = "db/" + "migrate" + ".py"
    assert not (ROOT / legacy).exists()
    tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                             cwd=ROOT, capture_output=True, text=True).stdout.split()
    for rel in tracked:
        p = ROOT / rel
        if not p.is_file() or rel.endswith(".pyc"):
            continue
        assert legacy not in p.read_text(encoding="utf-8", errors="ignore"), rel
