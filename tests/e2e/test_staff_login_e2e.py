"""E2E: run the real server and log in at /quan-tri over HTTP."""
import http.client
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse

from app import accounts
from tests.support import ROOT, migrated_db


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class StaffLoginE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = migrated_db(cls.tmp.name)
        conn = accounts.connect(db)
        accounts.create_staff(conn, "staff@clinic.vn", "Correct-horse-1", "Lan")
        conn.close()
        cls.port = free_port()
        env = dict(os.environ, AUTH_SECRET="e2e-secret", AUTH_COOKIE_SECURE="0", PYTHONPATH=ROOT)
        cls.proc = subprocess.Popen([sys.executable, "-m", "app", "--db", db, "serve", "--port", str(cls.port)],
                                    cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", cls.port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        else:
            cls.proc.kill()
            raise RuntimeError("server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=5)
        cls.tmp.cleanup()

    def http(self, method, path, body=None, cookie=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {}
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if cookie:
            headers["Cookie"] = cookie
        conn.request(method, path, urllib.parse.urlencode(body) if body is not None else None, headers)
        r = conn.getresponse()
        data = r.read().decode()
        conn.close()
        return r, data

    def test_login_flow(self):
        r, page = self.http("GET", "/quan-tri/dang-nhap")
        self.assertEqual(r.status, 200)
        self.assertIn('name="password"', page)

        r, _ = self.http("POST", "/quan-tri/dang-nhap", {"email": "staff@clinic.vn", "password": "bad"})
        self.assertEqual(r.status, 401)

        r, _ = self.http("POST", "/quan-tri/dang-nhap", {"email": "staff@clinic.vn", "password": "Correct-horse-1"})
        self.assertEqual(r.status, 303)
        self.assertEqual(r.getheader("Location"), "/quan-tri/quan-ly")
        cookie = r.getheader("Set-Cookie").split(";")[0]

        r, page = self.http("GET", "/quan-tri/quan-ly", cookie=cookie)
        self.assertEqual(r.status, 200)
        self.assertIn("Trang quản lý", page)


if __name__ == "__main__":
    unittest.main()
