"""REQ-003 / REQ-027: giới hạn gửi lại OTP (unit)."""
import os
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone

from clinic.tk import otp_rate_limit as rl
from clinic.tk.timefmt import to_vn_iso


class FakeClock:
    def __init__(self, start=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, **kw):
        self.now += timedelta(**kw)


class OtpRateLimiterTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.limiter = rl.OtpRateLimiter(rl.SqliteOtpSendStore.open(":memory:"), self.clock)
        self.phone = "0912345678"

    def send_five(self):
        """5 mã cách nhau 60 giây: t = 0, 60, 120, 180, 240."""
        for i in range(5):
            if i:
                self.clock.advance(seconds=60)
            self.assertTrue(self.limiter.request_send(self.phone).allowed)

    def test_first_request_allowed(self):
        d = self.limiter.request_send(self.phone)
        self.assertTrue(d.allowed)
        self.assertEqual(d.next_resend_at, self.clock.now + timedelta(seconds=60))
        self.assertEqual(d.retry_after_seconds, 60)
        self.assertEqual(d.remaining_in_window, 4)

    def test_rejected_before_60_seconds(self):
        self.limiter.request_send(self.phone)
        self.clock.advance(seconds=59, milliseconds=999)
        d = self.limiter.request_send(self.phone)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, rl.REASON_COOLDOWN)
        self.assertEqual(d.retry_at, datetime(2025, 1, 1, 0, 1, 0, tzinfo=timezone.utc))
        self.assertEqual(d.retry_after_seconds, 1)

    def test_accepted_at_exactly_60_seconds(self):
        self.limiter.request_send(self.phone)
        self.clock.advance(seconds=60)
        self.assertTrue(self.limiter.request_send(self.phone).allowed)

    def test_rejected_request_does_not_restart_cooldown(self):
        self.limiter.request_send(self.phone)
        self.clock.advance(seconds=30)
        self.assertFalse(self.limiter.request_send(self.phone).allowed)
        self.clock.advance(seconds=30)  # tổng 60 giây kể từ lần gửi thành công
        self.assertTrue(self.limiter.request_send(self.phone).allowed)

    def test_first_five_allowed_sixth_rejected_with_retry_time(self):
        self.send_five()  # t=240s
        self.clock.advance(seconds=60)  # t=300s, qua cooldown
        d = self.limiter.request_send(self.phone)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, rl.REASON_LIMIT)
        first_send = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(d.retry_at, first_send + timedelta(minutes=60))
        self.assertEqual(d.retry_after_seconds, 3300)

    def test_allowed_again_when_oldest_leaves_window(self):
        self.send_five()
        self.clock.now = datetime(2025, 1, 1, 0, 59, 59, tzinfo=timezone.utc)
        self.assertFalse(self.limiter.request_send(self.phone).allowed)
        self.clock.now = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(self.limiter.request_send(self.phone).allowed)

    def test_fifth_send_reports_next_resend_at_window_end(self):
        # 5 mã dồn sát nhau để cooldown 60s kéo dài hơn cửa sổ
        for i in range(4):
            self.limiter.request_send(self.phone)
            self.clock.advance(seconds=60)
        d = self.limiter.request_send(self.phone)
        self.assertTrue(d.allowed)
        self.assertEqual(d.remaining_in_window, 0)
        self.assertEqual(d.next_resend_at, datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc))

    def test_limits_are_per_phone(self):
        self.limiter.request_send(self.phone)
        self.assertTrue(self.limiter.request_send("0987654321").allowed)

    def test_retry_time_in_ho_chi_minh(self):
        self.send_five()
        self.clock.advance(seconds=60)
        d = self.limiter.request_send(self.phone)
        # 00:00 UTC + 60 phút = 01:00 UTC = 08:00 giờ Việt Nam
        self.assertEqual(to_vn_iso(d.retry_at), "2025-01-01T08:00:00+07:00")

    def test_status_does_not_record(self):
        self.assertTrue(self.limiter.status(self.phone).allowed)
        self.assertTrue(self.limiter.status(self.phone).allowed)
        self.assertEqual(self.limiter.request_send(self.phone).remaining_in_window, 4)
        s = self.limiter.status(self.phone)
        self.assertFalse(s.allowed)
        self.assertEqual(s.retry_after_seconds, 60)

    def test_window_slides(self):
        # 2 mã đầu rồi chờ; mã cũ nhất rời cửa sổ thì trừ vào hạn mức
        self.limiter.request_send(self.phone)  # t=0
        self.clock.advance(minutes=30)
        self.limiter.request_send(self.phone)  # t=30m
        self.clock.advance(minutes=31)  # t=61m: chỉ còn mã t=30m trong cửa sổ
        d = self.limiter.request_send(self.phone)
        self.assertTrue(d.allowed)
        self.assertEqual(d.remaining_in_window, 3)


    def test_window_boundary_exactly_60_minutes(self):
        # 5 mã dồn trong 4 phút đầu: t=0,1,2,3,4 phút
        for _ in range(5):
            self.assertTrue(self.limiter.request_send(self.phone).allowed)
            self.clock.advance(minutes=1)
        t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
        # còn 1 ms nữa mã đầu (t=0) rời cửa sổ -> vẫn bị từ chối, retry_at = t0 + 60 phút
        self.clock.now = t0 + timedelta(minutes=60) - timedelta(milliseconds=1)
        d = self.limiter.request_send(self.phone)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, rl.REASON_LIMIT)
        self.assertEqual(d.retry_at, t0 + timedelta(minutes=60))
        # đúng now - 60 phút == mã đầu: mã đó đã ra khỏi cửa sổ -> được gửi
        self.clock.now = t0 + timedelta(minutes=60)
        self.assertTrue(self.limiter.request_send(self.phone).allowed)
        # t=61 phút: mã t=1 phút vừa rời cửa sổ (đúng biên) -> còn 4 mã trong cửa sổ, được gửi
        self.clock.now = t0 + timedelta(minutes=61)
        d = self.limiter.request_send(self.phone)
        self.assertTrue(d.allowed)
        self.assertEqual(d.remaining_in_window, 0)

    def test_cancel_send_refunds_quota(self):
        d = self.limiter.request_send(self.phone)
        self.limiter.cancel_send(d)
        self.assertTrue(self.limiter.request_send(self.phone).allowed)


