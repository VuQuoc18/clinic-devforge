"""Unit: loader cấu hình theo môi trường (REQ-003)."""
import unittest

from config import ConfigError, load_settings

SMS = {"SMS_API_URL": "https://sms.test.invalid/v1", "SMS_API_KEY": "k-fake-1"}


def env(**kw):
    return {**SMS, **kw}


class LoadSettingsTest(unittest.TestCase):
    def test_default_env_is_dev(self):
        s = load_settings(env())
        self.assertEqual(s.env, "dev")

    def test_dev_values(self):
        s = load_settings(env(APP_ENV="dev"))
        self.assertEqual(s.log_level, "DEBUG")
        self.assertTrue(s.database_url.endswith("/app"))

    def test_test_values(self):
        s = load_settings(env(APP_ENV="test"))
        self.assertEqual(s.env, "test")
        self.assertEqual(s.log_level, "INFO")
        self.assertTrue(s.database_url.endswith("/app_test"))

    def test_prod_values(self):
        s = load_settings(env(APP_ENV="prod", DATABASE_URL="postgresql://p/db"))
        self.assertEqual(s.env, "prod")
        self.assertEqual(s.log_level, "WARNING")
        self.assertEqual(s.database_url, "postgresql://p/db")

    def test_prod_requires_database_url(self):
        with self.assertRaises(ConfigError) as cm:
            load_settings(env(APP_ENV="prod"))
        self.assertIn("DATABASE_URL", str(cm.exception))

    def test_prod_requires_https_sms(self):
        with self.assertRaises(ConfigError):
            load_settings(env(APP_ENV="prod", DATABASE_URL="x", SMS_API_URL="http://s.invalid"))

    def test_invalid_env_rejected(self):
        with self.assertRaises(ConfigError) as cm:
            load_settings(env(APP_ENV="staging"))
        self.assertIn("APP_ENV", str(cm.exception))

    def test_missing_sms_vars_clear_error_in_every_env(self):
        for name in ("dev", "test", "prod"):
            with self.subTest(env=name):
                with self.assertRaises(ConfigError) as cm:
                    load_settings({"APP_ENV": name, "DATABASE_URL": "x"})
                msg = str(cm.exception)
                self.assertIn("SMS_API_URL", msg)
                self.assertIn("SMS_API_KEY", msg)
                self.assertIn(name, msg)

    def test_missing_only_key(self):
        with self.assertRaises(ConfigError) as cm:
            load_settings({"SMS_API_URL": SMS["SMS_API_URL"]})
        self.assertIn("SMS_API_KEY", str(cm.exception))
        self.assertNotIn("SMS_API_URL", str(cm.exception))

    def test_blank_sms_value_is_missing(self):
        with self.assertRaises(ConfigError):
            load_settings(env(SMS_API_KEY="   "))

    def test_invalid_sms_url(self):
        with self.assertRaises(ConfigError):
            load_settings(env(SMS_API_URL="not-a-url"))

    def test_change_sms_url_and_key_only_by_env(self):
        a = load_settings(env())
        b = load_settings(env(SMS_API_URL="https://other.invalid/api", SMS_API_KEY="k-fake-2"))
        self.assertEqual((a.sms_api_url, a.sms_api_key), (SMS["SMS_API_URL"], "k-fake-1"))
        self.assertEqual((b.sms_api_url, b.sms_api_key), ("https://other.invalid/api", "k-fake-2"))

    def test_env_overrides_defaults(self):
        s = load_settings(env(APP_ENV="test", LOG_LEVEL="error", DATABASE_URL="postgresql://o/x"))
        self.assertEqual(s.log_level, "ERROR")
        self.assertEqual(s.database_url, "postgresql://o/x")

    def test_key_not_in_repr(self):
        self.assertNotIn("k-fake-1", repr(load_settings(env())))


if __name__ == "__main__":
    unittest.main()
