"""Account data access for the two separate auth domains: staff and patients."""
import datetime
import sqlite3

from app import security


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def normalize_email(email):
    return email.strip().lower()


# --- staff -----------------------------------------------------------------

def create_staff(conn, email, password, full_name="", now=None):
    email = normalize_email(email)
    if "@" not in email or not password:
        raise ValueError("email and password are required")
    cur = conn.execute(
        "INSERT INTO staff_users (email, password_hash, full_name, created_at) VALUES (?, ?, ?, ?)",
        (email, security.hash_password(password), full_name, iso(now or utcnow())))
    conn.commit()
    return cur.lastrowid


def authenticate_staff(conn, email, password, now=None):
    """Return the staff row on success (and record last login), else None."""
    row = conn.execute("SELECT * FROM staff_users WHERE email = ?", (normalize_email(email),)).fetchone()
    if row is None:
        security.verify_password(password, security.DUMMY_HASH)
        return None
    if not security.verify_password(password, row["password_hash"]):
        return None
    conn.execute("UPDATE staff_users SET last_login_at = ? WHERE id = ?", (iso(now or utcnow()), row["id"]))
    conn.commit()
    return conn.execute("SELECT * FROM staff_users WHERE id = ?", (row["id"],)).fetchone()


def get_staff(conn, staff_id):
    return conn.execute("SELECT * FROM staff_users WHERE id = ?", (staff_id,)).fetchone()


# --- patients --------------------------------------------------------------

def create_patient(conn, phone, now=None):
    cur = conn.execute("INSERT INTO patients (phone, created_at) VALUES (?, ?)",
                       (phone.strip(), iso(now or utcnow())))
    conn.commit()
    return cur.lastrowid


def set_patient_otp(conn, phone, otp, ttl_seconds=300, now=None):
    """Store a hashed one-time passcode for an existing patient."""
    now = now or utcnow()
    row = conn.execute("SELECT id FROM patients WHERE phone = ?", (phone.strip(),)).fetchone()
    if row is None:
        raise ValueError("unknown patient")
    expires = now + datetime.timedelta(seconds=ttl_seconds)
    conn.execute("INSERT OR REPLACE INTO patient_otps (patient_id, otp_hash, expires_at) VALUES (?, ?, ?)",
                 (row["id"], security.hash_password(otp), iso(expires)))
    conn.commit()


def authenticate_patient(conn, phone, otp, now=None):
    """Return the patient row if phone + OTP match and are unexpired; the OTP is single-use."""
    now = now or utcnow()
    row = conn.execute(
        "SELECT p.id, o.otp_hash, o.expires_at FROM patients p "
        "LEFT JOIN patient_otps o ON o.patient_id = p.id WHERE p.phone = ?", (phone.strip(),)).fetchone()
    if row is None or row["otp_hash"] is None:
        security.verify_password(otp, security.DUMMY_HASH)
        return None
    ok = security.verify_password(otp, row["otp_hash"])
    if not ok or row["expires_at"] <= iso(now):
        return None
    conn.execute("DELETE FROM patient_otps WHERE patient_id = ?", (row["id"],))
    conn.commit()
    return conn.execute("SELECT * FROM patients WHERE id = ?", (row["id"],)).fetchone()


def get_patient(conn, patient_id):
    return conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
