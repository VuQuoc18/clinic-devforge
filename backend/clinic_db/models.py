from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from clinic_db.base import Base


class AppInfo(Base):
    """Bảng key/value lưu metadata của ứng dụng."""

    __tablename__ = "app_info"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
