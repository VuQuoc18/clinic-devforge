"""Test helpers: migrated temp DB and a minimal in-process WSGI client."""
import io
import json
import os
import sqlite3
import sys
import tempfile
import urllib.parse
from http.cookies import SimpleCookie

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "db"))
import migrate  # noqa: E402

SECRET = "test-secret"


def migrated_db(directory):
    path = os.path.join(directory, "test.db")
    conn = migrate.connect(path)
    migrate.up(conn, migrate.discover())
    conn.close()
    return path


def rows(db_path, sql, *params):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


class Response:
    def __init__(self, status, headers, body):
        self.status = int(status.split()[0])
        self.headers = headers
        self.text = body.decode("utf-8")

    def header(self, name):
        return next((v for k, v in self.headers if k.lower() == name.lower()), None)

    def json(self):
        return json.loads(self.text)

    def set_cookies(self):
        out = {}
        for k, v in self.headers:
            if k.lower() == "set-cookie":
                jar = SimpleCookie()
                jar.load(v)
                out.update({n: m.value for n, m in jar.items()})
        return out


class Client:
    def __init__(self, app):
        self.app = app
        self.cookies = {}

    def request(self, method, path, body=b"", content_type=None, cookies=None):
        jar = self.cookies if cookies is None else cookies
        environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "SERVER_NAME": "t", "SERVER_PORT": "80",
                   "wsgi.input": io.BytesIO(body), "CONTENT_LENGTH": str(len(body)),
                   "wsgi.url_scheme": "http"}
        if content_type:
            environ["CONTENT_TYPE"] = content_type
        if jar:
            environ["HTTP_COOKIE"] = "; ".join("%s=%s" % kv for kv in jar.items())
        captured = {}

        def start_response(status, headers):
            captured["s"], captured["h"] = status, headers

        body_out = b"".join(self.app(environ, start_response))
        resp = Response(captured["s"], captured["h"], body_out)
        if cookies is None:
            for k, v in resp.set_cookies().items():
                if v:
                    self.cookies[k] = v
                else:
                    self.cookies.pop(k, None)
        return resp

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post_json(self, path, data, **kw):
        return self.request("POST", path, json.dumps(data).encode(), "application/json", **kw)

    def post_form(self, path, data, **kw):
        return self.request("POST", path, urllib.parse.urlencode(data).encode(),
                            "application/x-www-form-urlencoded", **kw)
