#!/usr/bin/env python3
"""Migration runner (REQ-008). Conventions: docs/db-migrations.md.

Usage:
    python3 db/migrate.py up      [--db PATH] [--dir DIR] [--target VERSION]
    python3 db/migrate.py down    [--db PATH] [--dir DIR] [--steps N]
    python3 db/migrate.py status  [--db PATH] [--dir DIR]

The DB path defaults to $DATABASE_PATH. Only the Python standard library is used
(SQLite driver).
"""
import argparse
import hashlib
import os
import re
import sqlite3
import sys

DEFAULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")
NAME_RE = re.compile(r"^(\d{4})_([a-z0-9]+(?:_[a-z0-9]+)*)\.(up|down)\.sql$")
TABLE = "schema_migrations"


class MigrationError(Exception):
    pass


class Migration:
    def __init__(self, version, name, up_path, down_path=None):
        self.version = version
        self.name = name
        self.up_path = up_path
        self.down_path = down_path

    def read(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    @property
    def checksum(self):
        return hashlib.sha256(self.read(self.up_path).encode("utf-8")).hexdigest()


def discover(directory=DEFAULT_DIR):
    """Return migrations sorted by version; validate naming rules."""
    found = {}
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".sql"):
            continue
        m = NAME_RE.match(fname)
        if not m:
            raise MigrationError("invalid migration file name: %s" % fname)
        version, name, kind = m.groups()
        entry = found.setdefault(version, {"name": name})
        if entry["name"] != name:
            raise MigrationError("version %s used by different names" % version)
        if kind in entry:
            raise MigrationError("duplicate %s for version %s" % (kind, version))
        entry[kind] = os.path.join(directory, fname)
    migrations = []
    for version in sorted(found):
        e = found[version]
        if "up" not in e:
            raise MigrationError("version %s has .down.sql but no .up.sql" % version)
        migrations.append(Migration(version, e["name"], e["up"], e.get("down")))
    versions = [int(m.version) for m in migrations]
    if versions != list(range(1, len(versions) + 1)):
        raise MigrationError("versions must be contiguous starting at 0001: %s" % versions)
    return migrations


def connect(path):
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS %s ("
        "version TEXT PRIMARY KEY, name TEXT NOT NULL, checksum TEXT NOT NULL, "
        "applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)" % TABLE
    )
    return conn


def applied(conn):
    return {r[0]: (r[1], r[2]) for r in conn.execute(
        "SELECT version, name, checksum FROM %s ORDER BY version" % TABLE)}


def _run_script(conn, script, record_sql, params):
    """Run script + bookkeeping in one transaction (rolled back on failure)."""
    try:
        conn.execute("BEGIN")
        for stmt in _split(script):
            conn.execute(stmt)
        conn.execute(record_sql, params)
        conn.execute("COMMIT")
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise


def _split(script):
    stmts, buf = [], ""
    for line in script.splitlines(keepends=True):
        buf += line
        if sqlite3.complete_statement(buf):
            if buf.strip():
                stmts.append(buf.strip())
            buf = ""
    if buf.strip():
        raise MigrationError("incomplete SQL statement (missing ';'): %r" % buf.strip()[:60])
    return stmts


def up(conn, migrations, target=None):
    done = applied(conn)
    for m in migrations:
        if m.version in done and done[m.version][1] != m.checksum:
            raise MigrationError("applied migration %s was modified (checksum mismatch)" % m.version)
    for v in done:
        if v not in {m.version for m in migrations}:
            raise MigrationError("applied version %s missing from migrations dir" % v)
    ran = []
    for m in migrations:
        if m.version in done:
            continue
        if target and m.version > target:
            break
        try:
            _run_script(conn, m.read(m.up_path),
                        "INSERT INTO %s (version, name, checksum) VALUES (?,?,?)" % TABLE,
                        (m.version, m.name, m.checksum))
        except Exception as e:
            raise MigrationError("migration %s_%s failed: %s" % (m.version, m.name, e))
        ran.append(m)
    return ran


def down(conn, migrations, steps=1):
    done = applied(conn)
    by_version = {m.version: m for m in migrations}
    ran = []
    for v in sorted(done, reverse=True)[:steps]:
        m = by_version.get(v)
        if m is None or m.down_path is None:
            raise MigrationError("migration %s has no .down.sql; cannot roll back" % v)
        try:
            _run_script(conn, m.read(m.down_path),
                        "DELETE FROM %s WHERE version = ?" % TABLE, (v,))
        except Exception as e:
            raise MigrationError("rollback %s_%s failed: %s" % (m.version, m.name, e))
        ran.append(m)
    return ran


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("command", choices=["up", "down", "status"])
    p.add_argument("--db", default=os.environ.get("DATABASE_PATH"))
    p.add_argument("--dir", default=DEFAULT_DIR)
    p.add_argument("--target")
    p.add_argument("--steps", type=int, default=1)
    a = p.parse_args(argv)
    if not a.db:
        p.error("--db or DATABASE_PATH is required")
    try:
        migrations = discover(a.dir)
        conn = connect(a.db)
        if a.command == "up":
            ran = up(conn, migrations, a.target)
            for m in ran:
                print("applied %s_%s" % (m.version, m.name))
            if not ran:
                print("nothing to apply")
        elif a.command == "down":
            for m in down(conn, migrations, a.steps):
                print("rolled back %s_%s" % (m.version, m.name))
        else:
            done = applied(conn)
            for m in migrations:
                print("%s %s_%s" % ("applied" if m.version in done else "pending", m.version, m.name))
    except MigrationError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
