"""Integration: loader chạy trong process riêng với os.environ thật; repo sạch khóa (REQ-003)."""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SNIPPET = "from config import load_settings as l; s=l(); print(s.env, s.sms_api_url, s.sms_api_key)"


def run_py(extra):
    base = {k: v for k, v in os.environ.items()
            if not k.startswith(("SMS_", "APP_ENV", "DATABASE_URL", "LOG_LEVEL"))}
    return subprocess.run([sys.executable, "-c", SNIPPET], cwd=ROOT, env={**base, **extra},
                          capture_output=True, text=True)


class ConfigProcessTest(unittest.TestCase):
    def test_sms_change_only_via_environment(self):
        r1 = run_py({"SMS_API_URL": "https://a.invalid", "SMS_API_KEY": "k1"})
        r2 = run_py({"SMS_API_URL": "https://b.invalid", "SMS_API_KEY": "k2"})
        self.assertEqual(r1.stdout.split(), ["dev", "https://a.invalid", "k1"], r1.stderr)
        self.assertEqual(r2.stdout.split(), ["dev", "https://b.invalid", "k2"], r2.stderr)

    def test_missing_sms_fails_with_clear_message(self):
        r = run_py({})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ConfigError", r.stderr)
        self.assertIn("SMS_API_URL", r.stderr)

    def test_env_files_ignored_and_example_clean(self):
        ignore = open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read().split()
        self.assertIn(".env", ignore)
        example = open(os.path.join(ROOT, ".env.example"), encoding="utf-8").read()
        self.assertIn("SMS_API_URL=", example)
        self.assertIn("SMS_API_KEY=changeme", example)
        self.assertFalse(os.path.exists(os.path.join(ROOT, ".env")) and
                         self._tracked(".env"))

    def _tracked(self, path):
        r = subprocess.run(["git", "ls-files", path], cwd=ROOT, capture_output=True, text=True)
        return bool(r.stdout.strip())

    def test_no_real_secret_in_tracked_files(self):
        r = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode != 0:
            self.skipTest("không phải git repo")
        pat = re.compile(r"(?m)^\s*(?:export\s+)?SMS_API_KEY=(?!changeme\s*$|\$|\s*$)\S+")
        for f in r.stdout.split("\n"):
            p = os.path.join(ROOT, f)
            if not f or f.startswith("tests/") or not os.path.isfile(p):
                continue
            try:
                text = open(p, encoding="utf-8").read()
            except UnicodeDecodeError:
                continue
            self.assertIsNone(pat.search(text), "khóa SMS nghi ngờ trong " + f)


if __name__ == "__main__":
    unittest.main()
