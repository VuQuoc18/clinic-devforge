"""Hiển thị thời điểm theo giờ Việt Nam (REQ-027)."""
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except Exception:  # thiếu tzdata: Việt Nam cố định UTC+7, không có DST
    VN_TZ = timezone(timedelta(hours=7), "Asia/Ho_Chi_Minh")

TZ_NAME = "Asia/Ho_Chi_Minh"


def to_vn_iso(dt):
    """Trả chuỗi ISO-8601 theo Asia/Ho_Chi_Minh (offset +07:00), làm tròn tới giây."""
    if dt.tzinfo is None:
        raise ValueError("naive datetime is not allowed")
    return dt.astimezone(VN_TZ).replace(microsecond=0).isoformat()


def utcnow():
    return datetime.now(timezone.utc)