class ConcurrencyTest(unittest.TestCase):
    """Hai store (hai kết nối) trỏ cùng một file DB: kiểm tra-rồi-ghi phải nguyên tử."""

    def _run_concurrently(self, limiters, phone, attempts=8):
        results, barrier = [], threading.Barrier(len(limiters) * attempts)

        def worker(limiter):
            barrier.wait()
            results.append(limiter.request_send(phone).allowed)

        threads = [threading.Thread(target=worker, args=(lim,))
                   for lim in limiters for _ in range(attempts)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return results

    def test_concurrent_requests_respect_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "otp.db")
            now = datetime(2025, 1, 1, tzinfo=timezone.utc)
            limiters = [rl.OtpRateLimiter(rl.SqliteOtpSendStore.open(path), lambda: now)
                        for _ in range(2)]
            results = self._run_concurrently(limiters, "+84912345678")
            self.assertEqual(results.count(True), 1)

    def test_concurrent_requests_respect_window_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "otp.db")
            t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
            store = rl.SqliteOtpSendStore.open(path)
            for i in range(4):  # 4 mã trước đó, cách nhau 2 phút
                store.record("+84912345678", t0 + timedelta(minutes=2 * i))
            now = t0 + timedelta(minutes=10)
            limiters = [rl.OtpRateLimiter(rl.SqliteOtpSendStore.open(path), lambda: now)
                        for _ in range(2)]
            results = self._run_concurrently(limiters, "+84912345678")
            self.assertEqual(results.count(True), 1)
            self.assertEqual(len(store.sends_since("+84912345678", t0 - timedelta(days=1))), 5)


class TimeFormatTest(unittest.TestCase):
    def test_utc_converted_to_vn(self):
        dt = datetime(2025, 6, 30, 17, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(to_vn_iso(dt), "2025-07-01T00:30:00+07:00")

    def test_other_offset_converted_to_vn(self):
        dt = datetime(2025, 1, 1, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
        self.assertEqual(to_vn_iso(dt), "2025-01-01T12:00:00+07:00")

    def test_naive_rejected(self):
        with self.assertRaises(ValueError):
            to_vn_iso(datetime(2025, 1, 1))


if __name__ == "__main__":
    unittest.main()
