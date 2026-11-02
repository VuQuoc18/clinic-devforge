"""REQ-004: PostgreSQL local dùng múi giờ Asia/Ho_Chi_Minh (cần Docker, tự bỏ qua nếu không có)."""
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "clinic-tz-it"
PORT = "55443"


def docker_ok():
    return shutil.which("docker") is not None and subprocess.run(
        ["docker", "info"], capture_output=True).returncode == 0


@unittest.skipUnless(docker_ok(), "Docker không khả dụng")
class PostgresTimezoneTest(unittest.TestCase):
    def sh(self, *cmd):
        env = {**os.environ, "DB_PORT": PORT, "COMPOSE_PROJECT_NAME": PROJECT}
        return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=240)

    def tearDown(self):
        self.sh("docker", "compose", "down", "-v")

    def test_db_timezone(self):
        up = self.sh("docker", "compose", "up", "-d", "--wait")
        self.assertEqual(up.returncode, 0, up.stderr)
        q = self.sh("docker", "compose", "exec", "-T", "db", "psql", "-U", "app", "-d", "app", "-tAc",
                    "SHOW timezone; SELECT to_char(TIMESTAMPTZ '2024-01-01 16:00+00', 'YYYY-MM-DD HH24:MI')")
        self.assertEqual(q.returncode, 0, q.stderr)
        self.assertEqual(q.stdout.split(), ["Asia/Ho_Chi_Minh", "2024-01-01", "23:00"])


if __name__ == "__main__":
    unittest.main()
