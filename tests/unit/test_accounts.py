import datetime
import tempfile
import unittest

from app import accounts
from tests.support import migrated_db

T0 = datetime.datetime(2026, 1, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)


class AccountsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = accounts.connect(migrated_db(self.tmp.name))

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_staff_email_normalized_and_last_login_set(self):
        accounts.create_staff(self.conn, " Nurse@Clinic.VN ", "pw12345678", "Nurse", now=T0)
        later = T0 + datetime.timedelta(hours=1)
        row = accounts.authenticate_staff(self.conn, "nurse@clinic.vn", "pw12345678", now=later)
        self.assertEqual(row["email"], "nurse@clinic.vn")
        self.assertEqual(row["last_login_at"], "2026-01-01T09:00:00Z")

    def test_staff_failed_login_does_not_touch_last_login(self):
        accounts.create_staff(self.conn, "a@b.vn", "pw12345678")
        self.assertIsNone(accounts.authenticate_staff(self.conn, "a@b.vn", "bad"))
        self.assertIsNone(accounts.authenticate_staff(self.conn, "none@b.vn", "pw12345678"))
        row = self.conn.execute("SELECT last_login_at FROM staff_users").fetchone()
        self.assertIsNone(row["last_login_at"])

    def test_staff_requires_email_and_password(self):
        with self.assertRaises(ValueError):
            accounts.create_staff(self.conn, "not-an-email", "pw")
        with self.assertRaises(ValueError):
            accounts.create_staff(self.conn, "a@b.vn", "")

    def test_patient_otp_single_use_and_expiry(self):
        accounts.create_patient(self.conn, "0900000001", now=T0)
        accounts.set_patient_otp(self.conn, "0900000001", "123456", ttl_seconds=300, now=T0)
        self.assertIsNone(accounts.authenticate_patient(self.conn, "0900000001", "000000", now=T0))
        self.assertIsNotNone(accounts.authenticate_patient(self.conn, "0900000001", "123456", now=T0))
        self.assertIsNone(accounts.authenticate_patient(self.conn, "0900000001", "123456", now=T0))
        accounts.set_patient_otp(self.conn, "0900000001", "654321", ttl_seconds=300, now=T0)
        late = T0 + datetime.timedelta(seconds=301)
        self.assertIsNone(accounts.authenticate_patient(self.conn, "0900000001", "654321", now=late))

    def test_patient_unknown_phone(self):
        self.assertIsNone(accounts.authenticate_patient(self.conn, "0911111111", "123456"))


if __name__ == "__main__":
    unittest.main()
