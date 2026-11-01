"""Password hashing and signed session tokens (stdlib only)."""
import base64
import hashlib
import hmac
import json
import os
import time

_N, _R, _P = 2 ** 14, 8, 1
_DKLEN = 32


def _b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _unb64(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password):
    """Return a salted scrypt hash: scrypt$n$r$p$salt$hash."""
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    return "scrypt$%d$%d$%d$%s$%s" % (_N, _R, _P, _b64(salt), _b64(digest))


def verify_password(password, stored):
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = _unb64(digest)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=_unb64(salt),
                                n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


# Used to spend the same time when the account does not exist.
DUMMY_HASH = hash_password("dummy-password-for-timing")


def _domain_key(secret, domain):
    return hmac.new(secret.encode("utf-8"), b"session|" + domain.encode("ascii"), hashlib.sha256).digest()


def sign_session(secret, domain, subject, ttl, now=None):
    """Signed token bound to one auth domain ("staff" or "patient")."""
    now = time.time() if now is None else now
    payload = _b64(json.dumps({"d": domain, "sub": subject, "exp": int(now + ttl)},
                              separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(_domain_key(secret, domain), payload.encode("ascii"), hashlib.sha256).digest()
    return payload + "." + _b64(sig)


def read_session(secret, domain, token, now=None):
    """Return the subject id if the token is valid for `domain`, else None."""
    now = time.time() if now is None else now
    try:
        payload, sig = token.split(".")
        expected = hmac.new(_domain_key(secret, domain), payload.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(_unb64(sig), expected):
            return None
        data = json.loads(_unb64(payload))
        if data.get("d") != domain or data.get("exp", 0) <= now:
            return None
        sub = data.get("sub")
        return sub if isinstance(sub, int) else None
    except (ValueError, TypeError, AttributeError):
        return None
