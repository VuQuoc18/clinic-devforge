"""Cấu hình hệ thống (REQ-004): múi giờ mặc định Asia/Ho_Chi_Minh.

Nguồn duy nhất của múi giờ là `config/timezone.json`; frontend, backend, DB và
tiện ích thời gian (`app/timeutil.py`) đều đọc từ đó. Múi giờ KHÔNG phụ thuộc
múi giờ của máy chủ (biến TZ / giờ hệ điều hành).
"""
import json
import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEZONE_FILE = os.path.join(ROOT, "config", "timezone.json")
ENVIRONMENTS = ("dev", "test", "prod")
DEFAULT_ENV = "dev"


def _load_default_timezone():
    with open(TIMEZONE_FILE, encoding="utf-8") as f:
        name = json.load(f)["default_timezone"]
    ZoneInfo(name)  # fail fast nếu tên múi giờ sai
    return name


DEFAULT_TIMEZONE = _load_default_timezone()


@dataclass(frozen=True)
class Settings:
    env: str
    timezone: str

    @property
    def tzinfo(self):
        return ZoneInfo(self.timezone)

    @property
    def postgres_options(self):
        """Tham số `options` của libpq để phiên DB dùng cùng múi giờ."""
        return "-c timezone=%s" % self.timezone


def get_settings(env=None):
    """Trả về cấu hình cho `env` (mặc định: $APP_ENV, rồi `dev`)."""
    env = env or os.environ.get("APP_ENV") or DEFAULT_ENV
    if env not in ENVIRONMENTS:
        raise ValueError("unknown environment %r (expected one of %s)" % (env, ENVIRONMENTS))
    return Settings(env=env, timezone=DEFAULT_TIMEZONE)
