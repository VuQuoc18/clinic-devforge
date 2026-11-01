"""CLI: `python3 -m app serve` and `python3 -m app create-staff EMAIL`.

Env: DATABASE_PATH (default app.db), AUTH_SECRET (required to serve),
AUTH_COOKIE_SECURE=0 to allow cookies over plain HTTP in local dev.
"""
import argparse
import getpass
import os
import sys
from wsgiref.simple_server import make_server

from app import accounts
from app.web import App


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m app")
    parser.add_argument("--db", default=os.environ.get("DATABASE_PATH", "app.db"))
    sub = parser.add_subparsers(dest="cmd", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    cs = sub.add_parser("create-staff")
    cs.add_argument("email")
    cs.add_argument("--full-name", default="")
    args = parser.parse_args(argv)

    if args.cmd == "create-staff":
        password = os.environ.get("STAFF_PASSWORD") or getpass.getpass("Password: ")
        conn = accounts.connect(args.db)
        try:
            accounts.create_staff(conn, args.email, password, args.full_name)
        finally:
            conn.close()
        print("created staff %s" % accounts.normalize_email(args.email))
        return 0

    secret = os.environ.get("AUTH_SECRET")
    if not secret:
        print("AUTH_SECRET is required", file=sys.stderr)
        return 2
    secure = os.environ.get("AUTH_COOKIE_SECURE", "1") != "0"
    app = App(args.db, secret, cookie_secure=secure)
    with make_server(args.host, args.port, app) as httpd:
        print("serving on http://%s:%d" % (args.host, args.port))
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
