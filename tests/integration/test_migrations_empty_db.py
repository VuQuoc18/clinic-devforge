"""REQ-008: apply every real migration onto an empty DB and verify the schema."""
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "db", "migrate.py")
MIGRATIONS = os.path.join(ROOT, "db", "migrations")

# Expected schema: table -> ordered column names. Update together with new migrations.
EXPECTED_TABLES = {
    "app_info": ["key", "value"],
    "otp_sends": ["id", "phone", "sent_at"],
    "schema_migrations": ["version", "name", "checksum", "applied_at"],
}


def cli(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


class MigrateEmptyDbTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "test.db")

    def tearDown(self):
        self.tmp.cleanup()

    def tables(self):
        conn = sqlite3.connect(self.db)
        try:
            names = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            return {n: [c[1] for c in conn.execute("PRAGMA table_info(%s)" % n)] for n in names}
        finally:
            conn.close()

    def test_apply_all_on_empty_db(self):
        self.assertFalse(os.path.exists(self.db))
        r = cli("up", "--db", self.db)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.tables(), EXPECTED_TABLES)

        files = sorted(f for f in os.listdir(MIGRATIONS) if f.endswith(".up.sql"))
        conn = sqlite3.connect(self.db)
        versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
        conn.close()
        self.assertEqual(versions, [f.split("_")[0] for f in files])

    def test_rerun_is_noop(self):
        cli("up", "--db", self.db)
        r = cli("up", "--db", self.db)
        self.assertEqual(r.returncode, 0)
        self.assertIn("nothing to apply", r.stdout)

    def test_status_and_env_var(self):
        env = dict(os.environ, DATABASE_PATH=self.db)
        r = subprocess.run([sys.executable, SCRIPT, "up"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = cli("status", "--db", self.db)
        self.assertNotIn("pending", r.stdout)

    def test_rollback_all_then_reapply(self):
        cli("up", "--db", self.db)
        n = len([f for f in os.listdir(MIGRATIONS) if f.endswith(".up.sql")])
        r = cli("down", "--db", self.db, "--steps", str(n))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(list(self.tables()), ["schema_migrations"])
        self.assertEqual(cli("up", "--db", self.db).returncode, 0)
        self.assertEqual(self.tables(), EXPECTED_TABLES)

    def test_missing_db_arg_fails(self):
        env = {k: v for k, v in os.environ.items() if k != "DATABASE_PATH"}
        r = subprocess.run([sys.executable, SCRIPT, "up"], capture_output=True, text=True, env=env)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
