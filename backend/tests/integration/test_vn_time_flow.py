"""Integration: luồng điển hình của OTP/khóa/phiên dùng vn_time (REQ-027)."""
from datetime import datetime, timedelta, timezone

from common import vn_time

UTC = timezone.utc


def test_lockout_retry_time_displayed_in_vn():
    """Khóa 15 phút (BR-TK-06): lưu UTC, hiển thị giờ VN."""
    clock = vn_time.FixedClock(datetime(2026, 11, 1, 16, 50, tzinfo=UTC))
    with vn_time.use_clock(clock):
        locked_until = vn_time.add_duration(vn_time.now(), timedelta(minutes=15))
    assert locked_until == datetime(2026, 11, 1, 17, 5, tzinfo=UTC)  # lưu UTC
    assert vn_time.format_vn(locked_until) == "00:05 02/11/2026"  # hiển thị VN


def test_resend_time_after_clock_advance():
    """Giờ được gửi lại (BR-TK-02) tính từ đồng hồ giả lập đã tiến lên."""
    clock = vn_time.FixedClock(datetime(2026, 11, 1, 10, 0, tzinfo=UTC))
    with vn_time.use_clock(clock):
        first = vn_time.now()
        clock.advance(timedelta(minutes=30))
        resend_at = vn_time.add_duration(first, timedelta(minutes=60))
        assert vn_time.now() < resend_at
        clock.advance(timedelta(minutes=31))
        assert vn_time.now() > resend_at
    assert vn_time.format_vn(resend_at) == "18:00 01/11/2026"


def test_daily_reset_boundary_with_clock():
    clock = vn_time.FixedClock(datetime(2026, 11, 1, 16, 58, tzinfo=UTC))
    with vn_time.use_clock(clock):
        cutoff = vn_time.daily_cutoff_after(vn_time.now())
        assert vn_time.now() < cutoff
        clock.advance(timedelta(minutes=1))
        assert vn_time.now() >= cutoff
        assert vn_time.daily_cutoff_after(vn_time.now()) == cutoff + timedelta(days=1)
