"""Cấu hình theo môi trường dev/test/prod, đọc từ biến môi trường (REQ-003).

Môi trường chọn bằng ``APP_ENV`` (dev | test | prod; mặc định dev).
Địa chỉ và khóa cổng SMS lấy từ ``SMS_API_URL`` và ``SMS_API_KEY`` — bắt buộc ở mọi
môi trường, không có giá trị mặc định trong code. Client cổng SMS dùng ``load_settings()``.
"""
import os
from dataclasses import dataclass, field
from urllib.parse import urlparse

ENVIRONMENTS = ("dev", "test", "prod")
DEFAULT_ENV = "dev"

# Giá trị mặc định riêng từng môi trường (không chứa bí mật).
# None = bắt buộc phải đặt bằng biến môi trường.
_ENV_DEFAULTS = {
    "dev": {
        "DATABASE_URL": "postgresql://app:app@127.0.0.1:5442/app",
        "LOG_LEVEL": "DEBUG",
    },
    "test": {
        "DATABASE_URL": "postgresql://app:app@127.0.0.1:5442/app_test",
        "LOG_LEVEL": "INFO",
    },
    "prod": {
        "DATABASE_URL": None,
        "LOG_LEVEL": "WARNING",
    },
}

_REQUIRED_SMS = ("SMS_API_URL", "SMS_API_KEY")


class ConfigError(ValueError):
    """Cấu hình thiếu hoặc không hợp lệ; thông báo nêu rõ tên biến và môi trường."""


@dataclass(frozen=True)
class Settings:
    env: str
    database_url: str
    log_level: str
    sms_api_url: str
    sms_api_key: str = field(repr=False)  # không lộ khóa trong log/repr


def _get(environ, name):
    value = environ.get(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def load_settings(environ=None):
    """Đọc cấu hình từ ``environ`` (mặc định ``os.environ``)."""
    environ = os.environ if environ is None else environ

    env = (_get(environ, "APP_ENV") or DEFAULT_ENV).lower()
    if env not in ENVIRONMENTS:
        raise ConfigError(
            "APP_ENV=%r không hợp lệ; chỉ chấp nhận: %s" % (env, ", ".join(ENVIRONMENTS))
        )

    defaults = _ENV_DEFAULTS[env]
    values = {}
    missing = []
    for name in _REQUIRED_SMS:
        value = _get(environ, name)
        if value is None:
            missing.append(name)
        values[name] = value
    for name, default in defaults.items():
        value = _get(environ, name) or default
        if value is None:
            missing.append(name)
        values[name] = value
    if missing:
        raise ConfigError(
            "Thiếu biến môi trường bắt buộc cho môi trường %s: %s"
            % (env, ", ".join(missing))
        )

    url = urlparse(values["SMS_API_URL"])
    if url.scheme not in ("http", "https") or not url.netloc:
        raise ConfigError("SMS_API_URL phải là URL http(s) hợp lệ")
    if env == "prod" and url.scheme != "https":
        raise ConfigError("SMS_API_URL ở môi trường prod phải dùng https")

    return Settings(
        env=env,
        database_url=values["DATABASE_URL"],
        log_level=values["LOG_LEVEL"].upper(),
        sms_api_url=values["SMS_API_URL"],
        sms_api_key=values["SMS_API_KEY"],
    )
