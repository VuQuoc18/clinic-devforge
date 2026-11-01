"""REQ-015: staff login at /quan-tri, separate from patient login."""
import datetime
import tempfile
import unittest

from app import accounts
from app.web import App, STAFF_COOKIE, PATIENT_COOKIE
from tests.support import SECRET, Client, migrated_db, rows

PASSWORD = "Correct-horse-1"
PHONE = "0900000001"
OTP = "123456"


class StaffLoginTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = migrated_db(self.tmp.name)
        self.now = datetime.datetime(2026, 3, 1, 10, 30, 0, tzinfo=datetime.timezone.utc)
        conn = accounts.connect(self.db)
        accounts.create_staff(conn, "staff@clinic.vn", PASSWORD, "Lan", now=self.now)
        accounts.create_patient(conn, PHONE, now=self.now)
        accounts.set_patient_otp(conn, PHONE, OTP, now=self.now)
        conn.close()
        self.app = App(self.db, SECRET, now=lambda: self.now)
        self.client = Client(self.app)

    def tearDown(self):
        self.tmp.cleanup()

    def last_login(self):
        return rows(self.db, "SELECT last_login_at FROM staff_users")[0][0]

    # --- staff success
    def test_login_page_is_served(self):
        r = self.client.get("/quan-tri/dang-nhap")
        self.assertEqual(r.status, 200)
        self.assertIn('name="email"', r.text)
        self.assertIn('name="password"', r.text)

    def test_form_login_reaches_dashboard_and_updates_last_login(self):
        self.assertIsNone(self.last_login())
        r = self.client.post_form("/quan-tri/dang-nhap", {"email": "Staff@Clinic.vn", "password": PASSWORD})
        self.assertEqual(r.status, 303)
        self.assertEqual(r.header("Location"), "/quan-tri/quan-ly")
        cookie = [v for k, v in r.headers if k == "Set-Cookie"][0]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Path=/quan-tri", cookie)
        self.assertEqual(self.last_login(), "2026-03-01T10:30:00Z")
        page = self.client.get("/quan-tri/quan-ly")
        self.assertEqual(page.status, 200)
        self.assertIn("Trang quản lý", page.text)
        self.assertIn("Lan", page.text)

    def test_api_login_returns_staff_and_sets_session(self):
        r = self.client.post_json("/quan-tri/v1/auth/login", {"email": "staff@clinic.vn", "password": PASSWORD})
        self.assertEqual(r.status, 200)
        data = r.json()["data"]
        self.assertEqual(data["email"], "staff@clinic.vn")
        self.assertEqual(data["last_login_at"], "2026-03-01T10:30:00Z")
        self.assertNotIn("password", r.text)
        self.assertEqual(self.client.get("/quan-tri/quan-ly").status, 200)

    def test_last_login_advances_on_each_login(self):
        self.client.post_json("/quan-tri/v1/auth/login", {"email": "staff@clinic.vn", "password": PASSWORD})
        self.now += datetime.timedelta(days=1)
        self.client.post_json("/quan-tri/v1/auth/login", {"email": "staff@clinic.vn", "password": PASSWORD})
        self.assertEqual(self.last_login(), "2026-03-02T10:30:00Z")

    def test_logout_ends_session(self):
        self.client.post_form("/quan-tri/dang-nhap", {"email": "staff@clinic.vn", "password": PASSWORD})
        self.client.post_form("/quan-tri/dang-xuat", {})
        r = self.client.get("/quan-tri/quan-ly")
        self.assertEqual(r.status, 303)

    # --- staff failures
    def test_wrong_password_or_unknown_email_rejected(self):
        for email, pw in [("staff@clinic.vn", "nope"), ("other@clinic.vn", PASSWORD)]:
            r = self.client.post_json("/quan-tri/v1/auth/login", {"email": email, "password": pw})
            self.assertEqual(r.status, 401)
            err = r.json()["error"]
            self.assertEqual(err["code"], "UNAUTHENTICATED")
            self.assertEqual(err["request_id"], r.header("X-Request-Id"))
            self.assertNotIn(STAFF_COOKIE, self.client.cookies)
        self.assertIsNone(self.last_login())
        r = self.client.post_form("/quan-tri/dang-nhap", {"email": "staff@clinic.vn", "password": "nope"})
        self.assertEqual(r.status, 401)
        self.assertIn("không đúng", r.text)

    def test_dashboard_requires_login(self):
        r = self.client.get("/quan-tri/quan-ly")
        self.assertEqual(r.status, 303)
        self.assertEqual(r.header("Location"), "/quan-tri/dang-nhap")

    def test_api_validation_and_bad_json(self):
        r = self.client.post_json("/quan-tri/v1/auth/login", {"email": "staff@clinic.vn"})
        self.assertEqual(r.status, 422)
        self.assertEqual(r.json()["error"]["details"][0]["field"], "password")
        r = self.client.request("POST", "/quan-tri/v1/auth/login", b"{oops", "application/json")
        self.assertEqual(r.status, 400)

    # --- domain separation
    def test_patient_phone_and_otp_rejected_at_staff_login(self):
        r = self.client.post_json("/quan-tri/v1/auth/login", {"phone": PHONE, "otp": OTP})
        self.assertEqual(r.status, 422)
        r = self.client.post_json("/quan-tri/v1/auth/login", {"email": PHONE, "password": OTP})
        self.assertEqual(r.status, 401)
        r = self.client.post_form("/quan-tri/dang-nhap", {"email": PHONE, "password": OTP})
        self.assertEqual(r.status, 401)
        self.assertEqual(self.client.get("/quan-tri/quan-ly").status, 303)

    def test_staff_email_rejected_at_patient_login(self):
        r = self.client.post_json("/v1/auth/patient/login", {"email": "staff@clinic.vn", "password": PASSWORD})
        self.assertEqual(r.status, 422)
        r = self.client.post_json("/v1/auth/patient/login", {"phone": "staff@clinic.vn", "otp": PASSWORD})
        self.assertEqual(r.status, 401)
        self.assertNotIn(PATIENT_COOKIE, self.client.cookies)
        self.assertIsNone(self.last_login())

    def test_patient_login_still_works_and_is_not_staff_session(self):
        r = self.client.post_json("/v1/auth/patient/login", {"phone": PHONE, "otp": OTP})
        self.assertEqual(r.status, 200)
        self.assertEqual(self.client.get("/v1/me").status, 200)
        # patient session grants nothing in the staff area
        self.assertEqual(self.client.get("/quan-tri/quan-ly").status, 303)

    def test_session_cookie_of_one_domain_not_accepted_by_the_other(self):
        self.client.post_json("/quan-tri/v1/auth/login", {"email": "staff@clinic.vn", "password": PASSWORD})
        staff_token = self.client.cookies[STAFF_COOKIE]
        # staff token presented as a patient cookie, and vice versa
        self.assertEqual(self.client.get("/v1/me", cookies={PATIENT_COOKIE: staff_token}).status, 401)
        self.assertEqual(self.client.get("/v1/me").status, 401)
        other = Client(self.app)
        other.post_json("/v1/auth/patient/login", {"phone": PHONE, "otp": OTP})
        patient_token = other.cookies[PATIENT_COOKIE]
        r = other.get("/quan-tri/quan-ly", cookies={STAFF_COOKIE: patient_token})
        self.assertEqual(r.status, 303)

    # --- storage
    def test_password_not_stored_in_plaintext(self):
        stored = rows(self.db, "SELECT password_hash FROM staff_users")[0][0]
        self.assertNotIn(PASSWORD, stored)
        self.assertTrue(stored.startswith("scrypt$"))
        with open(self.db, "rb") as f:
            self.assertNotIn(PASSWORD.encode(), f.read())

    def test_otp_not_stored_in_plaintext(self):
        stored = rows(self.db, "SELECT otp_hash FROM patient_otps")[0][0]
        self.assertNotEqual(stored, OTP)

    def test_unknown_route_and_method(self):
        self.assertEqual(self.client.get("/quan-tri/nope").status, 404)
        r = self.client.get("/quan-tri/v1/auth/login")
        self.assertEqual(r.status, 405)


if __name__ == "__main__":
    unittest.main()
