"""REQ-004: múi giờ mặc định Asia/Ho_Chi_Minh ở dev/test/prod và dùng chung với timeutil."""
import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app import config, timeutil

ROOT = config.ROOT
HCM = "Asia/Ho_Chi_Minh"


class TimezoneConfigTest(unittest.TestCase):
    def test_default_is_ho_chi_minh_in_every_environment(self):
        self.assertEqual(config.ENVIRONMENTS, ("dev", "test", "prod"))
        for env in config.ENVIRONMENTS:
            self.assertEqual(config.get_settings(env).timezone, HCM, env)

    def test_env_from_app_env_variable(self):
        old = os.environ.get("APP_ENV")
        try:
            for env in config.ENVIRONMENTS:
                os.environ["APP_ENV"] = env
                s = config.get_settings()
                self.assertEqual((s.env, s.timezone), (env, HCM))
        finally:
            if old is None:
                os.environ.pop("APP_ENV", None)
            else:
                os.environ["APP_ENV"] = old

    def test_unknown_env_rejected(self):
        with self.assertRaises(ValueError):
            config.get_settings("staging")

    def test_single_source_file_used_by_frontend_and_backend(self):
        with open(os.path.join(ROOT, "config", "timezone.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["default_timezone"], HCM)
        self.assertEqual(config.DEFAULT_TIMEZONE, HCM)

    def test_postgres_session_options(self):
        self.assertEqual(config.get_settings("prod").postgres_options, "-c timezone=" + HCM)

    def test_compose_db_uses_ho_chi_minh(self):
        with open(os.path.join(ROOT, "docker-compose.yml"), encoding="utf-8") as f:
            compose = f.read()
        self.assertIn("timezone=" + HCM, compose)
        self.assertIn("TZ: " + HCM, compose)


class TimeUtilUsesSharedConfigTest(unittest.TestCase):
    def test_tz_comes_from_config(self):
        self.assertEqual(str(timeutil.tz()), HCM)
        self.assertEqual(timeutil.tz(), config.get_settings().tzinfo)

    def test_now_is_aware_and_plus_7(self):
        n = timeutil.now()
        self.assertEqual(n.utcoffset(), timedelta(hours=7))

    def test_to_local_from_utc(self):
        dt = datetime(2024, 1, 1, 16, 0, tzinfo=timezone.utc)
        self.assertEqual(timeutil.to_local(dt).isoformat(), "2024-01-01T23:00:00+07:00")

    def test_naive_rejected_by_to_local_and_localize_attaches_tz(self):
        with self.assertRaises(ValueError):
            timeutil.to_local(datetime(2024, 1, 1))
        self.assertEqual(timeutil.localize(datetime(2024, 1, 1, 23)).isoformat(),
                         "2024-01-01T23:00:00+07:00")

    def test_parse_without_offset_is_local(self):
        self.assertEqual(timeutil.parse("2024-05-05T23:00").utcoffset(), timedelta(hours=7))
        self.assertEqual(timeutil.parse("2024-05-05T16:00:00+00:00").hour, 23)

    def test_offsets_minus_60_plus_15(self):
        base = timeutil.at_local(2024, 3, 3, 9, 0)
        self.assertEqual(timeutil.minutes_from_now(-60, base).isoformat(), "2024-03-03T08:00:00+07:00")
        self.assertEqual(timeutil.minutes_from_now(15, base).isoformat(), "2024-03-03T09:15:00+07:00")

    def test_changing_config_changes_timeutil(self):
        orig = config.get_settings
        try:
            config.get_settings = lambda env=None: config.Settings("test", "UTC")
            self.assertEqual(timeutil.now().utcoffset(), timedelta(0))
        finally:
            config.get_settings = orig


if __name__ == "__main__":
    unittest.main()
