-- OTP send log per phone number (REQ-003): used for the 60s cooldown and 5 codes / 60 minutes limit.
CREATE TABLE otp_sends (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    phone   TEXT NOT NULL,
    sent_at INTEGER NOT NULL  -- UTC epoch milliseconds
);
CREATE INDEX idx_otp_sends_phone_sent_at ON otp_sends (phone, sent_at);
