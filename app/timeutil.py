"""Tiện ích thời gian (#2). Múi giờ lấy từ cấu hình chung `app.config`.

Mọi giá trị trả về là datetime có múi giờ (aware); không bao giờ dùng giờ địa phương
của máy chủ.
"""
from datetime import datetime, timedelta, timezone

from app import config


def tz():
    return config.get_settings().tzinfo


def now():
    """Thời điểm hiện tại theo múi giờ mặc định."""
    return datetime.now(tz())


def to_local(dt):
    """Đổi datetime aware sang múi giờ mặc định. Datetime naive bị từ chối."""
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("naive datetime is not allowed; attach a timezone first")
    return dt.astimezone(tz())


def localize(dt):
    """Gắn múi giờ mặc định cho datetime naive (giờ treo tường theo múi giờ mặc định)."""
    if dt.tzinfo is not None:
        raise ValueError("datetime is already timezone-aware")
    return dt.replace(tzinfo=tz())


def to_utc(dt):
    return to_local(dt).astimezone(timezone.utc)


def at_local(year, month, day, hour=0, minute=0, second=0):
    """Mốc giờ treo tường theo múi giờ mặc định (vd. job 23:00)."""
    return datetime(year, month, day, hour, minute, second, tzinfo=tz())


def isoformat(dt):
    return to_local(dt).isoformat()


def parse(text):
    """Đọc chuỗi ISO-8601; chuỗi không có offset được coi là giờ theo múi giờ mặc định."""
    dt = datetime.fromisoformat(text)
    return to_local(dt) if dt.tzinfo else localize(dt)


def minutes_from_now(minutes, base=None):
    """Mốc cách `base` (mặc định: bây giờ) một số phút, ví dụ -60 / +15."""
    base = now() if base is None else to_local(base)
    return base + timedelta(minutes=minutes)
