"""Giới hạn gửi lại OTP theo số điện thoại (REQ-003, BR-TK-02).

- Gửi lại chỉ được sau 60 giây kể từ lần gửi trước (tại đúng 60 giây là được).
- Tối đa 5 mã trong 60 phút liên tiếp (cửa sổ trượt); yêu cầu thứ 6 bị từ chối
  kèm thời điểm được gửi lại.
Yêu cầu bị từ chối không được ghi nhận là một lần gửi.
"""
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from db import migrate

RESEND_COOLDOWN = timedelta(seconds=60)
WINDOW = timedelta(minutes=60)
MAX_PER_WINDOW = 5

REASON_COOLDOWN = "OTP_RESEND_TOO_EARLY"
REASON_LIMIT = "OTP_SEND_LIMIT_EXCEEDED"


def _to_ms(dt):
    return int(dt.timestamp() * 1000)


def _from_ms(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    now: datetime
    reason: Optional[str] = None
    retry_at: Optional[datetime] = None  # UTC; khi bị từ chối
    sent_at: Optional[datetime] = None  # khi được gửi
    next_resend_at: Optional[datetime] = None  # thời điểm sớm nhất được gửi lại sau quyết định này
    remaining_in_window: int = 0
    record_id: Optional[int] = None  # id bản ghi gửi, dùng cho cancel_send

    @property
    def retry_after_seconds(self):
        """Số giây còn lại (làm tròn lên) tới thời điểm được gửi lại, cho đồng hồ đếm ngược."""
        target = self.retry_at if not self.allowed else self.next_resend_at
        if target is None:
            return 0
        secs = (target - self.now).total_seconds()
        return max(0, int(-(-secs // 1)))


class SqliteOtpSendStore:
    """Nhật ký gửi OTP trong bảng otp_sends (migration 0002)."""

    def __init__(self, conn):
        self.conn = conn
        self.lock = threading.RLock()

    @classmethod
    def open(cls, path):
        """Mở (và migrate) DB tại `path`. `path` bắt buộc; ":memory:" chỉ nên dùng trong test."""
        conn = migrate.connect(path, check_same_thread=False)
        migrate.up(conn, migrate.discover())
        return cls(conn)

    @contextmanager
    def transaction(self):
        """Khóa ghi (BEGIN IMMEDIATE) để kiểm tra-rồi-ghi là nguyên tử giữa các tiến trình/kết nối."""
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                yield
            except BaseException:
                if self.conn.in_transaction:
                    self.conn.execute("ROLLBACK")
                raise
            self.conn.execute("COMMIT")

    def sends_since(self, phone, since):
        rows = self.conn.execute(
            "SELECT sent_at FROM otp_sends WHERE phone = ? AND sent_at > ? ORDER BY sent_at",
            (phone, _to_ms(since)))
        return [_from_ms(r[0]) for r in rows]

    def record(self, phone, at):
        cur = self.conn.execute("INSERT INTO otp_sends (phone, sent_at) VALUES (?, ?)",
                                (phone, _to_ms(at)))
        return cur.lastrowid

    def delete(self, record_id):
        self.conn.execute("DELETE FROM otp_sends WHERE id = ?", (record_id,))


class OtpRateLimiter:
    def __init__(self, store, clock):
        self.store = store
        self.clock = clock

    def _evaluate(self, phone, now):
        recent = self.store.sends_since(phone, now - WINDOW)  # tăng dần theo thời gian
        retry_at = None
        reason = None
        if len(recent) >= MAX_PER_WINDOW:
            # Mã cũ nhất trong số MAX_PER_WINDOW mã gần nhất rời cửa sổ thì được gửi lại.
            retry_at = recent[-MAX_PER_WINDOW] + WINDOW
            reason = REASON_LIMIT
        if recent and now - recent[-1] < RESEND_COOLDOWN:
            cooldown_end = recent[-1] + RESEND_COOLDOWN
            if retry_at is None or cooldown_end > retry_at:
                retry_at = cooldown_end
            reason = reason or REASON_COOLDOWN
        return recent, reason, retry_at

    def status(self, phone):
        """Trạng thái hiện tại (không ghi nhận lần gửi)."""
        with self.store.lock:
            now = self.clock()
            recent, reason, retry_at = self._evaluate(phone, now)
            remaining = max(0, MAX_PER_WINDOW - len(recent))
            if reason:
                return Decision(False, now, reason, retry_at, remaining_in_window=remaining)
            return Decision(True, now, remaining_in_window=remaining, next_resend_at=now)

    def request_send(self, phone):
        """Kiểm tra và, nếu được phép, ghi nhận một lần gửi OTP."""
        with self.store.transaction():
            now = self.clock()
            recent, reason, retry_at = self._evaluate(phone, now)
            remaining = max(0, MAX_PER_WINDOW - len(recent))
            if reason:
                return Decision(False, now, reason, retry_at, remaining_in_window=remaining)
            record_id = self.store.record(phone, now)
            next_at = now + RESEND_COOLDOWN
            if len(recent) + 1 >= MAX_PER_WINDOW:
                next_at = max(next_at, recent[-(MAX_PER_WINDOW - 1)] + WINDOW)
            return Decision(True, now, sent_at=now, next_resend_at=next_at,
                            remaining_in_window=remaining - 1, record_id=record_id)

    def cancel_send(self, decision):
        """Hoàn lại một lần gửi đã ghi nhận (khi gửi SMS thất bại)."""
        if decision.record_id is not None:
            with self.store.lock:
                self.store.delete(decision.record_id)
