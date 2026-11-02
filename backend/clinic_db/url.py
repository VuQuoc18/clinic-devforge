"""Chuẩn hóa DATABASE_URL cho SQLAlchemy async (driver asyncpg)."""
import os

# Khớp README / docker-compose.yml (môi trường local).
DEFAULT_DATABASE_URL = "postgresql://app:app@127.0.0.1:5442/app"

_PREFIXES = ("postgresql+asyncpg://", "postgresql://", "postgres://")


def to_async_url(url: str) -> str:
    """Đổi URL PostgreSQL dạng `postgresql://...` sang `postgresql+asyncpg://...`."""
    if url.startswith(_PREFIXES[0]):
        return url
    for prefix in _PREFIXES[1:]:
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix):]
    raise ValueError("DATABASE_URL phải là URL PostgreSQL (postgresql://...)")


def get_database_url() -> str:
    return to_async_url(os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
