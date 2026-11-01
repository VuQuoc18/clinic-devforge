-- Patient accounts and one-time passcodes (separate auth domain from staff_users, REQ-015).
CREATE TABLE patients (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    phone      TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE patient_otps (
    patient_id INTEGER PRIMARY KEY REFERENCES patients (id),
    otp_hash   TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
