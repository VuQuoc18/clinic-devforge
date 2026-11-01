import unittest

from app import security


class PasswordTest(unittest.TestCase):
    def test_hash_is_not_plaintext_and_salted(self):
        h1, h2 = security.hash_password("s3cret!"), security.hash_password("s3cret!")
        self.assertNotIn("s3cret!", h1)
        self.assertNotEqual(h1, h2)
        self.assertTrue(h1.startswith("scrypt$"))

    def test_verify(self):
        h = security.hash_password("s3cret!")
        self.assertTrue(security.verify_password("s3cret!", h))
        self.assertFalse(security.verify_password("wrong", h))

    def test_verify_malformed_hash(self):
        self.assertFalse(security.verify_password("x", "plaintext"))
        self.assertFalse(security.verify_password("x", "md5$1$2$3$a$b"))


class SessionTest(unittest.TestCase):
    def test_roundtrip(self):
        t = security.sign_session("k", "staff", 7, 60, now=1000)
        self.assertEqual(security.read_session("k", "staff", t, now=1010), 7)

    def test_expired(self):
        t = security.sign_session("k", "staff", 7, 60, now=1000)
        self.assertIsNone(security.read_session("k", "staff", t, now=1061))

    def test_domains_are_isolated(self):
        t = security.sign_session("k", "patient", 7, 60, now=1000)
        self.assertIsNone(security.read_session("k", "staff", t, now=1001))
        t = security.sign_session("k", "staff", 7, 60, now=1000)
        self.assertIsNone(security.read_session("k", "patient", t, now=1001))

    def test_tampered_or_wrong_secret(self):
        t = security.sign_session("k", "staff", 7, 60, now=1000)
        self.assertIsNone(security.read_session("other", "staff", t, now=1001))
        self.assertIsNone(security.read_session("k", "staff", "x" + t, now=1001))
        self.assertIsNone(security.read_session("k", "staff", "garbage", now=1001))


if __name__ == "__main__":
    unittest.main()
