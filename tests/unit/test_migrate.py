import os
import tempfile
import unittest

from db import migrate


def write(d, name, content=""):
    with open(os.path.join(d, name), "w") as f:
        f.write(content)


class DiscoverTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_sorted_by_version(self):
        write(self.d, "0002_b.up.sql", "SELECT 1;")
        write(self.d, "0001_a.up.sql", "SELECT 1;")
        write(self.d, "0001_a.down.sql", "SELECT 1;")
        ms = migrate.discover(self.d)
        self.assertEqual([m.version for m in ms], ["0001", "0002"])
        self.assertIsNotNone(ms[0].down_path)
        self.assertIsNone(ms[1].down_path)

    def test_invalid_name(self):
        write(self.d, "1_bad.up.sql")
        with self.assertRaises(migrate.MigrationError):
            migrate.discover(self.d)

    def test_gap_rejected(self):
        write(self.d, "0001_a.up.sql")
        write(self.d, "0003_c.up.sql")
        with self.assertRaises(migrate.MigrationError):
            migrate.discover(self.d)

    def test_down_without_up(self):
        write(self.d, "0001_a.down.sql")
        with self.assertRaises(migrate.MigrationError):
            migrate.discover(self.d)

    def test_name_mismatch_for_same_version(self):
        write(self.d, "0001_a.up.sql")
        write(self.d, "0001_b.down.sql")
        with self.assertRaises(migrate.MigrationError):
            migrate.discover(self.d)


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        write(self.d, "0001_t1.up.sql", "CREATE TABLE t1 (id INTEGER);")
        write(self.d, "0001_t1.down.sql", "DROP TABLE t1;")
        write(self.d, "0002_t2.up.sql", "CREATE TABLE t2 (id INTEGER);")
        self.conn = migrate.connect(os.path.join(self.d, "x.db"))

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_up_idempotent(self):
        ms = migrate.discover(self.d)
        self.assertEqual(len(migrate.up(self.conn, ms)), 2)
        self.assertEqual(migrate.up(self.conn, ms), [])

    def test_target(self):
        ms = migrate.discover(self.d)
        migrate.up(self.conn, ms, target="0001")
        self.assertEqual(list(migrate.applied(self.conn)), ["0001"])

    def test_failed_migration_rolls_back(self):
        write(self.d, "0003_bad.up.sql", "CREATE TABLE t3 (id INTEGER);\nSELECT * FROM nope;")
        ms = migrate.discover(self.d)
        with self.assertRaises(migrate.MigrationError):
            migrate.up(self.conn, ms)
        self.assertNotIn("0003", migrate.applied(self.conn))
        names = [r[0] for r in self.conn.execute("SELECT name FROM sqlite_master")]
        self.assertNotIn("t3", names)
        self.assertIn("t2", names)

    def test_checksum_change_detected(self):
        ms = migrate.discover(self.d)
        migrate.up(self.conn, ms)
        write(self.d, "0001_t1.up.sql", "CREATE TABLE t1 (id INTEGER, x TEXT);")
        with self.assertRaises(migrate.MigrationError):
            migrate.up(self.conn, migrate.discover(self.d))

    def test_down(self):
        ms = migrate.discover(self.d)
        migrate.up(self.conn, ms, target="0001")
        migrate.down(self.conn, ms)
        self.assertEqual(migrate.applied(self.conn), {})

    def test_down_without_script_fails(self):
        ms = migrate.discover(self.d)
        migrate.up(self.conn, ms)
        with self.assertRaises(migrate.MigrationError):
            migrate.down(self.conn, ms)


if __name__ == "__main__":
    unittest.main()
