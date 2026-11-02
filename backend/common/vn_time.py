"""Tiện ích thời gian dùng chung cho mô-đun TK (REQ-027).

Quy ước:
- Mọi thời điểm lưu/tính toán là datetime *aware* ở UTC.
- Chỉ đổi sang Asia/Ho_Chi_Minh khi hiển thị (`format_vn`) hoặc khi tính mốc
  theo ngày giờ Việt Nam (`daily_cutoff_after`, `daily_cutoff_on_or_before`).
- Đồng hồ giả lập được: `now()` đọc từ một clock thay thế được bằng
  `set_clock` / `use_clock` / `FixedClock`.
"""
from __future__ import annotations

import contextlib
from datetime import datetime, time, timedelta, timezone
from typing import Callable, Iterator, Optional, Union

try:
    from zoneinfo import ZoneInfo

    VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except Exception:  # pragma: no cover - môi trường thiếu tzdata
    # Việt Nam dùng UTC+7 cố định từ 1975, nên offset cố định là tương đương.
    VN_TZ = timezone(timedelta(hours=7), "Asia/Ho_Chi_Minh")

UTC = timezone.utc
DISPLAY_FORMAT = "%H:%M %d/%m/%Y"
CUTOFF_TIME = time(23, 59)

Clock = Callable[[], datetime]


def _system_clock() -> datetime:
    return datetime.now(UTC)


_clock: Clock = _system_clock


def to_utc(dt: datetime) -> datetime:
    """Chuẩn hóa về UTC. datetime naive bị từ chối để tránh nhầm múi giờ."""
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("datetime phải có múi giờ (aware)")
    return dt.astimezone(UTC)


def now() -> datetime:
    """Thời điểm hiện tại (UTC, aware) theo clock hiện hành."""
    return to_utc(_clock())


def set_clock(clock: Optional[Clock]) -> None:
    """Đặt clock giả lập; truyền None để về đồng hồ hệ thống."""
    global _clock
    _clock = clock if clock is not None else _system_clock


@contextlib.contextmanager
def use_clock(clock: Union[Clock, datetime]) -> Iterator[None]:
    """Dùng clock (hoặc một thời điểm cố định) trong phạm vi `with`."""
    global _clock
    previous = _clock
    _clock = FixedClock(clock) if isinstance(clock, datetime) else clock
    try:
        yield
    finally:
        _clock = previous


class FixedClock:
    """Clock giả lập cho test: đứng yên, có thể `set` hoặc `advance`."""

    def __init__(self, current: datetime):
        self._current = to_utc(current)

    def __call__(self) -> datetime:
        return self._current

    def set(self, current: datetime) -> None:
        self._current = to_utc(current)

    def advance(self, delta: timedelta) -> None:
        self._current = self._current + delta


def add_duration(dt: datetime, delta: timedelta) -> datetime:
    """Cộng khoảng thời gian vào thời điểm; kết quả ở UTC."""
    return to_utc(dt) + delta


def to_vn(dt: datetime) -> datetime:
    """Đổi sang giờ Việt Nam (chỉ dùng để hiển thị/tính theo ngày VN)."""
    return to_utc(dt).astimezone(VN_TZ)


def format_vn(dt: datetime, fmt: str = DISPLAY_FORMAT) -> str:
    """Định dạng hiển thị theo Asia/Ho_Chi_Minh, vd 16:30 UTC -> '23:30 ...'."""
    return to_vn(dt).strftime(fmt)


def daily_cutoff_after(dt: datetime) -> datetime:
    """Mốc 23:59 (giờ VN) đầu tiên *sau hẳn* `dt`, trả về ở UTC.

    Đúng 23:59:00 giờ VN thì trả mốc của ngày hôm sau.
    """
    local = to_vn(dt)
    cutoff = datetime.combine(local.date(), CUTOFF_TIME, tzinfo=VN_TZ)
    if cutoff <= local:
        cutoff = datetime.combine(
            local.date() + timedelta(days=1), CUTOFF_TIME, tzinfo=VN_TZ
        )
    return cutoff.astimezone(UTC)


def daily_cutoff_on_or_before(dt: datetime) -> datetime:
    """Mốc 23:59 (giờ VN) gần nhất không sau `dt`, trả về ở UTC."""
    return daily_cutoff_after(dt) - timedelta(days=1)
