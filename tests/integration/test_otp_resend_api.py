"""REQ-003 / REQ-027: API gửi OTP với đồng hồ giả lập (integration, qua WSGI)."""
import io
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from clinic.tk import otp_rate_limit as rl
from clinic.tk.api import OtpApp


class Client:
    def __init__(self, app):
        self.app = app

    def call(self, method, path, body=None, query=""):
        raw = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
                   "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw)}
        out = {}

        def start_response(status, headers):
            out["status"] = int(status.split()[0])
            out["headers"] = dict(headers)

        data = b"".join(self.app(environ, start_response))
        return out["status"], out["headers"], json.loads(data)

    def send(self, phone="0912345678"):
        return self.call("POST", "/v1/otp-codes", {"phone": phone})

    def status(self, phone="0912345678"):
        return self.call("GET", "/v1/otp-resend-status", query="phone=" + phone)


class OtpResendApiTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.sent = []
        self.app = OtpApp(clock=lambda: self.now, sender=lambda p, t: self.sent.append(p))
        self.api = Client(self.app)

    def advance(self, **kw):
        self.now += timedelta(**kw)

    def test_first_send_returns_countdown(self):
        status, headers, body = self.api.send()
        self.assertEqual(status, 201)
        d = body["data"]
        self.assertEqual(d["resend_after_seconds"], 60)
        self.assertEqual(d["sent_at"], "2025-01-01T07:00:00+07:00")
        self.assertEqual(d["resend_available_at"], "2025-01-01T07:01:00+07:00")
        self.assertEqual(d["timezone"], "Asia/Ho_Chi_Minh")
        self.assertEqual(d["remaining_in_window"], 4)
        self.assertEqual(self.sent, ["0912345678"])

    def test_resend_before_60s_rejected_with_remaining_time(self):
        self.api.send()
        self.advance(seconds=45)
        status, headers, body = self.api.send()
        self.assertEqual(status, 429)
        err = body["error"]
        self.assertEqual(err["code"], "RATE_LIMITED")
        self.assertEqual(err["reason"], rl.REASON_COOLDOWN)
        self.assertEqual(err["retry_after_seconds"], 15)
        self.assertEqual(headers["Retry-After"], "15")
        self.assertEqual(err["retry_at"], "2025-01-01T07:01:00+07:00")
        self.assertEqual(headers["X-Request-Id"], err["request_id"])
        self.assertEqual(len(self.sent), 1)  # không gửi SMS khi bị từ chối

    def test_resend_at_60s_accepted(self):
        self.api.send()
        self.advance(seconds=60)
        status, _, _ = self.api.send()
        self.assertEqual(status, 201)
        self.assertEqual(len(self.sent), 2)

    def test_sixth_code_within_60_minutes_rejected_with_vn_time(self):
        for i in range(5):
            if i:
                self.advance(seconds=60)
            self.assertEqual(self.api.send()[0], 201)
        self.advance(seconds=60)  # 00:05 UTC
        status, headers, body = self.api.send()
        self.assertEqual(status, 429)
        err = body["error"]
        self.assertEqual(err["reason"], rl.REASON_LIMIT)
        self.assertEqual(err["retry_at"], "2025-01-01T08:00:00+07:00")
        self.assertEqual(err["retry_after_seconds"], 55 * 60)
        self.assertEqual(err["timezone"], "Asia/Ho_Chi_Minh")
        self.assertEqual(len(self.sent), 5)

        # tới giờ được gửi lại thì gửi được
        self.now = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(self.api.send()[0], 201)

    def test_status_endpoint_countdown(self):
        status, _, body = self.api.status()
        self.assertEqual(status, 200)
        self.assertTrue(body["data"]["can_resend"])
        self.assertEqual(body["data"]["retry_after_seconds"], 0)

        self.api.send()
        self.advance(seconds=20)
        d = self.api.status()[2]["data"]
        self.assertFalse(d["can_resend"])
        self.assertEqual(d["retry_after_seconds"], 40)
        self.assertEqual(d["retry_at"], "2025-01-01T07:01:00+07:00")
        self.assertEqual(d["reason"], rl.REASON_COOLDOWN)

        self.advance(seconds=40)
        d = self.api.status()[2]["data"]
        self.assertTrue(d["can_resend"])
        self.assertEqual(d["retry_after_seconds"], 0)
        self.assertIsNone(d["retry_at"])

    def test_limit_is_per_phone(self):
        self.api.send("0912345678")
        self.assertEqual(self.api.send("0912345678")[0], 429)
        self.assertEqual(self.api.send("0987654321")[0], 201)

    def test_phone_formatting_is_normalized(self):
        self.api.send("0912 345 678")
        self.assertEqual(self.api.send("0912345678")[0], 429)

    def test_validation_errors(self):
        status, _, body = self.api.call("POST", "/v1/otp-codes", {"phone": "abc"})
        self.assertEqual((status, body["error"]["code"]), (422, "VALIDATION_FAILED"))
        self.assertEqual(body["error"]["details"][0]["field"], "phone")
        status, _, body = self.api.call("POST", "/v1/otp-codes", {})
        self.assertEqual(status, 422)
        status, _, body = self.api.call("POST", "/v1/otp-codes", b"not json")
        self.assertEqual((status, body["error"]["code"]), (400, "INVALID_REQUEST"))
        status, _, body = self.api.call("GET", "/v1/otp-resend-status")
        self.assertEqual(status, 422)

    def test_unknown_route_and_method(self):
        self.assertEqual(self.api.call("GET", "/v1/nope")[0], 404)
        status, headers, _ = self.api.call("GET", "/v1/otp-codes")
        self.assertEqual((status, headers["Allow"]), (405, "POST"))

    def test_history_persists_in_database_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "otp.db")
            clock = lambda: self.now  # noqa: E731
            app1 = OtpApp(rl.OtpRateLimiter(rl.SqliteOtpSendStore.open(path), clock), clock)
            Client(app1).send()
            app2 = OtpApp(rl.OtpRateLimiter(rl.SqliteOtpSendStore.open(path), clock), clock)
            self.assertEqual(Client(app2).send()[0], 429)


if __name__ == "__main__":
    unittest.main()
