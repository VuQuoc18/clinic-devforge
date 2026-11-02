"""Kết nối DB với thời gian lưu/đọc theo múi giờ mặc định (REQ-004).

SQLite (dev/test): datetime được lưu dạng ISO-8601 kèm offset của Asia/Ho_Chi_Minh
vào cột khai báo kiểu TIMESTAMP, đọc ra là datetime aware cùng múi giờ.
PostgreSQL: dùng `postgres_connect_kwargs()` để phiên DB đặt timezone đúng.
"""
import sqlite3
from datetime import datetime

from app import config, timeutil


def _adapt(dt):
    return timeutil.isoformat(dt)  # từ chối datetime naive


def _convert(raw):
    return timeutil.parse(raw.decode("utf-8"))


sqlite3.register_adapter(datetime, _adapt)
sqlite3.register_converter("TIMESTAMP", _convert)


def connect(path):
    return sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)


def postgres_connect_kwargs(env=None):
    """Kwargs cho psycopg/libpq: `psycopg.connect(url, **postgres_connect_kwargs())`."""
    return {"options": config.get_settings(env).postgres_options}
