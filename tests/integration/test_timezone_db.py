"""REQ-004: thời gian lưu/đọc qua DB và hiển thị theo Asia/Ho_Chi_Minh dù máy chủ đặt TZ khác."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCRIPT = r"""
import sys
from datetime import datetime, timezone
from app import db, timeutil

conn = db.connect(sys.argv[1])
conn.execute("CREATE TABLE IF NOT EXISTS appt (id INTEGER PRIMARY KEY, at TIMESTAMP NOT NULL)")
utc = datetime(2024, 1, 1, 16, 0, tzinfo=timezone.utc)   # = 23:00 giờ VN
conn.execute("INSERT INTO appt (at) VALUES (?)", (utc,))
conn.execute("INSERT INTO appt (at) VALUES (?)", (timeutil.at_local(2024, 6, 1, 23, 0),))
conn.commit()
raw = [r[0] for r in conn.execute("SELECT CAST(at AS TEXT) FROM appt ORDER BY id")]
vals = [r[0] for r in conn.execute("SELECT at FROM appt ORDER BY id")]
print("|".join(raw))
print("|".join(v.isoformat() for v in vals))
print(timeutil.now().utcoffset())
try:
    conn.execute("INSERT INTO appt (at) VALUES (?)", (datetime(2024, 1, 1, 23, 0),))
    print("naive-accepted")
except ValueError:
    print("naive-rejected")
"""


class TimezoneDbTest(unittest.TestCase):
    def run_with_tz(self, tz, env_name="prod"):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, APP_ENV=env_name, PYTHONPATH=ROOT)
            if tz is None:
                env.pop("TZ", None)
            else:
                env["TZ"] = tz
            r = subprocess.run([sys.executable, "-c", SCRIPT, os.path.join(tmp, "t.db")],
                               capture_output=True, text=True, env=env, cwd=ROOT)
            self.assertEqual(r.returncode, 0, r.stderr)
            return r.stdout.strip().splitlines()

    def test_store_and_read_in_ho_chi_minh_regardless_of_server_tz(self):
        expected = [
            "2024-01-01T23:00:00+07:00|2024-06-01T23:00:00+07:00",
            "2024-01-01T23:00:00+07:00|2024-06-01T23:00:00+07:00",
            "7:00:00",
            "naive-rejected",
        ]
        for tz in ("UTC", "America/New_York", "Asia/Tokyo", None):
            for env_name in ("dev", "test", "prod"):
                with self.subTest(tz=tz, env=env_name):
                    self.assertEqual(self.run_with_tz(tz, env_name), expected)


if __name__ == "__main__":
    unittest.main()
