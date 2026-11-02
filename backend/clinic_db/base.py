from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base chung cho mọi model; `Base.metadata` là nguồn của Alembic autogenerate."""
