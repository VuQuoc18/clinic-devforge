"""WSGI app: staff login under /quan-tri and patient login, as separate auth domains (REQ-015).

Staff:    GET/POST /quan-tri/dang-nhap, GET /quan-tri/quan-ly, POST /quan-tri/v1/auth/login
Patient:  POST /v1/auth/patient/login (phone + otp), GET /v1/me
Each domain has its own cookie, signing key and token audience, so a session or credential
from one domain is never accepted by the other.
"""
import html
import json
import urllib.parse
import uuid
from http.cookies import SimpleCookie

from app import accounts, security

STAFF_PREFIX = "/quan-tri"
STAFF_COOKIE = "staff_session"
PATIENT_COOKIE = "patient_session"
SESSION_TTL = 8 * 3600
MAX_BODY = 64 * 1024

_STATUS = {200: "OK", 303: "See Other", 400: "Bad Request", 401: "Unauthorized",
           404: "Not Found", 405: "Method Not Allowed", 413: "Payload Too Large",
           422: "Unprocessable Entity"}


class _Request:
    def __init__(self, environ):
        self.environ = environ
        self.method = environ["REQUEST_METHOD"].upper()
        self.path = environ.get("PATH_INFO", "/")
        self.request_id = "req_" + uuid.uuid4().hex[:8]
        jar = SimpleCookie()
        try:
            jar.load(environ.get("HTTP_COOKIE", ""))
        except Exception:
            pass
        self.cookies = {k: m.value for k, m in jar.items()}

    def body(self):
        try:
            length = int(self.environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        if length > MAX_BODY:
            raise _HttpError(413, "INVALID_REQUEST", "Request body too large.")
        return self.environ["wsgi.input"].read(length) if length else b""

    def json(self):
        try:
            data = json.loads(self.body() or b"")
        except ValueError:
            raise _HttpError(400, "INVALID_REQUEST", "Body must be valid JSON.")
        if not isinstance(data, dict):
            raise _HttpError(400, "INVALID_REQUEST", "Body must be a JSON object.")
        return data

    def form(self):
        parsed = urllib.parse.parse_qs(self.body().decode("utf-8", "replace"))
        return {k: v[0] for k, v in parsed.items()}


class _HttpError(Exception):
    def __init__(self, status, code, message, details=None):
        self.status, self.code, self.message, self.details = status, code, message, details


def _response(req, status, body, content_type, headers=()):
    if isinstance(body, str):
        body = body.encode("utf-8")
    hdrs = [("Content-Type", content_type), ("Content-Length", str(len(body))),
            ("X-Request-Id", req.request_id), ("Cache-Control", "no-store")]
    hdrs.extend(headers)
    return "%d %s" % (status, _STATUS[status]), hdrs, [body]


def _json(req, status, payload, headers=()):
    return _response(req, status, json.dumps(payload), "application/json; charset=utf-8", headers)


def _error(req, err):
    error = {"code": err.code, "message": err.message}
    if err.details:
        error["details"] = err.details
    error["request_id"] = req.request_id
    return _json(req, err.status, {"error": error})


def _page(req, status, title, body_html, headers=()):
    doc = ("<!doctype html><html lang=\"vi\"><head><meta charset=\"utf-8\"><title>%s</title></head>"
           "<body>%s</body></html>" % (html.escape(title), body_html))
    return _response(req, status, doc, "text/html; charset=utf-8", headers)


def _redirect(req, location, headers=()):
    return _response(req, 303, "", "text/plain; charset=utf-8", [("Location", location), *headers])


def _require_strings(data, fields):
    details = [{"field": f, "code": "REQUIRED", "message": "%s must be a non-empty string." % f}
               for f in fields if not isinstance(data.get(f), str) or not data[f].strip()]
    if details:
        raise _HttpError(422, "VALIDATION_FAILED", "Request validation failed.", details)


_BAD_CREDENTIALS = ("UNAUTHENTICATED", "Invalid credentials.")


class App:
    def __init__(self, db_path, secret, cookie_secure=True, now=None):
        if not secret:
            raise ValueError("secret is required")
        self.db_path, self.secret, self.cookie_secure = db_path, secret, cookie_secure
        self.now = now  # optional callable returning aware datetime (tests)

    # -- helpers
    def _now(self):
        return self.now() if self.now else None

    def _cookie(self, name, value, path, max_age):
        parts = ["%s=%s" % (name, value), "Path=" + path, "HttpOnly", "SameSite=Lax", "Max-Age=%d" % max_age]
        if self.cookie_secure:
            parts.append("Secure")
        return ("Set-Cookie", "; ".join(parts))

    def _staff_cookie(self, value, max_age=SESSION_TTL):
        return self._cookie(STAFF_COOKIE, value, STAFF_PREFIX, max_age)

    def _patient_cookie(self, value, max_age=SESSION_TTL):
        return self._cookie(PATIENT_COOKIE, value, "/", max_age)

    def _current_staff(self, conn, req):
        token = req.cookies.get(STAFF_COOKIE)
        sub = security.read_session(self.secret, "staff", token) if token else None
        return accounts.get_staff(conn, sub) if sub is not None else None

    def _current_patient(self, conn, req):
        token = req.cookies.get(PATIENT_COOKIE)
        sub = security.read_session(self.secret, "patient", token) if token else None
        return accounts.get_patient(conn, sub) if sub is not None else None

    # -- WSGI
    def __call__(self, environ, start_response):
        req = _Request(environ)
        conn = accounts.connect(self.db_path)
        try:
            try:
                status, headers, body = self._dispatch(req, conn)
            except _HttpError as err:
                status, headers, body = _error(req, err)
        finally:
            conn.close()
        start_response(status, headers)
        return body

    def _dispatch(self, req, conn):
        routes = {
            STAFF_PREFIX: {"GET": self.staff_root},
            STAFF_PREFIX + "/": {"GET": self.staff_root},
            STAFF_PREFIX + "/dang-nhap": {"GET": self.staff_login_page, "POST": self.staff_login_form},
            STAFF_PREFIX + "/quan-ly": {"GET": self.staff_dashboard},
            STAFF_PREFIX + "/dang-xuat": {"POST": self.staff_logout},
            STAFF_PREFIX + "/v1/auth/login": {"POST": self.staff_login_api},
            "/v1/auth/patient/login": {"POST": self.patient_login_api},
            "/v1/me": {"GET": self.patient_me},
        }
        methods = routes.get(req.path)
        if methods is None:
            raise _HttpError(404, "RESOURCE_NOT_FOUND", "Route not found.")
        handler = methods.get(req.method)
        if handler is None:
            raise _HttpError(405, "METHOD_NOT_ALLOWED", "Method not allowed.")
        return handler(req, conn)

    # -- staff
    def _login_form_html(self, error=""):
        msg = '<p role="alert">%s</p>' % html.escape(error) if error else ""
        return ('<h1>Đăng nhập nhân viên</h1>%s<form method="post" action="%s/dang-nhap">'
                '<label>Email <input type="email" name="email" required></label>'
                '<label>Mật khẩu <input type="password" name="password" required></label>'
                '<button type="submit">Đăng nhập</button></form>' % (msg, STAFF_PREFIX))

    def staff_root(self, req, conn):
        target = "/quan-tri/quan-ly" if self._current_staff(conn, req) else "/quan-tri/dang-nhap"
        return _redirect(req, target)

    def staff_login_page(self, req, conn):
        if self._current_staff(conn, req):
            return _redirect(req, STAFF_PREFIX + "/quan-ly")
        return _page(req, 200, "Đăng nhập nhân viên", self._login_form_html())

    def _staff_session_for(self, conn, email, password):
        staff = accounts.authenticate_staff(conn, email, password, now=self._now())
        if staff is None:
            return None, None
        token = security.sign_session(self.secret, "staff", staff["id"], SESSION_TTL)
        return staff, self._staff_cookie(token)

    def staff_login_form(self, req, conn):
        form = req.form()
        staff, cookie = self._staff_session_for(conn, form.get("email", ""), form.get("password", ""))
        if staff is None:
            return _page(req, 401, "Đăng nhập nhân viên",
                         self._login_form_html("Email hoặc mật khẩu không đúng."))
        return _redirect(req, STAFF_PREFIX + "/quan-ly", [cookie])

    def staff_login_api(self, req, conn):
        data = req.json()
        _require_strings(data, ["email", "password"])
        staff, cookie = self._staff_session_for(conn, data["email"], data["password"])
        if staff is None:
            raise _HttpError(401, *_BAD_CREDENTIALS)
        return _json(req, 200, {"data": {"id": staff["id"], "email": staff["email"],
                                         "full_name": staff["full_name"],
                                         "last_login_at": staff["last_login_at"]}}, [cookie])

    def staff_dashboard(self, req, conn):
        staff = self._current_staff(conn, req)
        if staff is None:
            return _redirect(req, STAFF_PREFIX + "/dang-nhap")
        name = staff["full_name"] or staff["email"]
        return _page(req, 200, "Quản lý",
                     '<h1>Trang quản lý</h1><p>Xin chào, %s</p>'
                     '<form method="post" action="%s/dang-xuat"><button type="submit">Đăng xuất</button></form>'
                     % (html.escape(name), STAFF_PREFIX))

    def staff_logout(self, req, conn):
        return _redirect(req, STAFF_PREFIX + "/dang-nhap", [self._staff_cookie("", 0)])

    # -- patient
    def patient_login_api(self, req, conn):
        data = req.json()
        _require_strings(data, ["phone", "otp"])
        patient = accounts.authenticate_patient(conn, data["phone"], data["otp"], now=self._now())
        if patient is None:
            raise _HttpError(401, *_BAD_CREDENTIALS)
        token = security.sign_session(self.secret, "patient", patient["id"], SESSION_TTL)
        return _json(req, 200, {"data": {"id": patient["id"], "phone": patient["phone"]}},
                     [self._patient_cookie(token)])

    def patient_me(self, req, conn):
        patient = self._current_patient(conn, req)
        if patient is None:
            raise _HttpError(401, "UNAUTHENTICATED", "Authentication required.")
        return _json(req, 200, {"data": {"id": patient["id"], "phone": patient["phone"]}})
