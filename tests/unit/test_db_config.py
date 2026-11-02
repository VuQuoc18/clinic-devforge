"""Unit: URL DB và quy ước đặt tên revision Alembic (REQ-008)."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
VERSIONS = BACKEND / "migrations" / "versions"
sys.path.insert(0, str(BACKEND))

from clinic_db.url import DEFAULT_DATABASE_URL, get_database_url, to_async_url  # noqa: E402


@pytest.mark.parametrize("url,expected", [
    ("postgresql://u:p@h:5432/d", "postgresql+asyncpg://u:p@h:5432/d"),
    ("postgres://u:p@h/d", "postgresql+asyncpg://u:p@h/d"),
    ("postgresql+asyncpg://u:p@h/d", "postgresql+asyncpg://u:p@h/d"),
])
def test_to_async_url(url, expected):
    assert to_async_url(url) == expected


@pytest.mark.parametrize("url", ["sqlite:///app.db", "mysql://u@h/d", ""])
def test_to_async_url_rejects_non_postgres(url):
    with pytest.raises(ValueError):
        to_async_url(url)


def test_get_database_url_uses_env_then_default(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://a:b@c:1/d")
    assert get_database_url() == "postgresql+asyncpg://a:b@c:1/d"
    monkeypatch.delenv("DATABASE_URL")
    assert get_database_url() == to_async_url(DEFAULT_DATABASE_URL)


def revisions():
    files = sorted(p for p in VERSIONS.glob("*.py"))
    out = {}
    for p in files:
        text = p.read_text(encoding="utf-8")
        rev = re.search(r"^revision: str = '(\w+)'", text, re.M).group(1)
        down = re.search(r"^down_revision: .*= (None|'\w+')", text, re.M).group(1)
        out[p.name] = (rev, None if down == "None" else down.strip("'"))
    return out


def test_revision_files_follow_naming_convention():
    revs = revisions()
    assert revs, "phải có ít nhất một revision"
    for name, (rev, _) in revs.items():
        assert re.fullmatch(r"\d{4}_[a-z0-9]+(_[a-z0-9]+)*\.py", name), name
        assert name.startswith(rev + "_"), name


def test_revisions_are_sequential_single_chain():
    revs = list(revisions().values())
    assert [r for r, _ in revs] == ["%04d" % i for i in range(1, len(revs) + 1)]
    assert revs[0][1] is None
    for (prev, _), (_, down) in zip(revs, revs[1:]):
        assert down == prev


def test_models_register_expected_tables():
    from clinic_db import models  # noqa: F401
    from clinic_db.base import Base

    assert set(Base.metadata.tables) == {"app_info"}
