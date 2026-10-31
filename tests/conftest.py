import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session


def alembic_config(url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


@pytest.fixture
def db_url(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def migrated_engine(db_url):
    command.upgrade(alembic_config(db_url), "head")
    engine = create_engine(db_url)

    @event.listens_for(engine, "connect")
    def _fk(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    yield engine
    engine.dispose()


@pytest.fixture
def session(migrated_engine):
    with Session(migrated_engine) as s:
        yield s
