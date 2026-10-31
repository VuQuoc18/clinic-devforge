"""SQLAlchemy models (REQ-026): patient accounts, patient profiles, staff accounts,
plus OTP tables and counters used by the OTP tasks."""
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text,
    UniqueConstraint, false, true,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class PatientAccount(Base):
    """Tài khoản bệnh nhân."""
    __tablename__ = "patient_accounts"
    __table_args__ = (UniqueConstraint("phone", name="uq_patient_accounts_phone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    online_booking_locked: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)
    lock_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    consented_policy_version: Mapped[Optional[str]] = mapped_column(String(50))
    consented_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    profiles: Mapped[list["PatientProfile"]] = relationship(back_populates="account")


class PatientProfile(Base):
    """Hồ sơ bệnh nhân."""
    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("patient_accounts.id"), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(Text)
    relationship_to_account: Mapped[Optional[str]] = mapped_column("relationship", String(50))
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)

    account: Mapped[PatientAccount] = relationship(back_populates="profiles")


class StaffAccount(Base):
    """Tài khoản nhân viên."""
    __tablename__ = "staff_accounts"
    __table_args__ = (UniqueConstraint("email", name="uq_staff_accounts_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active", nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class OtpCode(Base):
    """Mã OTP đã phát hành (lưu hash, không lưu mã gốc)."""
    __tablename__ = "otp_codes"
    __table_args__ = (Index("ix_otp_codes_phone_created_at", "phone", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)


class OtpCounter(Base):
    """Bộ đếm theo số điện thoại và cửa sổ thời gian (số lần gửi, số lần nhập sai)."""
    __tablename__ = "otp_counters"
    __table_args__ = (
        UniqueConstraint("phone", "window_start", name="uq_otp_counters_phone_window"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    send_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
