"""Unit: tiện ích thời gian Asia/Ho_Chi_Minh (REQ-027)."""
from datetime import datetime, timedelta, timezone

import pytest

from common import vn_time

UTC = timezone.utc


def utc(*args):
    return datetime(*args, tzinfo=UTC)


def test_format_utc_to_vn_same_day():
    assert vn_time.format_vn(utc(2026, 11, 1, 16, 30)) == "23:30 01/11/2026"


def test_format_utc_to_vn_next_day():
    assert vn_time.format_vn(utc(2026, 11, 1, 17, 0)) == "00:00 02/11/2026"


def test_format_accepts_other_timezone_input():
    plus9 = timezone(timedelta(hours=9))
    dt = datetime(2026, 11, 2, 1, 30, tzinfo=plus9)  # = 16:30 UTC
    assert vn_time.format_vn(dt) == "23:30 01/11/2026"


def test_format_custom_format():
    assert vn_time.format_vn(utc(2026, 11, 1, 16, 30), "%H:%M") == "23:30"


def test_naive_datetime_rejected():
    with pytest.raises(ValueError):
        vn_time.format_vn(datetime(2026, 11, 1, 16, 30))
    with pytest.raises(ValueError):
        vn_time.add_duration(datetime(2026, 11, 1), timedelta(minutes=1))


def test_add_duration_stays_utc():
    r = vn_time.add_duration(utc(2026, 11, 1, 16, 50), timedelta(minutes=15))
    assert r == utc(2026, 11, 1, 17, 5)
    assert r.utcoffset() == timedelta(0)


def test_to_vn_offset_is_plus_7():
    assert vn_time.to_vn(utc(2026, 1, 1)).utcoffset() == timedelta(hours=7)


# --- đồng hồ giả lập ---

def test_now_is_aware_utc_by_default():
    n = vn_time.now()
    assert n.utcoffset() == timedelta(0)


def test_use_clock_with_datetime_and_restores():
    fixed = utc(2026, 11, 1, 16, 30)
    with vn_time.use_clock(fixed):
        assert vn_time.now() == fixed
    assert vn_time.now() != fixed


def test_fixed_clock_advance_and_set():
    clock = vn_time.FixedClock(utc(2026, 11, 1, 0, 0))
    with vn_time.use_clock(clock):
        clock.advance(timedelta(hours=1))
        assert vn_time.now() == utc(2026, 11, 1, 1, 0)
        clock.set(utc(2027, 1, 1))
        assert vn_time.now() == utc(2027, 1, 1)


def test_set_clock_and_reset():
    vn_time.set_clock(lambda: utc(2026, 5, 5, 5, 5))
    try:
        assert vn_time.now() == utc(2026, 5, 5, 5, 5)
    finally:
        vn_time.set_clock(None)
    assert vn_time.now().year >= 2025


def test_now_normalizes_clock_to_utc():
    plus7 = timezone(timedelta(hours=7))
    with vn_time.use_clock(lambda: datetime(2026, 11, 1, 23, 30, tzinfo=plus7)):
        assert vn_time.now() == utc(2026, 11, 1, 16, 30)
        assert vn_time.now().utcoffset() == timedelta(0)


# --- mốc 23:59 ---

def test_cutoff_midday_vn():
    # 05:00 UTC = 12:00 VN -> 23:59 VN cùng ngày = 16:59 UTC
    assert vn_time.daily_cutoff_after(utc(2026, 11, 1, 5, 0)) == utc(2026, 11, 1, 16, 59)


def test_cutoff_around_utc_midnight():
    # 23:30 UTC = 06:30 VN ngày 02/11 -> mốc 02/11 23:59 VN = 02/11 16:59 UTC
    assert vn_time.daily_cutoff_after(utc(2026, 11, 1, 23, 30)) == utc(2026, 11, 2, 16, 59)
    # 00:30 UTC = 07:30 VN cùng ngày
    assert vn_time.daily_cutoff_after(utc(2026, 11, 2, 0, 30)) == utc(2026, 11, 2, 16, 59)


def test_cutoff_around_vn_midnight():
    # 16:58 UTC = 23:58 VN -> mốc ngay sau 1 phút
    assert vn_time.daily_cutoff_after(utc(2026, 11, 1, 16, 58)) == utc(2026, 11, 1, 16, 59)
    # đúng 23:59 VN -> mốc ngày kế tiếp
    assert vn_time.daily_cutoff_after(utc(2026, 11, 1, 16, 59)) == utc(2026, 11, 2, 16, 59)
    # 17:00 UTC = 00:00 VN ngày 02/11 -> mốc 02/11 23:59 VN
    assert vn_time.daily_cutoff_after(utc(2026, 11, 1, 17, 0)) == utc(2026, 11, 2, 16, 59)


def test_cutoff_displays_as_2359_vn():
    for dt in (utc(2026, 11, 1, 5, 0), utc(2026, 11, 1, 16, 58), utc(2026, 11, 1, 23, 30)):
        assert vn_time.format_vn(vn_time.daily_cutoff_after(dt), "%H:%M") == "23:59"


def test_cutoff_on_or_before():
    assert vn_time.daily_cutoff_on_or_before(utc(2026, 11, 1, 16, 59)) == utc(2026, 11, 1, 16, 59)
    assert vn_time.daily_cutoff_on_or_before(utc(2026, 11, 1, 16, 58)) == utc(2026, 10, 31, 16, 59)
    assert vn_time.daily_cutoff_on_or_before(utc(2026, 11, 1, 17, 0)) == utc(2026, 11, 1, 16, 59)


def test_cutoff_result_is_utc():
    assert vn_time.daily_cutoff_after(utc(2026, 11, 1)).utcoffset() == timedelta(0)


def test_cutoff_with_fake_clock():
    with vn_time.use_clock(utc(2026, 11, 1, 16, 58)):
        assert vn_time.daily_cutoff_after(vn_time.now()) == utc(2026, 11, 1, 16, 59)
