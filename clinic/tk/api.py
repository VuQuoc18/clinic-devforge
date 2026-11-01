"""API gửi OTP có giới hạn gửi lại (REQ-003, REQ-027). WSGI thuần, chỉ dùng thư viện chuẩn.

Route (theo docs/api-conventions.md):
    POST /v1/otp-codes                      body {"phone": "..."}  -> 201 | 429
    GET  /v1/otp-resend-status?phone=...    -> 200 (cho đồng hồ đếm ngược)

Thời điểm trả về (`*_at`) là ISO-8601 theo Asia/Ho_Chi_Minh (+07:00).
"""
import json
import os
import re
import uuid
from urllib.parse import parse_qs

from clinic.tk import otp_rate_limit as rl
from clinic.tk.timefmt import TZ_NAME, to_vn_iso, utcnow

# Số di động Việt Nam (nhận được SMS): đầu số 3/5/7/8/9 + 8 chữ số, không kể tiền tố quốc gia.
VN_MOBILE_RE = re.compile(r"^[35789]\d{8}$")

_STATUS = {
    200: "200 OK", 201: "201 Created", 400: "400 Bad Request", 404: "404 Not Found",
    405: "405 Method Not Allowed", 422: "422 Unprocessable Entity", 429: "429 Too Many Requests",
    502: "502 Bad Gateway",
}


class _HttpError(Exception):
    def __init__(self, status, code, message, details=None, extra=None, headers=None):
        self.status, self.code, self.message = status, code, message
        self.details, self.extra, self.headers = details, extra or {}, headers or []


def _normalize_phone(raw):
    """Chuẩn hóa về E.164 (+84xxxxxxxxx). '0912345678', '84912345678', '+84 912 345 678'
    đều cho cùng một khóa, dùng cho giới hạn gửi và khi gọi sender."""
    if not isinstance(raw, str):
        raise _HttpError(422, "VALIDATION_FAILED", "Request validation failed.", [
            {"field": "phone", "code": "REQUIRED", "message": "Phone must be a non-empty string."}])
    phone = re.sub(r"[\s.\-]", "", raw)
    for prefix in ("+84", "84", "0"):
        if phone.startswith(prefix):
            national = phone[len(prefix):]
            break
    else:
        national = ""
    if not VN_MOBILE_RE.match(national):
        raise _HttpError(422, "VALIDATION_FAILED", "Request validation failed.", [
            {"field": "phone", "code": "INVALID_FORMAT",
             "message": "Phone is not a valid Vietnamese mobile number."}])
    return "+84" + national


def _rate_limited(decision):
    secs = decision.retry_after_seconds
    return _HttpError(
        429, "RATE_LIMITED",
        "OTP resend is not allowed yet." if decision.reason == rl.REASON_COOLDOWN
        else "OTP send limit exceeded (5 codes per 60 minutes).",
        extra={
            "reason": decision.reason,
            "retry_at": to_vn_iso(decision.retry_at),
            "retry_after_seconds": secs,
            "timezone": TZ_NAME,
        },
        headers=[("Retry-After", str(secs))])


class OtpApp:
    """`clock` trả datetime có timezone (mặc định: UTC hiện tại); test truyền đồng hồ giả lập.
    `sender(phone, sent_at)` là hook gửi SMS thực tế, chỉ được gọi khi yêu cầu được chấp nhận."""

    def __init__(self, limiter, clock=None, sender=None):
        if limiter is None:
            raise ValueError("limiter is required: OTP send history must be persisted and shared")
        self.clock = clock or utcnow
        self.limiter = limiter
        self.sender = sender

    @classmethod
    def from_database(cls, path=None, clock=None, sender=None):
        """Dựng app với lịch sử gửi lưu trong file SQLite `path` (mặc định $DATABASE_PATH).
        Thiếu cấu hình thì báo lỗi thay vì lặng lẽ dùng DB tạm trong bộ nhớ."""
        path = path or os.environ.get("DATABASE_PATH")
        if not path:
            raise ValueError("database path is required (argument or DATABASE_PATH)")
        clock = clock or utcnow
        return cls(rl.OtpRateLimiter(rl.SqliteOtpSendStore.open(path), clock), clock, sender)

    # --- handlers ---
    def _create(self, environ):
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
            body = json.loads(environ["wsgi.input"].read(length) or b"")
            if not isinstance(body, dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            raise _HttpError(400, "INVALID_REQUEST", "Body must be a JSON object.")
        phone = _normalize_phone(body.get("phone"))
        d = self.limiter.request_send(phone)
        if not d.allowed:
            raise _rate_limited(d)
        if self.sender:
            try:
                self.sender(phone, d.sent_at)
            except Exception:
                # SMS chưa gửi được: hoàn lại lần gửi để người dùng không bị trừ hạn mức.
                self.limiter.cancel_send(d)
                raise _HttpError(502, "OTP_SEND_FAILED",
                                 "OTP could not be delivered. Please try again.")
        return 201, {"data": {
            "phone": phone,
            "sent_at": to_vn_iso(d.sent_at),
            "resend_available_at": to_vn_iso(d.next_resend_at),
            "resend_after_seconds": d.retry_after_seconds,
            "remaining_in_window": d.remaining_in_window,
            "timezone": TZ_NAME,
        }}

    def _status(self, environ):
        qs = parse_qs(environ.get("QUERY_STRING", ""))
        phone = _normalize_phone((qs.get("phone") or [None])[0])
        d = self.limiter.status(phone)
        data = {
            "phone": phone,
            "can_resend": d.allowed,
            "retry_after_seconds": d.retry_after_seconds,
            "retry_at": to_vn_iso(d.retry_at) if d.retry_at else None,
            "reason": d.reason,
            "remaining_in_window": d.remaining_in_window,
            "timezone": TZ_NAME,
        }
        return 200, {"data": data}

    # --- WSGI ---
    def __call__(self, environ, start_response):
        request_id = environ.get("HTTP_X_REQUEST_ID") or "req_" + uuid.uuid4().hex[:8]
        headers = []
        try:
            method, path = environ["REQUEST_METHOD"], environ.get("PATH_INFO", "")
            routes = {"/v1/otp-codes": ("POST", self._create),
                      "/v1/otp-resend-status": ("GET", self._status)}
            if path not in routes:
                raise _HttpError(404, "RESOURCE_NOT_FOUND", "Route %s was not found." % path)
            allowed, handler = routes[path]
            if method != allowed:
                raise _HttpError(405, "METHOD_NOT_ALLOWED", "Use %s." % allowed,
                                 headers=[("Allow", allowed)])
            status, payload = handler(environ)
        except _HttpError as e:
            status, headers = e.status, e.headers
            err = {"code": e.code, "message": e.message}
            if e.details:
                err["details"] = e.details
            err.update(e.extra)
            err["request_id"] = request_id
            payload = {"error": err}
        body = json.dumps(payload).encode("utf-8")
        start_response(_STATUS[status], [("Content-Type", "application/json"),
                                         ("Content-Length", str(len(body))),
                                         ("X-Request-Id", request_id)] + headers)
        return [body]
